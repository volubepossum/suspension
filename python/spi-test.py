#! /usr/bin/python3

import spidev

def send(bus, cmd):
    ans = bus.xfer(cmd)
    # return two bytes in binary and hex
    if len(ans) == 1:
        return f"{format(ans[0], '#010b')}\t      {ans[0]:02X}"
    return f"{format(ans[0], '#010b')}-{format(ans[1], '08b')}  {ans[0]:02X}-{ans[1]:02X}"

def read(bus, cmd):
    ans = bus.xfer([cmd|0x80, 0x00])
    # return two bytes in binary and hex
    return f"{format(ans[0], '#010b')}-{format(ans[1], '08b')}  {ans[0]:02X}-{ans[1]:02X}"

spi = spidev.SpiDev()

bus = spidev.SpiDev(0, 0)
bus.max_speed_hz = 100000
 
print(f"Turning on SPI mode:\t {send(bus,[0xFF, 0x00])}")  # turn on SPI mode
print(f"Read id:\t\t {read(bus,0x00)}")  # read id
#print(f"g-range:\t\t {send(bus,[0x41, 0x05])}")  # set g-range to  0x03 for +-2g, 0x05 for 4g, 0x08 for 8g, 0x0C for 16g
