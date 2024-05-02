#! /usr/bin/python3

import asyncio
import aioconsole
from time import sleep
from dotenv import load_dotenv

import measure
import valve as Valve

load_dotenv()

bmi0 = measure.Measure(0)
bmi1 = measure.Measure(1)
valve = Valve.Valve(200)

async def terminal_monitor():
    while True:
        prompt = await aioconsole.ainput(
            "Enter new position in percentage (or 'q' to quit): "
        )
        if prompt.lower() == "q":
            await valve.quit()
            bmi0.terminate_signal = True
            bmi1.terminate_signal = True
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
    tasks = [
        asyncio.create_task(bmi0.start_measure(True)),
        asyncio.create_task(bmi1.start_measure(True)),
        asyncio.create_task(valve.motor_loop()),
        asyncio.create_task(terminal_monitor())
        ]
    await asyncio.gather(*tasks)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    # Clean up GPIO on Ctrl+C
    bmi0.terminate_signal = True
    bmi1.terminate_signal = True
    valve.terminate_signal = True
    
    sleep(1)
    print("Died!")
    



