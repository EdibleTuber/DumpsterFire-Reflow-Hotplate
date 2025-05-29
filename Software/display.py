# display.py
from machine import Pin, I2C
import ssd1309

class Display:
    def __init__(self, scl_pin=1, sda_pin=0):
        i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.oled = ssd1309.SSD1309_I2C(128, 64, i2c)

    def show_startup(self):
        self.oled.fill(0)
        self.oled.text("Reflow Hotplate", 0, 0)
        self.oled.text("Initializing...", 0, 20)
        self.oled.show()

    def show_temp(self, temp_c):
        self.oled.fill(0)
        self.oled.text("Temp: {:.1f} C".format(temp_c), 0, 0)
        self.oled.show()

