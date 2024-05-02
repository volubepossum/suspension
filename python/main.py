#! /usr/bin/python3

import asyncio
import measure
from time import sleep
#import python.valve as valve
from dotenv import load_dotenv

load_dotenv()

bmi0 = measure.Measure(0)
bmi1 = measure.Measure(1)

async def main():
    # Start motor loop and speed monitor loop concurrently
    tasks = [
        asyncio.create_task(bmi0.start_measure(True)),
        asyncio.create_task(bmi1.start_measure(True))
        ]
    await asyncio.gather(*tasks)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    # Clean up GPIO on Ctrl+C
    bmi0.terminate_signal = True
    bmi1.terminate_signal = True
    sleep(1)
    print("Goodbye!")
    



