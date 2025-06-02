# display.py
from machine import Pin, I2C
from ssd1309 import SSD1309  # Assuming ssd1309.py is uploaded to the Pico

class Display:
    def __init__(self, scl_pin=1, sda_pin=0, i2c_addr=0x3C):
        self.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        self.oled = SSD1309(self.i2c, 128, 64)

    def clear(self):
        self.oled.fill(0)
        self.oled.show()

    def show_startup(self):
        self.oled.fill(0)
        self.oled.text("Reflow Hotplate", 0, 0)
        self.oled.text("Starting...", 0, 16)
        self.oled.show()

    def show_temp(self, temp_c, setpoint):
        self.oled.fill(0)
        self.oled.text("Temp: {:.1f} C".format(temp_c), 0, 0)
        self.oled.text("Setpoint: {}C".format(setpoint), 0, 20)
        status = "HEATING" if temp_c < setpoint else "HOLD"
        self.oled.text("Status: {}".format(status), 0, 40)
        self.oled.show()
