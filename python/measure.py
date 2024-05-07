import spidev
import csv
from time import sleep
import asyncio
import RPi.GPIO as GPIO

spi = spidev.SpiDev()


class Measure:
    possible_registries = {  # register, length, signed, multiplier
        "TIME": [0x18, 3, False, 39 * 10**-6],
        "A_X": [0x12, 2, True, 2**-15 * 4],  # multip = 2^(-15)*g-range
        "A_Y": [0x14, 2, True, 2**-15 * 4],  # multip = 2^(-15)*g-range
        "A_Z": [0x16, 2, True, 2**-15 * 4],  # multip = 2^(-15)*g-range
        "GYRO_X": [0x0C, 2, True],
        "GYRO_Y": [0x0E, 2, True],
        "GYRO_Z": [0x10, 2, True],
    }

    def __init__(self, device_id, registries=["TIME", "A_X", "A_Y", "A_Z"]):
        self.bus = spidev.SpiDev(0, device_id)
        self.bus.max_speed_hz = 100000
        self.last_read = None
        self.device_id = device_id
        self.terminate_signal = False
        self._configure_device()
        self.registries = {
            key: value
            for key, value in self.possible_registries.items()
            if key in registries
        }
        self._merge_registries()

    def _configure_device(self):
        self.bus.xfer([0xFF, 0x00])  # turn on SPI mode
        if self._read_measurement(0x00, 1)[0] == 0xD1:
            print(f"bmi {self.device_id} connected")
            self.error_check()
        else:
            print(f"bmi {self.device_id} not connected")
            GPIO.cleanup()
            exit()
        
        self.bus.xfer([0x7E, 0x11])  # set accelerometer mode to normal
        self.bus.xfer([0x7E, 0x14])  # set gyroscope mode to suspend
        self.bus.xfer([0x7E, 0x18])  # set magnetometer mode to suspend

        # power_mode = self._read_measurement(0x01, 1)[0]
        # print(f"bmi {self.device_id} power mode: {format(power_mode, '#010b')}")

        self.bus.xfer(
            [0x41, 0x05]
        )  # set g-range to  0x03 for +-2g, 0x05 for 4g, 0x08 for 8g, 0x0C for 16g

        input(f"hold the device still and vertical for dev-{self.device_id}, then press enter")
        self.bus.xfer(
            [0x69, 0b00011111]
        )  # configure FOC 0b00xxyyzz, ´0b00´ -> disabled, ´0b01´ -> +1 g, ´0b10´ -> -1 g, or ´0b11´ -> 0 g
        self.bus.xfer([0x77, 0b010000000])  # enable offset
        self.bus.xfer([0x7E, 0x03])  # trigger FOC
        sleep(0.2)
        self.error_check(lambda: self._configure_device, lambda: print("BMI ready for FOC"))
        while self._read_measurement(0x1B, 1)[0] & 0x08 == 0:
            # print(self._read_measurement(0x00, 1)[0])
            pass
        print("FOC done")
        self.bus.xfer(
            [0x40, 0x28]
        )  # 7: undersampling, 6-4: filtering config (0b010 for normal mode), 3-0: sampling rate (100*2^(x-8) Hz)
        self.bus.xfer([0x7E, 0x11])  # set accelerometer mode to normal

    def _merge_registries(self):
        self.reads = []  # first, length, [registries]
        for key, value in self.registries.items():  # merge registries into reads
            pre = next(
                (x for x in self.reads if x[0] + x[1] == value[0]), None
            )  # if there is a read after
            post = next(
                (x for x in self.reads if x[0] == value[0] + value[1]), None
            )  # if there is a read before
            if pre is None and post is None:  # if there are no reads before or after
                self.reads.append([value[0], value[1], [key]])
            elif (
                pre is not None and post is None
            ):  # if there is a read after but not before
                pre[1] += value[1]
                pre[2].append(key)
            elif (
                pre is None and post is not None
            ):  # if there is a read before but not after
                post[0] = value[0]
                post[1] += value[1]
                post[2].insert(0, key)
            else:  # if there are reads before and after
                pre[1] += value[1] + post[1]
                self.reads.remove(post)
                pre[2].append(key)
                pre[2].extend(post[2])

    def _read_measurement(self, register, length):
        tx_data = [0x80 | register] + [0x00] * length
        rx_data = self.bus.xfer(tx_data)
        return rx_data[1:]

    def read(self):
        # return {key: self._read_measurement(value[0], value[1]) for key, value in self.registries.items()}
        result = {}
        for read in self.reads:
            data = self._read_measurement(read[0], read[1])
            read_count = 0
            for key in read[2]:  # read[2] is the list of registries
                result[key] = self.registries[key][3] * int.from_bytes(
                    data[read_count : read_count + self.registries[key][1]],
                    byteorder="little",
                    signed=self.registries[key][2],
                )
                read_count += self.registries[key][1]
        self.last_read = result
        return result
    
    async def start_measure(self, logger = None):
        if logger is not None:
            # Write the header
            #logger.log_row(self.read().keys())
            logger.bmi_time_sync(self.device_id, self.read()["TIME"])
            while not self.terminate_signal:
                while (
                    self._read_measurement(0x1B, 1)[0] & 0x80 == 0
                ):  # wait for drdy_acc
                    pass
                
                logger.log_bmi(self.device_id, self.read())
                #print(row)
                await asyncio.sleep(0.008)
        else:
            while not self.terminate_signal:
                while (
                    self._read_measurement(0x1B, 1)[0] & 0x80 == 0
                ):  # wait for drdy_acc
                    pass
                await asyncio.sleep(0.008)

    def error_check(self, on_error=lambda: 0, on_ok=lambda: 0):
        err = self._read_measurement(0x02, 1)[0]
        if err != 0x00:
            print(f"bmi {self.device_id} error detected {format(err, '#010b')}")
            on_ok()
        else:
            on_error()
