# Dumpster Fire: Reflow Hotplate On A Budget
Reflow soldering doesn’t need to be expensive. This modified electronics repair hotplate is driven by a microcontroller and supports programmable thermal profiles including preheat, soak, and reflow phases — all for around $150. This includes an OLED screen and rotary encoder.

### That was my mission statement, here's why I am doing it.
I ordered some PCBs and chose not to have them preassembled to reduce cost. Once I realized how small 0402 surface mount parts are I started looking at strategies for how to solder them. A friend mentioned pick and place machines, but while I didn't go that route it led me to reflow soldering and I have been down the rabbit hole ever since.

### Where am I at?
Currently, I have the hardware done. I'm working on a BOM, but there were a lot of hardware safety considerations to take into account when modifying the hotplate unit I purchased. The wiring was simple enough, but care was taken to isolate the 3.3v circuit from the 110v circuit. The heating elements were wired in parallel, and I broke them out to two seperate 4 post terminals to handle power distrubution. I am using a solid state relay (SSR) to handle the switching of the AC current, and this is all controlled by a pico that monitors temp and controls the logic of the reflow process using a simple PWM implementation with duty cycles.

On the software side I am mostly code complete now. I abandoned PID control in favor of PWM controlled heating. PID sounds fancy, but it was a pain to implement and I kept going around in circles with the tuning. PWM is much more predictable and still gave me a nice reflow heating profile execution. Exactlhy what I wanted to begin with.

### 6/17/25 Major Code Update

So, the first major thing is that the code has been refactored to be more object oriented and user friendly. Major changes:
* Mode-Based Architecture
  * Refactored code into distinct mode classes: BaseMode, MenuMode, ManualMode, ReflowMode, and ProfileEditMode
  * Clean separation of concerns and improved code organization
  * Simplified main loop by delegating control to mode classes

### 06/07/25 code update
Was doing some debugging that came up during a dry run for the small live test. This led to improved pid.py and main.py files. Softer landing when nearing the final temp target to account for thermal inertia for one, and set PID variables whose declarations are at to the top of main.py as well as adding a reflow_output_reduction variable in the same area to help with setting the total percentage output should be after reduction. Made sense so I don't have to hunt them down in the middle of main.py to change them.

Here's my latest reflow profile curve attempt. You can see a little hump there in the middle, but I made an update after that test to account for thermal intertia in the 'waiting' between stages so it should smooth out going forward.

![image](https://github.com/user-attachments/assets/33c55b41-bfc4-4988-a463-32768e45eb2e)


### Eight time is the charm - Near the end of March, 2025
Ok, so I updated the hardcoded solder profile to use the lower temp profile for the soldering paste I am actually going to use, and... I was able to follow the profile from what I can see. Here's the curve:

![image](https://github.com/user-attachments/assets/dd616ea5-446e-4a27-946c-683a630c47fe)

And here is the data sheet for the paste I am going to use to solder my PCBs. It appears to be within spec! 🎉
![image](https://github.com/user-attachments/assets/e045908c-c53b-412e-a7d8-e27033aa4b1d)

I will need to manage the active cooling to bring the temp down but this is very good news for me.

Full datasheet here: https://qualitek.com/863_bi58_tds.pdf
