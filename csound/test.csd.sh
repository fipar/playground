#!/bin/bash

# this is not really a tempo, but how much a second lasts for me.
# essentially, in this very crude test, I am always using one second as the duration of beat-like events,
# and by multiplying by tempo I get the actual speed I want. 

# there are surely better ways to do this but playing with tempo from 0.05 to 0.8 I get
# very interesting results!
tempo=0.1

cat<<EOF > test.csd

<CsoundSynthesizer>;
  ; test.csd - a Csound structured data file

<CsOptions>
  -W -d -o tone.wav
</CsOptions>

<CsInstruments>

  ; originally tone.orc
  sr = 44100
  kr = 4410
  ksmps = 10
  nchnls = 2
  ;; 2 (iterations that I want to wait for) times 4 (seconds that an iteration lasts) times how much a second lasts
EOF

cat<<EOF >> test.csd

  instr   1
      iamp = p4
      panxp = p6
      kampenv linseg 0, 0.01, iamp, (p3 - 0.01), 0
      kpan lfo panxp, 2
      kpan = kpan + 0.5 ;; "The raw signal from lfo is bipolar; that is, it will run from −0.5 to 0.5. We need to add 0.5 to it so it will vary from 0 to 1."
      a1 oscil kampenv, p5, 1 ; simple oscillator
      aL, aR pan2 a1, kpan
      outs aL, aR
      ;out a1
  endin

instr 2
  iamp = p4
  kampenv linseg 0, 0.01, iamp, (p3 - 0.01), 0
  ifreq = cpspch(p5)
  index = 3
  kindexenv linseg index, p3, 0
  a1 foscil kampenv, ifreq, 1.073, 1,kindexenv, 1
  a2 foscil kampenv, ifreq*.75, 1.073, 1,kindexenv, 1
  a3 foscil kampenv, ifreq*.70, 1.073, 1,kindexenv, 1
  a4 foscil kampenv, ifreq*1.13, 1.073, 1,kindexenv, 1
  out a1+a2+a3+a4
  endin
</CsInstruments>

<CsScore>
  ; originally tone.sco
  f1 0 8192 10 1

EOF

# maybe I won't even need to use csound loops, and instead just loop in bash?

loopDur=4
totalLoops=96

for i in $(seq 0 $totalLoops); do
  startBeat=$(echo "$tempo * $loopDur * $i"|bc)
  cat <<EOF>>test.csd
i1 $startBeat $tempo  13000 [ 90 + 0 ]  1.7
i1     +        $tempo  13000 [ 130 + 0 ] 1.1
i1     +        $tempo  13000 [ 123 + 0 ] 0.4
i1     +        $tempo  13000 [ 101 + 0 ] 0.9

EOF

done

loopsToSkip=32

for i in $(seq $loopsToSkip $totalLoops); do
  startBeat=$(echo "$loopDur * $tempo * $i"|bc)
  cat <<EOF>>test.csd
i1 $startBeat  $tempo  13000 [ (90 + 0) * 1.25 ] 1.9
i1     +        $tempo  13000 [ (130  + 0) * 1.25 ]  1.1
i1     +        $tempo  13000 [ (123  + 0) * 1.25 ]  0.4
i1     +        $tempo  13000 [ (101  + 0) * 1.25 ]  0.8

EOF

done

cat <<EOF>>test.csd 

 e
</CsScore>

</CsoundSynthesizer>
