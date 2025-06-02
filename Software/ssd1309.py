# ssd1309.py
from micropython import const
import framebuf
import time

SET_CONTRAST = const(0x81)
DISPLAY_ALL_ON_RESUME = const(0xA4)
DISPLAY_ALL_ON = const(0xA5)
NORMAL_DISPLAY = const(0xA6)
INVERT_DISPLAY = const(0xA7)
DISPLAY_OFF = const(0xAE)
DISPLAY_ON = const(0xAF)
SET_DISPLAY_OFFSET = const(0xD3)
SET_COM_PINS = const(0xDA)
SET_VCOM_DETECT = const(0xDB)
SET_DISPLAY_CLOCK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_MULTIPLEX = const(0xA8)
SET_LOW_COLUMN = const(0x00)
SET_HIGH_COLUMN = const(0x10)
SET_START_LINE = const(0x40)
MEMORY_MODE = const(0x20)
COLUMN_ADDR = const(0x21)
PAGE_ADDR = const(0x22)
COM_SCAN_INC = const(0xC0)
COM_SCAN_DEC = const(0xC8)
SEG_REMAP = const(0xA0)
CHARGE_PUMP = const(0x8D)
EXTERNAL_VCC = const(0x1)
SWITCH_CAP_VCC = const(0x2)

class SSD1309(framebuf.FrameBuffer):
    def __init__(self, i2c, width, height, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.width * self.pages)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, b'\x00' + bytearray([cmd]))

    def init_display(self):
        for cmd in (
            DISPLAY_OFF,
            SET_DISPLAY_CLOCK_DIV, 0x80,
            SET_MULTIPLEX, self.height - 1,
            SET_DISPLAY_OFFSET, 0x00,
            SET_START_LINE | 0x00,
            CHARGE_PUMP, 0x14 if not self.external_vcc else 0x10,
            MEMORY_MODE, 0x00,
            SEG_REMAP | 0x1,
            COM_SCAN_DEC,
            SET_COM_PINS, 0x12,
            SET_CONTRAST, 0xCF,
            SET_PRECHARGE, 0xF1 if not self.external_vcc else 0x22,
            SET_VCOM_DETECT, 0x40,
            DISPLAY_ALL_ON_RESUME,
            NORMAL_DISPLAY,
            DISPLAY_ON,
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def show(self):
        for page in range(0, self.pages):
            self.write_cmd(0xB0 + page)
            self.write_cmd(SET_LOW_COLUMN | 0x0)
            self.write_cmd(SET_HIGH_COLUMN | 0x0)
            self.i2c.writeto(self.addr, b'\x40' + self.buffer[self.width * page:self.width * (page + 1)])
