# Dumpster Fire: Reflow Hotplate On A Budget
Reflow soldering doesn’t need to be expensive. This modified electronics repair hotplate is driven by a microcontroller and supports programmable thermal profiles including preheat, soak, and reflow phases — all for around $150. This includes an OLED screen and rotary encoder.

### That was my mission statement, here's why I am doing it.
I ordered some PCBs and chose not to have the preassembled to reduce cost. Once I realized how small 0402 surface mount parts are I started looking at strategies for how to solder them. A friend mentioned pick and place machines, but while I didn't go that route it led me to reflow soldering and I have been down the rabbit hole ever since.

### Where am I at?
Currently, I have the hardware done. I'm working on a BOM, but there were a lot of hardware safety considerations to take into account when modifying the hotplate unit I purchased. The wiring was simple enough, but care was taken to isolate the 3.3v circuit from the 110v circuit. The heating elements were wired in parallel, and I broke them out to two seperate 4 post terminals to handle power distrubution. I am using a solid state relay (SSR) to handle the switching of the AC current, and this is all controlled by a pico that monitors temp and controls the logic of the reflow process using a simple Proportional, Integral, and Derivative (PID) algorithm.

Where I am at with the software is I am working to tune the PID to get to a point where I can follow a reflow profile for a given solder paste. My other variable with this is that I have been testing using a reflow profile of 150c - 180c soak and then a reflow target of 230c, but my actual reflow temp for the paste that I want to use is 155c. When I go back to testing I am going to update this, but I am cautiously optimistic currently that I can get there.

[first run](https://github.com/EdibleTuber/DumpsterFire-Reflow-Hotplate/blob/main/images/first_run.jpg)

[sixth run](https://github.com/EdibleTuber/DumpsterFire-Reflow-Hotplate/blob/main/images/sixth_run.jpg)
