# main.py - Dumpster Fire Reflow Hotplate Controller
#
# Supports:
# - Manual Mode: user sets temp directly
# - Reflow Mode: multi-stage profile with dynamic ramping from lower to upper temp
# - Set Reflow Mode: edit reflow profile
# Each reflow stage begins timing only once the lower bound is met or exceeded.

from display import Display
from encoder import RotaryEncoder
from thermocouple import MAX31855
from ssr import SSR
from modes import MenuMode, ManualMode, ReflowMode, ProfileEditMode
import utime

# ───── Modes ─────
MODE_MENU       = 0
MODE_MANUAL     = 1
MODE_REFLOW     = 2
MODE_SET_REFLOW = 3

# Environment variables
P = 1.2
I = 0.2
D = 3.0
reflow_output_reduction = 0.7

# ───── Logging Helper ─────
def log_data(t_elapsed, stage, temp, target, output):
    # Logs temperature, setpoint, output to CSV
    try:
        with open("log.csv", "a") as f:
            f.write("{},{:.1f},{:.1f},{:.1f},{:.1f}\n".format(t_elapsed, stage, temp, target, output))
    except:
        pass

# ───── Reflow Profile: (duration, lower_temp, upper_temp) ─────
reflow_profile = [
    [60, 25, 80],    # Preheat
    [60, 80, 110],   # Soak
    [60, 145, 155],  # Reflow
    [30, 100, 100],  # Cooldown
]

stage_names = ["Preheat", "Soak", "Reflow", "Cooldown"]

# ───── Hardware Init ─────
display = Display()
encoder = RotaryEncoder(clk=10, dt=11, button=12)
thermo = MAX31855(sck=6, cs=5, miso=4)
ssr = SSR(pin=16)

# ───── Mode Init ─────
modes = {
    MODE_MENU: MenuMode(display, encoder, thermo, ssr),
    MODE_MANUAL: ManualMode(display, encoder, thermo, ssr),
    MODE_REFLOW: ReflowMode(display, encoder, thermo, ssr, reflow_profile, stage_names),
    MODE_SET_REFLOW: ProfileEditMode(display, encoder, thermo, ssr, reflow_profile, stage_names)
}

# ───── Init ─────
display.show_startup()
utime.sleep(1)
current_mode = MODE_MENU
menu_items = ["Manual Mode", "Reflow Mode", "Set Profile"]
selected_index = 0
manual_setpoint = 150
profile_edit_stage = 0
profile_edit_param = 0

try:
    # ───── Main Loop ─────
    while True:
        encoder.update()
        
        # Update current mode and check for mode change
        new_mode = modes[current_mode].update()
        if new_mode:
            if new_mode == "MENU":
                current_mode = MODE_MENU
            elif new_mode == "MANUAL":
                current_mode = MODE_MANUAL
            elif new_mode == "REFLOW":
                current_mode = MODE_REFLOW
            elif new_mode == "SET_REFLOW":
                current_mode = MODE_SET_REFLOW
        
        utime.sleep_ms(10)
except Exception as e:
    ssr.off()
    display.oled.fill(0)
    display.oled.text("CRITICAL ERROR", 0, 0)
    display.oled.text(str(e), 0, 16)
    display.oled.show()
    while True:
        utime.sleep_ms(1000)
