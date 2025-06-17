# Disclaimer
I am not a certified electrician in any way, shape, or form. I in no way advocate anybody doing this unless you know what you are getting into and understand the risks. Household AC current is dangerous and every precaution should be taken to prevent touching live wires, separating and grounding circuits, fire prevention, etc. Never work with exposed live wires, make sure the hotplate switch is off, and don't plug this thing into AC current while you are working on the internals. Being zapped by AC 110v isn't fun, and all that being said I still didn't follow my own advice and recieved a shock while working on this project. Have a fire prevention and response strategy worked out in advance so you can respond accordingly in the event a fire does break out.

Again, please don't do this unlesss you are going to take the time to learn more about the type of electricity you are dealing with (which you should be learning about to master the fundamentals), and the precautions that need to be taken to stay safe and healthy.

All right. If you are still with me let's talk about the hardware.

# The Hardware

When I started to look for a reflow hotplate when I started down this path I landed on an 850w model that was $60. While I was waiting on it to arrive I was on a deep dive into the reflow process and contemplating how I was going to follow a reflow profile once I started learning about the things that could potentially go wrong in each of the reflow stages. The hotplate arrived and I immediately took the bottom plate off. There was a ton of space inside and the wiring was simple enough. The wheels began to turn from there...

## List of materials
I am going to be including a bill of materials (BOM) at some point in docs section, but here's a part list with accompanying descriptions of how I used them in this project:
* Heating Element: 850W electronics repair hotplate - [on amazon](https://www.amazon.com/dp/B082H12PPT?ref=ppx_yo2ov_dt_b_fed_asin_title)
  *This is the hotplate I ordered and is the base for this build. It seems to work well enough for what I need it for, and the main plus is enough extra space in the electronics box for my aftermarket needs. There is a 10amp fuse built into the plug, and the wiring was simple as can be seen in the image in the above section. disassembling the plastic insert enclosure was a bit tricky, but with some patience, finesse, and a small thin screwdriver the tab that is between the plastic insert and the top of the box can be lifted slightly to disengage the locking teeth. Once that's done the collar holding this insert in place can be slid off of the insert and then the whole circuit board enclosure completely removed from the unit.
* Raspberry Pi Pico: brains of the operation
* Solid State Relay (SSR): switches AC power to heating elements
* Thermocouple + MAX31855: accurate temperature sensing
* OLED Display: shows current status & temperature
* Rotary Encoder: used to start cycles or select profiles
* AC to DC Converter: powers the Pico from wall AC
* 10A Fuse: came with the hotplate — keeps it safe

### work in progress
