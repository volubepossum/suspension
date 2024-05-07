#! /usr/bin/python3

import asyncio
import aioconsole
from time import sleep
from dotenv import load_dotenv
import RPi.GPIO as GPIO

import measure
import valve as Valve
import logger as Logger

load_dotenv()

bmi0 = measure.Measure(0)
bmi1 = measure.Measure(1)
valve = Valve.Valve(400)
logger = Logger.Logger()

    

async def terminal_monitor():
    while True:
        prompt = await aioconsole.ainput(
            "Enter new position in percentage (or 'q' to quit): "
        )
        if prompt.lower() == "q":
            await valve.quit()
            program_terminate()
            break
        elif prompt.lower() == "c":  # calibrate
            await valve.calibrate()
        #if number, move to that position
        elif prompt.isnumeric():
            await valve.move_percentage(prompt)
        else:
            print("Valid commands: 'q' to quit, 'c' to calibrate, or a number (%) to move the valve.")

async def main():
    # Start motor loop and speed monitor loop concurrently
    logger.start_log()
    tasks = [
        asyncio.create_task(bmi0.start_measure(logger)),
        asyncio.create_task(bmi1.start_measure(logger)),
        asyncio.create_task(valve.motor_loop()),
        asyncio.create_task(terminal_monitor())
        ]
    await asyncio.gather(*tasks)

def program_terminate():
    valve.terminate_signal = True
    bmi0.terminate_signal = True
    bmi1.terminate_signal = True
    logger.end_log()
    sleep(1)
    print("Goodbye")
    
    
try:
    asyncio.run(main())
except KeyboardInterrupt:
    # Clean up GPIO on Ctrl+C
    program_terminate()
    



