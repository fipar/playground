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
  nchnls = 1
  instr   1
      iamp = p4
      kampenv linseg 0, 0.01, iamp, (p3 - 0.01), 0
      a1 oscil kampenv, p5, 1 ; simple oscillator
         out a1
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

;;  { 2 nn
;;  i1      $nn  1 5000 440
;;  i1      $nn  1.1 5000 460
;;  i1      $nn  1.1 5000 470
;;  i1      $nn  1.2 5000 410
;;  i1      $nn  1.4 5000 1470
;;  i1      $nn  1.7 5000 270
;;  }


;;  i2  3.0 1.1 5000 440
;;  i2  4.1  1.1 5000 740
;;  i2  5.2 1.1 5000 2727
;;  i1 6.7 7.8 9000 130
;;  i2 7.2 4.5 9000 160
;;
;;
;;  i2 18 0.5 9000 160
;;  i2 18.5 0.5 9000 130
;;  i2 19 0.5 9000 120
;;  i2 19.6 0.5 9000 190


;;  i2 0 0.5 9000 8.00 
;;  i2 0.5 0.5 9000 8.01
;;  i2 1 0.5 9000 8.03 
;;  i2 1.5 0.5 9000 8.05
;;  i2 2 0.5 9000 8.09 
;;  i2 2.5 0.5 9000 8.08
;;  i2 3 2 9000 8.02 

{ 6 nn
i1 [ $nn * 4 ]  1  13000 90
i1     +        1  13000 130
i1     +        1  13000 123
i1     +        1  13000 101
}

;; 12 = 3 (iterations that I want to wait for) times 4 (seconds that an iteration lasts)
{ 3 nn
i1 [ 12 + $nn * 4 ]  1  13000 [ 90 * 1.25 ]
i1     +        1  13000 [ 130 * 1.25 ]
i1     +        1  13000 [ 123 * 1.25 ]
i1     +        1  13000 [ 101 * 1.25 ]
}

;i2 3 2 9000 100
;i2 5 2 9000 70
;i2 7 2 9000 60

;; { 6 nn 
;;  i1 [ 0 + $nn ]   1 9000 130
;;  i1 [ 2.3 + $nn ] . 9000 130
;;  i1 [ 3.1 + $nn ] . 9000 90
;;  i1 [ 0 + $nn ]   . 9000 130
;; }

 e
</CsScore>

</CsoundSynthesizer>
