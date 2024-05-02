#! /usr/bin/python3
import RPi.GPIO as GPIO
import asyncio
import aioconsole

# Define the GPIO pins connected to the stepper motor
STEP_PIN = 15
EN_PIN = 17
DIR_PIN = 22

# WHEN STARTING, THE VALVE MUST BE FULLY CLOSED
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
    89 / 360 * STEPS_PER_REVOLUTION / GEAR_RATIO
)  # 90 degree * steps/revolution * gear ratio

# Global variables


# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(EN_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)


class Valve:
    def __init__(self, speed=100):
        self.speed = speed  # Default speed in RPMs
        self.current_position = 0  # current valve position in steps
        self.target_position = 0  # target valve position in steps
        self.positioning_enabled = True
        self.terminate_signal = False  # signal to quit the program
        
    # Function to rotate stepper motor by one step
    async def _rotate_stepper(self, direction, delay):
        GPIO.output(EN_PIN, MOTOR_ENABLED)  # Enable the motor driver
        GPIO.output(DIR_PIN, direction)  # Set the direction

        GPIO.output(STEP_PIN, GPIO.HIGH)
        await asyncio.sleep(delay / 2)
        GPIO.output(STEP_PIN, GPIO.LOW)
        await asyncio.sleep(delay / 2)

    # Function to continuously rotate motor at a given speed
    async def motor_loop(self):
        while not self.terminate_signal:
            if not self.positioning_enabled:
                await asyncio.sleep(0.1)
            delay = 60 / (STEPS_PER_REVOLUTION * self.speed)
            if self.current_position < self.target_position:
                await self._rotate_stepper(CW, delay)
                self.current_position += 1
            elif self.current_position > self.target_position:
                await self._rotate_stepper(CCW, delay)
                self.current_position -= 1
            else:
                GPIO.output(EN_PIN, MOTOR_DISABLED)
                await asyncio.sleep(delay * 2)
                
    async def quit(self):
        print("Quitting. Returning to position 0")
        self.target_position = 0
        while self.current_position != 0:
            await asyncio.sleep(0.1)
        GPIO.cleanup()
        print("goodbye")
        self.terminate_signal = True
    
    async def calibrate(self):
        print("Now in calibration mode. Give a number in steps to move the valve.")
        print("CAUTION! No protections apply. Press 'q' to exit calibration mode.")
        self.positioning_enabled = False
        GPIO.output(EN_PIN, MOTOR_DISABLED)
        await asyncio.sleep(0.05)
        while True:
            new_position = await aioconsole.ainput(
                "Enter new position in steps (or 'q' to quit calibration mode): "
            )
            if new_position.lower() == "q":
                self.current_position = 0
                self.target_position = 0
                self.positioning_enabled = True
                print("Calibration finished. Valve is now at position 0")
                break
            try:
                delay = 60 / (STEPS_PER_REVOLUTION * self.speed)
                new_position = int(new_position)
                GPIO.output(EN_PIN, MOTOR_ENABLED)
                await asyncio.sleep(0.05)

                for _ in range(abs(new_position)):
                    if new_position > 0:
                        await self._rotate_stepper(CW, delay)
                    else:
                        await self._rotate_stepper(CCW, delay)
                GPIO.output(EN_PIN, MOTOR_DISABLED)

            except ValueError:
                print("Invalid input. Please enter a valid number.")      
    
    async def move_percentage(self, percentage):
        self.target_position = float(percentage) / 100 * MAX_VALVE_POSITION
        # rounding to the nearest integer
        self.target_position = int(self.target_position + 0.5)
        # checking if out of bounds
        if self.target_position < 0:
            self.target_position = 0
            print(
                f"Out of bounds. Setting to minimum position: {self.target_position} steps"
            )
        elif self.target_position > MAX_VALVE_POSITION:
            self.target_position = MAX_VALVE_POSITION
            print(
                f"Out of bounds. Setting to maximum position: {self.target_position} steps"
            )
        else:
            print(f"New position set: {self.target_position} steps")

    async def terminal_monitor(self):
        while True:
            prompt = await aioconsole.ainput(
                "Enter new position in percentage (or 'q' to quit): "
            )
            if prompt.lower() == "q":
                await self.quit()
                break
            elif prompt.lower() == "c":  # calibrate
                await self.calibrate()
            #if number, move to that position
            elif prompt.isnumeric():
                await self.move_percentage(prompt)
            else:
                print("Valid commands: 'q' to quit, 'c' to calibrate, or a number (%) to move the valve.")

if __name__ == "__main__":
    valve = Valve()
    async def main():
        # Start motor loop and speed monitor loop concurrently
        tasks = [asyncio.create_task(valve.motor_loop()), asyncio.create_task(valve.terminal_monitor())]
        await asyncio.gather(*tasks)


    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Clean up GPIO on Ctrl+C
        valve.terminate_signal = True
        GPIO.cleanup()
