from display import Display
from encoder import RotaryEncoder
from thermocouple import MAX31855
import utime

# Initialize hardware
display = Display()
encoder = RotaryEncoder(clk=10, dt=11, button=12)

#thermocouple pin assignments
thermo = MAX31855(sck=6, cs=5, miso=4)

# Menu setup
menu_items = ["Start Reflow", "Profile Select", "Settings"]
selected_index = 0
setpoint_temp = 150  # Example setpoint for display

display.show_startup()
utime.sleep(1)

last_display_update = utime.ticks_ms()

while True:
    encoder.update()

    # Check for encoder rotation
    direction = encoder.get_position()
    if direction != 0:
        selected_index = direction % len(menu_items)

    # Periodic display update
    now = utime.ticks_ms()
    if utime.ticks_diff(now, last_display_update) > 250:
        current_temp = thermo.read_temp()
        if current_temp is None:
            current_temp = 0.0  # fallback if read failed

        # Draw main screen
        display.oled.fill(0)
        display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 0)
        display.oled.text("Setpoint: {}C".format(setpoint_temp), 0, 12)

        # Draw menu
        for i, item in enumerate(menu_items):
            prefix = ">" if i == selected_index else " "
            display.oled.text("{}{}".format(prefix, item), 0, 24 + i * 10)

        display.oled.show()
        last_display_update = now

    # Handle encoder button press
    if encoder.was_pressed():
        print("Selected:", menu_items[selected_index])
        # TODO: Implement action handlers for each menu item

    utime.sleep_ms(2)
