#! /usr/bin/python3

import measure
#import python.valve as valve
from dotenv import load_dotenv

load_dotenv()

bmi1 = measure.Measure(1)
bmi1.start_measure(True)
