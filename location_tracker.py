from flask import Flask, request
from geopy.geocoders import Nominatim
import time

app = Flask(__name__)

latest_location_name = "Unknown"
last_location_time = 0
LOCATION_TIMEOUT = 300

geolocator = Nominatim(user_agent="animal_surveillance")

def reverse_geocode(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), language="en")
        if location and location.address:
            return location.address
    except Exception as e:
        print("Reverse geocode error:", e)
    return "Unknown"

@app.route("/update_location", methods=["POST"])
def update_location():
    global latest_location_name, last_location_time

    data = request.get_json(silent=True)
    print("Received data:", data)

    try:
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
    except Exception as e:
        print("Invalid data:", data)
        return {"status": "bad_data"}, 400

    latest_location_name = reverse_geocode(lat, lon)
    last_location_time = time.time()

    print("Updated location:", latest_location_name)

    return {"status": "ok"}

def get_current_location():
    global latest_location_name, last_location_time
    if time.time() - last_location_time > LOCATION_TIMEOUT:
        return "Unknown"
    return latest_location_name