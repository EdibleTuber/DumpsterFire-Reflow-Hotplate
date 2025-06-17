from machine import Pin
import utime

class RotaryEncoder:
    def __init__(self, clk=10, dt=11, button=12, callback=None):
        self.clk = Pin(clk, Pin.IN, Pin.PULL_UP)
        self.dt = Pin(dt, Pin.IN, Pin.PULL_UP)
        self.button = Pin(button, Pin.IN, Pin.PULL_UP) if button is not None else None

        self.last_clk = self.clk.value()
        self.position = 0
        self.callback = callback
        
        # Button state
        self.button_pressed = False
        self.button_press_time = None
        self.long_press_detected = False
        self.last_button = 1
        
        # Setup button interrupt if button pin is provided
        if self.button is not None:
            self.button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._button_handler)
        
        # Setup encoder interrupts
        self.clk.irq(trigger=Pin.IRQ_FALLING, handler=self._encoder_handler)
        self.dt.irq(trigger=Pin.IRQ_FALLING, handler=self._encoder_handler)

    def _encoder_handler(self, pin):
        # Debounce
        utime.sleep_ms(2)
        
        # Read current state
        current_clk = self.clk.value()
        current_dt = self.dt.value()

        # Check if this is a valid state change
        if current_clk == 0 and self.last_clk == 1:
            if current_dt == 1:
                self.position += 1
                direction = 1  # clockwise
            else:
                self.position -= 1
                direction = -1  # counterclockwise
            if self.callback:
                self.callback(direction)

        self.last_clk = current_clk

    def _button_handler(self, pin):
        # Debounce
        utime.sleep_ms(2)
        
            current_button = self.button.value()
        now = utime.ticks_ms()
        
        if current_button == 0 and self.last_button == 1:  # Button pressed
                self.button_pressed = True
            self.button_press_time = now
            self.long_press_detected = False
        elif current_button == 1 and self.last_button == 0:  # Button released
            if self.button_pressed:
                press_duration = utime.ticks_diff(now, self.button_press_time)
                if press_duration >= 1000:  # Long press threshold
                    self.long_press_detected = True
                self.button_pressed = False
                self.button_press_time = None
        
            self.last_button = current_button

    def update(self):
        # This method is kept for compatibility but is now empty
        # as interrupts handle the updates
        pass

    def get_position(self):
        pos = self.position
        self.position = 0  # Reset position after reading
        return pos

    def was_pressed(self):
        if self.button_pressed and self.button_press_time is not None:
            press_duration = utime.ticks_diff(utime.ticks_ms(), self.button_press_time)
            if press_duration < 500 and not self.long_press_detected:  # Short press threshold
            self.button_pressed = False
                self.button_press_time = None
            return True
        return False
    
    def was_held(self, duration_ms=1000):
        if self.long_press_detected:
            self.long_press_detected = False
            self.button_pressed = False
            self.button_press_time = None
                return True
        return False
