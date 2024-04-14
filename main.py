import measure as measure
import valve
from dotenv import load_dotenv

load_dotenv()

# measure = mea.Measure(1, 0x69)
# measure.start_measure(True)

valve.init_valve()

try:
    while True:
        valve.set_valve(float(input("Duty: ")))
except KeyboardInterrupt:
    pass
