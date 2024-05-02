#! /usr/bin/python3

import measure
#import python.valve as valve
from dotenv import load_dotenv

load_dotenv()

bmi0 = measure.Measure(0)
bmi1 = measure.Measure(1)

bmi0.start_measure(True)
bmi1.start_measure(True)
