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
    # Logs temperature, setpoint, PID output to CSV
    try:
        with open("log.csv", "a") as f:
            f.write("{},{:.1f},{:.1f},{:.1f},{:.1f}\n".format(t_elapsed, stage, temp, target, output))
    except:
        pass

# ───── Reflow Profile: (duration, lower_temp, upper_temp) ─────
reflow_profile = [
    (60, 25, 80),    # Preheat
    (60, 80, 110),   # Soak
    (60, 145, 155),  # Reflow
    (30, 100, 100),  # Cooldown
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
P = 2.0
I = 0.4
D = 2.0
reflow_output_reduction = 0.7

MAX_RAMP_RATE = 2.0  # deg/sec limit for Preheat

stage_names = ["Preheat", "Soak", "Reflow", "Cooldown"]

# ───── Utility ─────
def compute_target_temp(stage_elapsed, duration, lower, upper, stage_name):
    # Computes ramped target temperature during a stage
    ramp = upper - lower
    if ramp > 0 and stage_names[reflow_stage] == "Preheat":
        max_temp = lower + MAX_RAMP_RATE * stage_elapsed
        linear_target = lower + ramp * min(1.0, stage_elapsed / duration)
        return min(linear_target, max_temp)
    return lower + ramp * min(1.0, stage_elapsed / duration)

# ───── Init ─────
display.show_startup()
utime.sleep(1)
last_display_update = utime.ticks_ms()

# ───── Main Loop ─────
while True:
    encoder.update()

    # ───── Menu ─────
    if current_mode == MODE_MENU:
        # Navigate menu with encoder
        direction = encoder.get_position()
        if direction != 0:
            selected_index = direction % len(menu_items)

        if encoder.was_pressed():
            # Select mode
            if selected_index == 0:
                current_mode = MODE_MANUAL
                encoder.position = 0
            elif selected_index == 1:
                current_mode = MODE_REFLOW
                encoder.position = 0

        # Update display periodically
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
        # Adjust setpoint with encoder
        manual_setpoint += encoder.get_position()
        manual_setpoint = max(0, min(300, manual_setpoint))
        encoder.position = 0

        current_temp = thermo.read_temp() or 0.0

        # Bang-bang control with 2°C hysteresis
        if current_temp < manual_setpoint - 2:
            ssr.on()
        elif current_temp > manual_setpoint + 2:
            ssr.off()

        # Periodically update display
        now = utime.ticks_ms()
        if utime.ticks_diff(now, last_display_update) > 250:
            display.show_temp(current_temp, manual_setpoint)
            last_display_update = now

        # Exit manual mode
        if encoder.was_pressed():
            ssr.off()
            current_mode = MODE_MENU
            encoder.position = 0

    # ───── Reflow Mode ─────
    elif current_mode == MODE_REFLOW:
        now = utime.ticks_ms()

        if reflow_start_time is None:
            # Initialize reflow state
            reflow_start_time = now
            reflow_stage = 0
            ssr.off()
            pid = PID(kp=P, ki=I, kd=D, setpoint=0, output_limits=(0, 100))
            pid.reset()
            try:
                with open("log.csv", "w") as f:
                    f.write("Time,Stage,Temp,Setpoint,PID%\n")
            except:
                pass

        current_temp = thermo.read_temp() or 0.0
        stage_duration, lower_bound, upper_bound = reflow_profile[reflow_stage]
        stage_name = stage_names[reflow_stage]

        if stage_start_time is None:
            # Wait until temperature reaches lower bound
            if current_temp < lower_bound:
                pid.setpoint = lower_bound
                output = pid.compute(current_temp)
                
                #soften our landing when we near target temp to plan for thermal inertia
                if output is not None and current_temp >= lower_bound - 8: 
                    output = output * reflow_output_reduction
                    
                if output is not None:
                    ssr.on() if output > 0 else ssr.off()

                # Display wait screen
                if utime.ticks_diff(now, last_display_update) > 500:
                    display.oled.fill(0)
                    display.oled.text(f"{stage_name}: Waiting", 0, 0)
                    display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 12)
                    display.oled.text("Target: {:.1f} C".format(lower_bound), 0, 24)
                    display.oled.text("Press to abort", 0, 50)
                    display.oled.show()
                    last_display_update = now

                if encoder.was_pressed():
                    ssr.off()
                    current_mode = MODE_MENU
                    encoder.position = 0
                continue
            else:
                stage_start_time = now

        # Stage is active
        stage_elapsed = utime.ticks_diff(now, stage_start_time) // 1000
        target_temp = compute_target_temp(stage_elapsed, stage_duration, lower_bound, upper_bound, stage_name)

        pid.setpoint = target_temp
        output = pid.compute(current_temp)

        # Feedforward: reduce output as we approach reflow peak
        if output is not None and stage_name == "Reflow" and current_temp >= upper_bound - 2:
            output = output * reflow_output_reduction


        if output is not None:
            total_elapsed = utime.ticks_diff(now, reflow_start_time) // 1000
            log_data(total_elapsed, reflow_stage + 1, current_temp, pid.setpoint, output)

            # Time-proportion SSR control (1s window)
            window_ms = 1000
            on_time = int(output / 100 * window_ms)
            cycle_pos = utime.ticks_diff(now, stage_start_time) % window_ms
            ssr.on() if cycle_pos < on_time else ssr.off()

        # Stage complete
        if stage_elapsed >= stage_duration:
            reflow_stage += 1
            if reflow_stage >= len(reflow_profile):
                # End of reflow process
                ssr.off()
                current_mode = MODE_MENU
                encoder.position = 0
                stage_start_time = None
                reflow_start_time = None
                continue
            stage_start_time = None
            pid.reset()

        # Display reflow stage status
        if utime.ticks_diff(now, last_display_update) > 500:
            display.oled.fill(0)
            display.oled.text(f"{stage_name} Stage", 0, 0)
            display.oled.text("Target: {:.1f} C".format(target_temp), 0, 12)
            display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 24)
            display.oled.text("Time: {}s".format(stage_elapsed), 0, 36)
            display.oled.text("Press to abort", 0, 50)
            display.oled.show()
            last_display_update = now

        # Abort reflow
        if encoder.was_pressed():
            ssr.off()
            current_mode = MODE_MENU
            stage_start_time = None
            reflow_start_time = None
            encoder.position = 0

    utime.sleep_ms(10)
