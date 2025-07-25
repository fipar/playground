; =================================================================
; BINAURAL RANDOMIZER SCORE
; =================================================================

; -- Define Instrument Parameters --
;         p4: Input File (string)
;         |              p5: Amplitude (1 = no change)
;         |              |    p6: Movement Speed (Hz)
;         |              |    |    p7: Movement Amount (degrees)
; p1 p2 p3|..............|....|....|..................
; |  |  | |              |    |    |
; i 1 0 30 "input.wav"   1.0  0.3  20
;
; This example will process the first 30 seconds of the input file.
;
; To get the full duration of your audio file automatically, you can use
; a command-line flag instead of a fixed duration. For example:
; csound -o output.wav binaural_random.orc binaural_random.sco -d
; The -d flag tells Csound to run until the input file ends.
; If using the -d flag, you can set p3 to a very long time.

;           dur  input file     amp  rate range
i 1   0   60   "input_stereo.wav"    1.0  0.2  15
; This line runs Instrument 1 starting at 0 seconds for 60 seconds.
; - Input file is "input.wav".
; - Amplitude multiplier is 1.0 (no change).
; - Movement speed is 0.2 Hz (slow).
; - Movement range is 15 degrees left and right of center.

e ; End of score
