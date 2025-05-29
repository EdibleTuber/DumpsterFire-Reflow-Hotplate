# thermocouple.py
from machine import SPI, Pin
import time

class MAX6675:
    def __init__(self, clk=2, cs=3, do=4):
        self.cs = Pin(cs, Pin.OUT)
        self.cs.value(1)
        self.spi = SPI(0, baudrate=5000000, polarity=0, phase=0, sck=Pin(clk), mosi=Pin(0), miso=Pin(do))

    def read_temp(self):
        self.cs.value(0)
        data = self.spi.read(2)
        self.cs.value(1)

        value = (data[0] << 8) | data[1]
        if value & 0x4:  # Open thermocouple error
            return None
        return (value >> 3) * 0.25  # Convert to Celsius

