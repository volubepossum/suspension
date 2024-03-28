from hmac import new
import time

import RPi.GPIO as GPIO

# Set the GPIO mode
GPIO.setmode(GPIO.BCM)

# Set the GPIO pin for PWM output
pwm_pin = 17

# Set the frequency and duty cycle for PWM
frequency = 1000  # in Hz
duty_cycle = 50  # in percentage

# Setup the PWM pin
GPIO.setup(pwm_pin, GPIO.OUT)
pwm = GPIO.PWM(pwm_pin, frequency)

# Start PWM with initial duty cycle
pwm.start(duty_cycle)
new_duty_cycle = duty_cycle

try:
    while True:
        # Your code logic goes here
        # You can read inputs, perform calculationsasd, etc.

        new_duty_cycle += 0.1
        if new_duty_cycle > 100:
            new_duty_cycle = 0
        pwm.ChangeDutyCycle()

        # Delay for a short period of time
        time.sleep(0.1)

except KeyboardInterrupt:
    # Clean up GPIO on keyboard interrupt
    GPIO.cleanup()