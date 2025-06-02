# ssr.py
from machine import Pin

class SSR:
    def __init__(self, pin=16):
        self.control = Pin(pin, Pin.OUT)
        self.off()

    def on(self):
        self.control.value(1)

    def off(self):
        self.control.value(0)

