import measure as mea
from dotenv import load_dotenv

load_dotenv()

measure = mea.Measure(1, 0x69)
measure.start_log()