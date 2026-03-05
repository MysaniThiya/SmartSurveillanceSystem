
import lgpio
import cv2
import numpy as np

# ------------------ PIR SENSOR SETUP ------------------
PIR_PIN = 17
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, PIR_PIN)

def pir_triggered():
    return lgpio.gpio_read(h, PIR_PIN) == 1


# ------------------ LOW-LIGHT CHECK ------------------
def is_night(frame, threshold=50):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    return brightness < threshold