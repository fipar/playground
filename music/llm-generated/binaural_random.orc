
; =================================================================
; BINAURAL RANDOMIZER ORCHESTRA
; For Csound 6.16
; Processes an input sound file into binaural stereo with
; slight, random movement.
; =================================================================

sr = 44100  ; Sample rate
ksmps = 32    ; Control rate samples
nchnls = 2    ; Stereo output
0dbfs = 1     ; 0dB Full Scale is 1

; -----------------------------------------------------------------
; Instrument 1: Audio Processing
; -----------------------------------------------------------------
instr 1
  ; p4 = input file name (string)
  ; p5 = amplitude multiplier
  ; p6 = rate of random movement (in Hz)
  ; p7 = amount of random movement (in degrees)

  ; -- Read Input Audio --
  ; diskin2 reads a stereo audio file.
  aInL, aInR diskin2 p4, 1, 0, 1
  aInput = (aInL + aInR) * 0.5 ; Mix to mono for panning
  aInput *= p5 ; Apply amplitude multiplier

  ; -- Generate Random Movement --
  kAzimuthRate = p6   ; How fast the direction changes (e.g., 0.2 Hz)
  kAzimuthRange = p7  ; How much the direction changes (e.g., 15 degrees)

  ; Create a slow, random, wandering value for the azimuth
  kAzimuth randi kAzimuthRate, kAzimuthRate

  ; -- Apply Stereo Panning --
  ; pan2 distributes a mono signal across two stereo channels.
  ; The panning position is controlled by kAzimuth.
  ; We scale it to a 0-1 range, where 0 is full left and 1 is full right.
  ; The formula (kAzimuth + kAzimuthRange) / (kAzimuthRange * 2) maps
  ; the range [-kAzimuthRange, +kAzimuthRange] to [0, 1].
  aOutL, aOutR hrtfmove2 aInput, kAzimuth, 0, "/Library/Frameworks/CsoundLib64.framework/Versions/6.0/samples/hrtf-44100-left.dat", "/Library/Frameworks/CsoundLib64.framework/Versions/6.0/samples/hrtf-44100-right.dat"

  ; -- Output --
  outs aOutL, aOutR

endin
