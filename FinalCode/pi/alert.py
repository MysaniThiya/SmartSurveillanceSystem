import pyttsx3

# Initialize once (important)
engine = pyttsx3.init()

# Optional tuning (you can adjust later)
engine.setProperty('rate', 150)   # speed
engine.setProperty('volume', 1.0) # max volume


def speak_alert(animal, proximity, behavior):
    if proximity == "Too Near":
        message = f" Warning. {animal} very close. It is {behavior}"
    elif proximity == "Near":
        message = f" Alert. {animal} detected nearby. It is {behavior}"
    else:
        message = f" {animal} detected. It is {behavior}"


    print(f"🔊 Speaking: {message}")

    engine.say(message)
    engine.runAndWait()

    return message