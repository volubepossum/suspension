#! ./venv/bin/python3
import RPi.GPIO as GPIO
import asyncio
import aioconsole

# Define the GPIO pins connected to the stepper motor
STEP_PIN = 15
EN_PIN = 17
DIR_PIN = 22

# percentage 0 = fully closed, perpendicular
# opening = CW


# setting constants
CW = GPIO.LOW  # clockwise
CCW = GPIO.HIGH  # counter-clockwise
MOTOR_ENABLED = GPIO.HIGH
MOTOR_DISABLED = GPIO.HIGH
STEPS_PER_REVOLUTION = 3200
GEAR_RATIO = 1 / 2.2
MAX_VALVE_POSITION = (
    93 / 360 * STEPS_PER_REVOLUTION / GEAR_RATIO
)  # 90 degree * steps/revolution * gear ratio

# Global variables
speed = 100  # Default speed in RPMs
current_position = 0  # current valve position in steps
target_position = 0  # target valve position in steps
positioning_enabled = True
terminate_signal = False  # signal to quit the program

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(EN_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)


# Function to rotate stepper motor by one step
async def rotate_stepper(direction, delay):
    GPIO.output(EN_PIN, MOTOR_ENABLED)  # Enable the motor driver
    GPIO.output(DIR_PIN, direction)  # Set the direction

    GPIO.output(STEP_PIN, GPIO.HIGH)
    await asyncio.sleep(delay / 2)
    GPIO.output(STEP_PIN, GPIO.LOW)
    await asyncio.sleep(delay / 2)


# Function to continuously rotate motor at a given speed
async def motor_loop():
    global speed, STEPS_PER_REVOLUTION, current_position, target_position
    while not terminate_signal:
        if not positioning_enabled:
            await asyncio.sleep(0.1)
        delay = 60 / (STEPS_PER_REVOLUTION * speed)
        if current_position < target_position:
            await rotate_stepper(CW, delay)
            current_position += 1
        elif current_position > target_position:
            await rotate_stepper(CCW, delay)
            current_position -= 1
        else:
            GPIO.output(EN_PIN, MOTOR_DISABLED)
            await asyncio.sleep(delay * 2)


async def terminal_monitor():
    global target_position, positioning_enabled, current_position, terminate_signal
    while True:
        new_position = await aioconsole.ainput(
            "Enter new position in percentage (or 'q' to quit): "
        )
        if new_position.lower() == "q":
            print("Quitting. Returning to position 0")
            target_position = 0
            while current_position != 0:
                await asyncio.sleep(0.1)
            GPIO.cleanup()
            print("goodbye")
            terminate_signal = True
            break
        elif new_position.lower() == "c":  # calibrate
            print("Now in calibration mode. Give a number in steps to move the valve.")
            print("CAUTION! No protections apply. Press 'q' to exit calibration mode.")
            positioning_enabled = False
            GPIO.output(EN_PIN, MOTOR_DISABLED)
            await asyncio.sleep(0.05)
            while True:
                new_position = await aioconsole.ainput(
                    "Enter new position in steps (or 'q' to quit calibration mode): "
                )
                if new_position.lower() == "q":
                    current_position = 0
                    target_position = 0
                    positioning_enabled = True
                    print("Calibration finished. Valve is now at position 0")
                    break
                try:
                    delay = 60 / (STEPS_PER_REVOLUTION * speed)
                    new_position = int(new_position)
                    GPIO.output(EN_PIN, MOTOR_ENABLED)
                    await asyncio.sleep(0.05)

                    for _ in range(abs(new_position)):
                        if new_position > 0:
                            await rotate_stepper(CW, delay)
                        else:
                            await rotate_stepper(CCW, delay)
                    GPIO.output(EN_PIN, MOTOR_DISABLED)

                except ValueError:
                    print("Invalid input. Please enter a valid number.")

        try:
            target_position = float(new_position) / 100 * MAX_VALVE_POSITION
            # rounding to the nearest integer
            target_position = int(target_position + 0.5)
            # checking if out of bounds
            if target_position < 0:
                target_position = 0
                print(
                    f"Out of bounds. Setting to minimum position: {target_position} steps"
                )
            elif target_position > MAX_VALVE_POSITION:
                target_position = MAX_VALVE_POSITION
                print(
                    f"Out of bounds. Setting to maximum position: {target_position} steps"
                )
            else:
                print(f"New position set: {target_position} steps")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


async def main():
    # Start motor loop and speed monitor loop concurrently
    tasks = [asyncio.create_task(motor_loop()), asyncio.create_task(terminal_monitor())]
    await asyncio.gather(*tasks)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    # Clean up GPIO on Ctrl+C
    terminate_signal = True
    GPIO.cleanup()
