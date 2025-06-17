from machine import Pin
import utime

def should_cutoff(current_temp, target_temp, ramp_rate, cutoff_k=7, min_margin=2):
    cutoff_margin = max(min_margin, cutoff_k * abs(ramp_rate))
    return current_temp >= target_temp - cutoff_margin

class BaseMode:
    def __init__(self, display, encoder, thermo, ssr):
        self.display = display
        self.encoder = encoder
        self.thermo = thermo
        self.ssr = ssr
        self.last_display_update = utime.ticks_ms()

    def update(self):
        """Called every loop iteration. Returns new mode if mode should change."""
        pass

    def update_display(self, force=False):
        """Update display if enough time has passed"""
        now = utime.ticks_ms()
        if force or utime.ticks_diff(now, self.last_display_update) > 200:
            self.last_display_update = now
            return True
        return False

class MenuMode(BaseMode):
    def __init__(self, display, encoder, thermo, ssr):
        super().__init__(display, encoder, thermo, ssr)
        self.menu_items = ["Manual Mode", "Reflow Mode", "Set Profile"]
        self.selected_index = 0

    def update(self):
        # Navigate menu with encoder
        delta = self.encoder.get_position()
        if delta != 0:
            self.selected_index = (self.selected_index + delta) % len(self.menu_items)
            self.encoder.position = 0

        if self.encoder.was_pressed():
            # Select mode
            if self.selected_index == 0:
                return "MANUAL"
            elif self.selected_index == 1:
                return "REFLOW"
            elif self.selected_index == 2:
                return "SET_REFLOW"

        # Update display
        if self.update_display():
            current_temp = self.thermo.read_temp() or 0.0
            self.display.oled.fill(0)
            self.display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 0)
            for i, item in enumerate(self.menu_items):
                prefix = ">" if i == self.selected_index else " "
                self.display.oled.text(f"{prefix}{item}", 0, 16 + i * 12)
            self.display.oled.show()

        return "MENU"

class ManualMode(BaseMode):
    def __init__(self, display, encoder, thermo, ssr):
        super().__init__(display, encoder, thermo, ssr)
        self.setpoint = 150
        self.last_temp = None
        self.last_temp_time = None
        self.ramp_rate = 0

    def update(self):
        # Adjust setpoint with encoder
        delta = self.encoder.get_position()
        if delta != 0:
            self.setpoint = max(0, min(300, self.setpoint + delta))
            self.encoder.position = 0

        current_temp = self.thermo.read_temp() or 0.0
        now = utime.ticks_ms()
        # Calculate ramp rate
        if self.last_temp is not None and self.last_temp_time is not None:
            dt = utime.ticks_diff(now, self.last_temp_time) / 1000.0
            if dt > 0:
                self.ramp_rate = (current_temp - self.last_temp) / dt
        self.last_temp = current_temp
        self.last_temp_time = now

        # Predictive cutoff for inertia
        if should_cutoff(current_temp, self.setpoint, self.ramp_rate, cutoff_k=7):
            self.ssr.off()
        elif current_temp < self.setpoint - 2:
            self.ssr.on()
        elif current_temp > self.setpoint + 2:
            self.ssr.off()

        # Update display
        if self.update_display():
            self.display.show_temp(current_temp, self.setpoint)

        # Exit manual mode
        if self.encoder.was_pressed():
            self.ssr.off()
            return "MENU"

        return None

class ReflowMode(BaseMode):
    def __init__(self, display, encoder, thermo, ssr, profile, stage_names):
        super().__init__(display, encoder, thermo, ssr)
        self.profile = profile
        self.stage_names = stage_names
        self.reflow_start_time = None
        self.stage_start_time = None
        self.reflow_stage = 0
        self.reflow_output_reduction = 0.7
        self.P = 1.2
        self.I = 0.2
        self.D = 3.0
        self.MAX_RAMP_RATE = 2.5
        self.last_temp = None
        self.last_temp_time = None
        self.temp_ramp_rate = 0
        self.COMPENSATION_FACTORS = {
            "Preheat": 0.5,
            "Soak": 0.6,
            "Reflow": 0.3,
            "Cooldown": 1.0
        }
        self.cutoff_k = 7

    def compute_target_temp(self, stage_elapsed, duration, lower, upper, stage_name):
        ramp = upper - lower
        if ramp > 0 and self.stage_names[self.reflow_stage] == "Preheat":
            max_temp = lower + self.MAX_RAMP_RATE * stage_elapsed
            linear_target = lower + ramp * min(1.0, stage_elapsed / duration)
            return min(linear_target, max_temp)
        return lower + ramp * min(1.0, stage_elapsed / duration)

    def calculate_thermal_compensation(self, current_temp, target_temp, stage_name):
        now = utime.ticks_ms()
        
        # Calculate temperature ramp rate
        if self.last_temp is not None and self.last_temp_time is not None:
            dt = utime.ticks_diff(now, self.last_temp_time) / 1000.0  # Convert to seconds
            if dt > 0:
                self.temp_ramp_rate = (current_temp - self.last_temp) / dt
        
        self.last_temp = current_temp
        self.last_temp_time = now

        # Base compensation factor for this stage
        base_factor = self.COMPENSATION_FACTORS.get(stage_name, 0.8)
        
        # Additional compensation based on temperature difference and ramp rate
        temp_diff = target_temp - current_temp
        if temp_diff > 0:  # Only compensate when heating
            # Reduce output more aggressively when:
            # 1. We're close to target (within 10°C)
            # 2. We have a high ramp rate (> 1°C/sec)
            if temp_diff < 20:
                proximity_factor = temp_diff / 10  # Linear reduction as we get closer
                ramp_factor = max(0.5, 1.0 - abs(self.temp_ramp_rate))  # Reduce output if ramping fast
                return base_factor * proximity_factor * ramp_factor
        
        return 1.0  # No compensation when cooling or far from target

    def update(self):
        now = utime.ticks_ms()
        MIN_OUTPUT_THRESHOLD = 1.0  # percent
        MIN_ON_TIME_MS = 50         # ms
        window_ms = 1000

        if self.reflow_start_time is None:
            self.reflow_start_time = now
            self.reflow_stage = 0
            self.ssr.off()
            self.last_temp = None
            self.last_temp_time = None
            self.temp_ramp_rate = 0
            try:
                with open("log.csv", "w") as f:
                    f.write("Time,Stage,Temp,Setpoint,Output,RampRate\n")
            except:
                pass

        current_temp = self.thermo.read_temp() or 0.0
        stage_duration, lower_bound, upper_bound = self.profile[self.reflow_stage]
        stage_name = self.stage_names[self.reflow_stage]

        # Calculate ramp rate for predictive cutoff
        if self.last_temp is not None and self.last_temp_time is not None:
            dt = utime.ticks_diff(now, self.last_temp_time) / 1000.0
            if dt > 0:
                self.temp_ramp_rate = (current_temp - self.last_temp) / dt
        self.last_temp = current_temp
        self.last_temp_time = now

        # --- Stage start logic ---
        if self.stage_start_time is None:
            if stage_name == "Preheat":
                # Start Preheat immediately, no waiting
                self.stage_start_time = now
            elif current_temp < lower_bound:
                # Waiting logic for other stages: use bang-bang control
                if current_temp < lower_bound - 2:
                    self.ssr.on()
                else:
                    self.ssr.off()
                if self.update_display():
                    self.display.oled.fill(0)
                    self.display.oled.text(f"{stage_name}: Waiting", 0, 0)
                    self.display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 12)
                    self.display.oled.text("Target: {:.1f} C".format(lower_bound), 0, 24)
                    self.display.oled.text("Press to abort", 0, 50)
                    self.display.oled.show()
                if self.encoder.was_pressed():
                    self.ssr.off()
                    self.stage_start_time = None
                    return "MENU"
            else:
                self.stage_start_time = now

        # --- Stage is active ---
        # PAUSE TIMER IF TEMP DROPS BELOW LOWER BOUND
        if stage_name != "Preheat" and current_temp < lower_bound:
            # Pause timer, re-engage heating
            if current_temp < lower_bound - 2:
                self.ssr.on()
            else:
                self.ssr.off()
            # Debug logging for PID output and cutoff status
            try:
                with open("debug_soak.log", "a") as f:
                    f.write("BelowBound: temp={:.2f}, set={:.2f}, out={:.2f}\n".format(current_temp, lower_bound, 100 if self.ssr.control.value() else 0))
            except:
                pass
            if self.update_display():
                self.display.oled.fill(0)
                self.display.oled.text(f"{stage_name}: Below Bound", 0, 0)
                self.display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 12)
                self.display.oled.text("Target: {:.1f} C".format(lower_bound), 0, 24)
                if stage_name == "Soak":
                    self.display.oled.text("Soak Paused", 0, 36)
                self.display.oled.text("Press to abort", 0, 50)
                self.display.oled.show()
            if self.encoder.was_pressed():
                self.ssr.off()
                self.stage_start_time = None
                return "MENU"
            if self.temp_ramp_rate is None:
                self.temp_ramp_rate = 0
            total_elapsed = utime.ticks_diff(now, self.reflow_start_time) // 1000
            self.log_data(total_elapsed, self.reflow_stage + 1, current_temp, lower_bound, 100 if self.ssr.control.value() else 0)
            return None

        # Only increment timer if temp is above lower bound
        stage_elapsed = utime.ticks_diff(now, self.stage_start_time) // 1000
        target_temp = self.compute_target_temp(stage_elapsed, stage_duration, lower_bound, upper_bound, stage_name)

        if stage_name == "Preheat":
            if current_temp < target_temp - 2:
                self.ssr.on()
            elif current_temp >= target_temp:
                self.ssr.off()
            output = 100 if self.ssr.control.value() else 0
        else:
            # PWM heating logic
            error = target_temp - current_temp
            if error > 0:
                # Compute PWM duty cycle (0-100%)
                duty_cycle = min(100, max(0, error * 10))  # Scale error to get reasonable duty cycle
                on_time = int(duty_cycle / 100 * window_ms)
                if on_time < MIN_ON_TIME_MS:
                    on_time = 0
                cycle_pos = utime.ticks_diff(now, self.stage_start_time) % window_ms
                self.ssr.on() if cycle_pos < on_time else self.ssr.off()
                output = duty_cycle
            else:
                self.ssr.off()
                output = 0
        if self.temp_ramp_rate is None:
            self.temp_ramp_rate = 0
        total_elapsed = utime.ticks_diff(now, self.reflow_start_time) // 1000
        self.log_data(total_elapsed, self.reflow_stage + 1, current_temp, target_temp, output)

        # Stage complete (only if timer has run for full duration above lower bound)
        if stage_elapsed >= stage_duration:
            self.reflow_stage += 1
            if self.reflow_stage >= len(self.profile):
                self.ssr.off()
                return "MENU"
            self.stage_start_time = None
            return None

        if self.update_display():
            self.display.oled.fill(0)
            self.display.oled.text(f"{stage_name} Stage", 0, 0)
            self.display.oled.text("Target: {:.1f} C".format(target_temp), 0, 12)
            self.display.oled.text("Temp: {:.1f} C".format(current_temp), 0, 24)
            self.display.oled.text("Time: {}s".format(stage_elapsed), 0, 36)
            self.display.oled.text("Press to abort", 0, 50)
            self.display.oled.show()

        if self.encoder.was_pressed():
            self.ssr.off()
            self.stage_start_time = None
            return "MENU"

        return None

    def log_data(self, t_elapsed, stage, temp, target, output):
        # Defensive: ensure all values are numbers
        try:
            if temp is None or not isinstance(temp, (int, float)):
                temp = 0.0
            if target is None or not isinstance(target, (int, float)):
                target = 0.0
            if output is None or not isinstance(output, (int, float)):
                output = 0.0
            if self.temp_ramp_rate is None or not isinstance(self.temp_ramp_rate, (int, float)):
                ramp = 0.0
            else:
                ramp = self.temp_ramp_rate
            with open("log.csv", "a") as f:
                f.write("{},{:.1f},{:.1f},{:.1f},{:.1f},{:.1f}\n".format(
                    t_elapsed, stage, temp, target, output, ramp))
        except Exception as e:
            pass

class ProfileEditMode(BaseMode):
    def __init__(self, display, encoder, thermo, ssr, profile, stage_names):
        super().__init__(display, encoder, thermo, ssr)
        self.profile = profile
        self.stage_names = stage_names
        self.profile_edit_stage = -1  # Start in stage selection
        self.profile_edit_param = 0
        self.selected_index = 0

    def update(self):
        # Get encoder delta to change current param value
        delta = self.encoder.get_position()
        if delta != 0:
            if self.profile_edit_stage == -1:  # Stage selection mode
                # Just update the display selection
                self.selected_index = (self.selected_index + delta) % (len(self.profile) + 1)  # +1 for menu exit
            else:  # Parameter editing mode
                stage = self.profile[self.profile_edit_stage]
                if self.profile_edit_param == 0:  # Duration
                    stage[0] = max(10, min(300, stage[0] + delta))
                elif self.profile_edit_param == 1:  # Low Temp
                    stage[1] = max(0, min(stage[2], stage[1] + delta))
                elif self.profile_edit_param == 2:  # High Temp
                    stage[2] = max(stage[1], min(300, stage[2] + delta))
            self.encoder.position = 0

        # Handle button press
        if self.encoder.was_pressed():
            if self.profile_edit_stage == -1:  # Stage selection mode
                if self.selected_index == len(self.profile):  # Menu exit option
                    return "MENU"
                else:
                    self.profile_edit_stage = self.selected_index
                    self.profile_edit_param = 0  # Start with duration
            else:  # Parameter editing mode
                self.profile_edit_param = (self.profile_edit_param + 1) % 3
                if self.profile_edit_param == 0:  # If we've cycled through all parameters
                    self.profile_edit_stage = -1  # Go back to stage selection
                    self.selected_index = 0  # Reset selection

        # Update display
        if self.update_display():
            self.display.oled.fill(0)
            
            if self.profile_edit_stage == -1:  # Stage selection mode
                for i, name in enumerate(self.stage_names):
                    prefix = ">" if i == self.selected_index else " "
                    self.display.oled.text(f"{prefix}{name}", 0, i * 12)
                # Add menu exit option
                prefix = ">" if self.selected_index == len(self.profile) else " "
                self.display.oled.text(f"{prefix}Back to Menu", 0, len(self.profile) * 12)
            else:  # Parameter editing mode
                stage = self.profile[self.profile_edit_stage]
                param_labels = ["Duration", "Low Temp", "High Temp"]
                self.display.oled.text(f"Edit {self.stage_names[self.profile_edit_stage]}", 0, 0)
                for i in range(3):
                    prefix = ">" if i == self.profile_edit_param else " "
                    self.display.oled.text(f"{prefix}{param_labels[i]}: {stage[i]}", 0, 16 + i * 12)
            
            self.display.oled.show()

        return None 