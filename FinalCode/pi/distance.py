import lgpio
import time


TRIG = 23
ECHO = 24
TIMEOUT = 2

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)


def get_distance():
    
    lgpio.gpio_write(h, TRIG, 0)
    time.sleep(0.1)

    # 10 microsecond trigger
    lgpio.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    lgpio.gpio_write(h, TRIG, 0)

    start_time = time.time()

    # wait echo HIGH
    while lgpio.gpio_read(h, ECHO) == 0:
        if time.time() - start_time > TIMEOUT:
            return None

    pulse_start = time.time()

    # wait echo LOW
    while lgpio.gpio_read(h, ECHO) == 1:
        if time.time() - pulse_start > TIMEOUT:
            return None

    pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start

    distance = (pulse_duration * 343) / 2
    return distance


def proximity_level(distance):
   
    if distance is None:
        return "Far"

    if distance < 10:
        return "Too Near"
    else:
        return "Near"


def measure_distance():
    
    distance = get_distance()
    proximity = proximity_level(distance)

    return distance, proximity


def cleanup_gpio():

    lgpio.gpiochip_close(h)