# Dumpster Fire: Reflow Hotplate On A Budget
Reflow soldering doesn’t need to be expensive. This modified electronics repair hotplate is driven by a microcontroller and supports programmable thermal profiles including preheat, soak, and reflow phases — all for around $150. This includes an OLED screen and rotary encoder.

### That was my mission statement, here's why I am doing it.
I ordered some PCBs and chose not to have them preassembled to reduce cost. Once I realized how small 0402 surface mount parts are I started looking at strategies for how to solder them. A friend mentioned pick and place machines, but while I didn't go that route it led me to reflow soldering and I have been down the rabbit hole ever since.

### Where am I at?
Currently, I have the hardware done. I'm working on a BOM, but there were a lot of hardware safety considerations to take into account when modifying the hotplate unit I purchased. The wiring was simple enough, but care was taken to isolate the 3.3v circuit from the 110v circuit. The heating elements were wired in parallel, and I broke them out to two seperate 4 post terminals to handle power distrubution. I am using a solid state relay (SSR) to handle the switching of the AC current, and this is all controlled by a pico that monitors temp and controls the logic of the reflow process using a simple Proportional, Integral, and Derivative (PID) algorithm.

Where I am at with the software is I am working to tune the PID to get to a point where I can follow a reflow profile for a given solder paste. My other variable with this is that I have been testing using a reflow profile of 150c - 180c soak and then a reflow target of 230c, but my actual reflow temp for the paste that I want to use is 155c. When I go back to testing I am going to update this, but I am cautiously optimistic currently that I can get there.

#### first run
![image](https://github.com/user-attachments/assets/2f3d4b7b-8331-4ea2-8b62-7e08c69fe146)

#### sixth run
![image](https://github.com/user-attachments/assets/c8b9ecd7-0dbb-4168-8ba8-7ca8c1be4b55)

### Eight time is the charm
Ok, so I updated the hardcoded solder profile to use the lower temp profile for the soldering paste I am actually going to use, and... I was able to follow the profile from what I can see. Here's the curve:
![image](https://github.com/user-attachments/assets/dd616ea5-446e-4a27-946c-683a630c47fe)

And here is the data sheet for the paste I am going to use to solder my PCBs. It appears to be within spec! 🎉
![image](https://github.com/user-attachments/assets/269a0a6a-e1b9-4519-a1c2-49138f2be957)

Full datasheet here: https://qualitek.com/863_bi58_tds.pdf
