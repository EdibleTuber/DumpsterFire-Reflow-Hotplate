# main.py - Dumpster Fire Reflow Hotplate Controller
#
# Supports:
# - Manual Mode: user sets temp directly
# - Reflow Mode: multi-stage profile with dynamic ramping from lower to upper temp
# Each reflow stage begins timing only once the lower bound is met or exceeded.

from display import Display
from encoder import RotaryEncoder
from thermocouple import MAX31855
from ssr import SSR
from pid import PID
import utime

# ───── Modes ─────
MODE_MENU = 0
MODE_MANUAL = 1
MODE_REFLOW = 2

# ───── Logging Helper ─────
def log_data(t_elapsed, stage, temp, target, output):
    try:
        with open("log.csv", "a") as f:
            f.write("{},{:.1f},{:.1f},{:.1f},{:.1f}\n".format(t_elapsed, stage, temp, target, output))
    except:
        pass

# ───── Reflow Profile: (duration, lower_temp, upper_temp) ─────
reflow_profile = [
    (60, 25, 80),    # Preheat
    (60, 80, 110),   # Soak
    (30, 145, 155),   # Reflow
    (30, 100, 100),   # Cooldown
]

# ───── Hardware Init ─────
display = Display()
encoder = RotaryEncoder(clk=10, dt=11, button=12)
thermo = MAX31855(sck=6, cs=5, miso=4)
ssr = SSR(pin=16)

# ───── State ─────
current_mode = MODE_MENU
menu_items = ["Manual Mode", "Reflow Profile"]
selected_index = 0
manual_setpoint = 150

reflow_stage = 0
stage_start_time = None
stage_elapsed = 0
reflow_start_time = None
pid = None

display.show_startup()
utime.sleep(1)
last_display_update = utime.ticks_ms()

# ───── Main Loop ─────
while True:
    encoder.update()

    # ───── Menu ─────
    if current_mode == MODE_MENU:
        direction = encoder.get_position()
        if direction != 0:
            selected_index = direction % len(menu_items)

        if encoder.was_pressed():
            if selected_index == 0:
                current_mode = MODE_MANUAL
                encoder.position = 0
            elif selected_index == 1:
                current_mode = MODE_REFLOW
                encoder.position = 0

        now = utime.ticks_ms()
        if utime.ticks_diff(now, last_display_update) > 250:
            current_temp = thermo.read_temp() or 0.0
            display.oled.fill(0)
            display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 0)
            for i, item in enumerate(menu_items):
                prefix = ">" if i == selected_index else " "
                display.oled.text(f"{prefix}{item}", 0, 16 + i * 12)
            display.oled.show()
            last_display_update = now

    # ───── Manual Mode ─────
    elif current_mode == MODE_MANUAL:
        manual_setpoint += encoder.get_position()
        manual_setpoint = max(0, min(300, manual_setpoint))
        encoder.position = 0

        current_temp = thermo.read_temp() or 0.0

        if current_temp < manual_setpoint - 2:
            ssr.on()
        elif current_temp > manual_setpoint + 2:
            ssr.off()

        now = utime.ticks_ms()
        if utime.ticks_diff(now, last_display_update) > 250:
            display.show_temp(current_temp, manual_setpoint)
            last_display_update = now

        if encoder.was_pressed():
            ssr.off()
            current_mode = MODE_MENU
            encoder.position = 0

    # ───── Reflow Mode ─────
    elif current_mode == MODE_REFLOW:
        now = utime.ticks_ms()

        # First-time init
        if reflow_start_time is None:
            reflow_start_time = now
            reflow_stage = 0
            ssr.off()
            pid = PID(kp=4.5, ki=0.4, kd=0.6, setpoint=0, output_limits=(0, 100))
            pid.reset()
            try:
                with open("log.csv", "w") as f:
                    f.write("Time,Stage,Temp,Setpoint,PID%\n")
            except:
                pass

        current_temp = thermo.read_temp() or 0.0
        stage_duration, lower_bound, upper_bound = reflow_profile[reflow_stage]

        # Wait for lower bound before starting stage
        if stage_start_time is None:
            if current_temp < lower_bound:
                # Hold temp at lower_bound
                pid.setpoint = lower_bound
                output = pid.compute(current_temp)
                if output is not None:
                    ssr.on() if output > 0 else ssr.off()

                if utime.ticks_diff(now, last_display_update) > 500:
                    display.oled.fill(0)
                    display.oled.text("Stage {}: Waiting".format(reflow_stage + 1), 0, 0)
                    display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 12)
                    display.oled.text("Target: {:.1f} C".format(lower_bound), 0, 24)
                    display.oled.text("Press to abort", 0, 50)
                    display.oled.show()
                    last_display_update = now

                if encoder.was_pressed():
                    ssr.off()
                    current_mode = MODE_MENU
                    encoder.position = 0
                continue  # retry loop

            else:
                stage_start_time = now  # temp is at or above lower bound

        # Compute dynamic target based on time within stage
        stage_elapsed = utime.ticks_diff(now, stage_start_time) // 1000
        progress = min(1.0, stage_elapsed / stage_duration)
        target_temp = lower_bound + (upper_bound - lower_bound) * progress

        pid.setpoint = target_temp
        output = pid.compute(current_temp)

        if output is not None:
            total_elapsed = utime.ticks_diff(now, reflow_start_time) // 1000
            log_data(total_elapsed, reflow_stage + 1, current_temp, pid.setpoint, output)

            # Soft PWM
            window_ms = 1000
            on_time = int(output / 100 * window_ms)
            cycle_pos = utime.ticks_diff(now, stage_start_time) % window_ms
            ssr.on() if cycle_pos < on_time else ssr.off()

        # Advance stage
        if stage_elapsed >= stage_duration:
            reflow_stage += 1
            if reflow_stage >= len(reflow_profile):
                ssr.off()
                current_mode = MODE_MENU
                encoder.position = 0
                stage_start_time = None
                reflow_start_time = None
                continue
            stage_start_time = None
            pid.reset()

        if utime.ticks_diff(now, last_display_update) > 500:
            display.oled.fill(0)
            display.oled.text("Reflow Stage: {}".format(reflow_stage + 1), 0, 0)
            display.oled.text("Target: {:.1f} C".format(target_temp), 0, 12)
            display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 24)
            display.oled.text("Time: {}s".format(stage_elapsed), 0, 36)
            display.oled.text("Press to abort", 0, 50)
            display.oled.show()
            last_display_update = now

        if encoder.was_pressed():
            ssr.off()
            current_mode = MODE_MENU
            stage_start_time = None
            reflow_start_time = None
            encoder.position = 0

    utime.sleep_ms(10)
