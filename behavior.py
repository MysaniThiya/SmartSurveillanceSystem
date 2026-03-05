from datetime import datetime
import os

FAILURE_LOG = "outputs/failure_log.txt"


# ==============================
# FAILURE LOGGER (optional safety)
# ==============================
def log_failure(animal_type, error_message):
    """Log behavior module failures"""
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"{ts} | {animal_type} | MODULE_FAILURE | {error_message}\n"

    os.makedirs("outputs", exist_ok=True)
    with open(FAILURE_LOG, "a", encoding="utf-8") as f:
        f.write(line)


# ==============================
# MAIN BEHAVIOR PREDICTION
# ==============================
def predict_behavior(animal_type, direction, current_speed):
    """
    Uses ONLY current movement + species knowledge
    (No historical learning)
    """

    try:
        # ----------------------------------
        # Movement classification
        # ----------------------------------
        if direction in ["LEFT", "RIGHT"]:
            if current_speed > 6:
                movement_label = "LIKELY CROSSING (FAST)"
            else:
                movement_label = "LIKELY CROSSING"

        elif direction == "DOWN":
            if current_speed > 6:
                movement_label = "APPROACHING VEHICLE (FAST)"
            else:
                movement_label = "APPROACHING VEHICLE"

        elif direction == "UP":
            movement_label = "MOVING AWAY"

        elif direction == "STATIONARY" or current_speed < 0.5:
            movement_label = "STANDING"

        else:
            movement_label = "MOVING"

        # ----------------------------------
        # historical behavior
        # ----------------------------------
        animal = animal_type.lower()

        if "elephant" in animal:
            normal_behavior = "It may attack vehicle"
        elif "dog" in animal:
            normal_behavior = "It may cross suddenly"
        elif "cow" in animal:
            normal_behavior = "It usually crosses slowly"
        else:
            normal_behavior = "Monitor animal movement"

        # ----------------------------------
        # Final combined message
        # ----------------------------------
        final_behavior = f"{movement_label} . {normal_behavior}"
        return final_behavior

    except Exception as e:
        log_failure(animal_type, str(e))
        return "UNKNOWN"