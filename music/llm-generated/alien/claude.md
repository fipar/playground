Please create a web-based, local-first single-page app that should run on Safari, is called alien.html, and works according to this spec:

- The app has a play, stop, and record buttons, emulating those of a tape player, that cause sound to start, be recorded (to a file), and stop, respectively.
- There are 5 sound sources available, each with volume knob (if volume is at 0, that sound source is disabled):
  - 3 are oscilators, each with :
    - a shape knob to range from sine to square (in a continuous way)
	- a frequency knob, which should range in the audible human range. 
	- a midi input file field which, if populated, causes the oscilator to choose frequencies based on the input file, in a loop
  - a noise source with a noise type selector:
    - pink
	- white
	- normal (values are randomly taken from a normal distribution)
	- exponential (values are randomly taken from an exponential distribution)
  - an audio file input field which, if populated, plays the file in a loop as another sound source, and offers the following controls:
    - an input text field to enter playback speed (default to 100; value is a percentage)
	- forward or reverse playback (default to forward)
	- skip playback: randomly skip segments of the audio file on each loop
