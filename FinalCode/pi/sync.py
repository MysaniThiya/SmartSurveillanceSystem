import csv
import requests
import os

BACKEND_URL = "https://smart-surveillance-system-production.up.railway.app"
CSV_FILE = "events/logs/events.csv"
IMAGE_FOLDER = "events/images"

remaining_rows = []
events = []

# -------- internet check --------
def is_online():
    try:
        requests.get(BACKEND_URL, timeout=5)
        return True
    except:
        return False

if not is_online():
    print("⚠️ No internet — skipping sync")
    exit()

# -------- read CSV --------
with open(CSV_FILE, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = reader.fieldnames

    for row in reader:
        image_path = os.path.join(IMAGE_FOLDER, row["snapshot"])

        if not os.path.exists(image_path):
            print(f"❌ Missing image: {image_path}")
            continue

        # upload image
        with open(image_path, "rb") as img:
            response = requests.post(
                f"{BACKEND_URL}/upload-image",
                files={"image": img}
            )

        if response.status_code == 200:
            image_url = BACKEND_URL + response.json()["path"]

            event = {
                "timestamp": row["timestamp"],
                "animal": row["animal"],
                "distance": row["distance"],
                "proximity": row["proximity"],
                "behavior": row["behavior"],
                "location": row["location"],
                "snapshot": image_url,
                "alert_message": row["alert_message"]
            }

            events.append(event)

            os.remove(image_path)

        else:
            # keep row if upload failed
            remaining_rows.append(row)

# -------- send events --------
if events:
    response = requests.post(
        f"{BACKEND_URL}/sync-events",
        json=events
    )
    print(response.json())

# -------- rewrite CSV with only unsynced --------
with open(CSV_FILE, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(remaining_rows)

print("✅ Sync completed (synced rows removed)")