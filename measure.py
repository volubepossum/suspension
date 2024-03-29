from smbus2 import SMBus
import csv
from time import sleep

class Measure:
    registries = { # register, length, signed
        'TIME':     [0x18,3, False],
        'ACCEL_X':  [0x12,2, True],
        'ACCEL_Y':  [0x14,2, True],
        'ACCEL_Z':  [0x16,2, True],
        # 'GYRO_X': [0x0C,2, True],
        # 'GYRO_Y': [0x0E,2, True],
        # 'GYRO_Z': [0x10,2, True],
    }
    def __init__(self, bus, address):
        self.bus = SMBus(bus)
        self.address = address
        self.bus.write_byte_data(self.address, 0x40, 0b00101000) # Wake up 7: undersampling, 6-4: filtering config (0b010 for normal mode), 3-0: sampling rate (100*2^(x-8) Hz)
        self.bus.write_byte_data(self.address, 0x7E, 0x11) # set acceleration mode to normal
        # self.bus.write_byte_data(self.address, 0x7F, 0x15) # set gyroscope mode to normal


    def _read_measurement(self, measurement_register, length): # works with all registries
        return self.bus.read_i2c_block_data(self.address, measurement_register, length)
    
    def read(self):
        return {key: self._read_measurement(value[0], value[1]) for key, value in self.registries.items()}
    
    def readfast(self): # only works for specific data read
        read = self.bus.read_i2c_block_data(self.address, 0x12, 9)
        return {
            'TIME':     int.from_bytes([read[6], read[7], read[8]], byteorder='little', signed=False),
            'ACCEL_X':  int.from_bytes([read[0], read[1]], byteorder='little', signed=True),
            'ACCEL_Y':  int.from_bytes([read[2], read[3]], byteorder='little', signed=True),
            'ACCEL_Z':  int.from_bytes([read[4], read[5]], byteorder='little', signed=True),
        }

    
    def start_log(self):
        with open('/home/cnc/suspension/measurement_log.csv', 'w', newline='') as csvfile:
        # Create a CSV writer object
                writer = csv.writer(csvfile)
                row = self.registries.keys()
                writer.writerow(row)
                try:
                    while True:
                        while self._read_measurement(0x1B, 1)[0] & 0x80 == 0: # wait for drdy_acc
                            pass
                        row = self.readfast().values()
                        writer.writerow(row)
                        sleep(0.005)
                except KeyboardInterrupt:
                    pass
                finally:
                    csvfile.close() 
#     while True:
#         measure = Measure(1, 0x69)
#         measurements = measure.read()
#         string = ""
#         for key, value in measurements.items():
#             string += f" {key}: {value:#0{6}x}"
#         print(string)
#         # print(measure.bus.read_byte_data(0x69, 0x00))
#         sleep(0.1)

# except KeyboardInterrupt:
#     pass