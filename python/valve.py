import atexit # Import the atexit module to register the cleanup function
import RPi.GPIO as GPIO # Import the RPi.GPIO module

# Set the GPIO pin for the PWM output
pwm_pin = 17

# Set the PWM frequency and duty cycle
pwm_frequency = 1000  # in Hz

# Initialize the valve
def init_valve():
    # Set the GPIO mode
    GPIO.setmode(GPIO.BCM)

    # Set the GPIO pin for PWM output
    GPIO.setup(pwm_pin, GPIO.OUT)

    # Setup the PWM pin
    global pwm
    pwm = GPIO.PWM(pwm_pin, pwm_frequency)
    pwm.start(input("Duty: "))

# Set the valve opening
def set_valve(percentage):
    pwm.ChangeDutyCycle(percentage)

# Cleanup GPIO on program exit
def cleanup():
    pwm.stop()
    GPIO.cleanup()
    
atexit.register(cleanup)