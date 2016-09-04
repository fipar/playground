\\ 2.1
(output "The sum of the two is ~A~%" (+ (input)(input)))

\\ 2.2

(define cent-to-far
  X -> (+ 32 (* X 1.8))
  )

(define fahr-to-cent
  X -> (/ (- X 32) 1.8) 
  )

\\ 2.3
\* But these aren't completely right, as X or Y can't be anything other than 0 or 1. Perhaps the correct thing to do is
   to list the complete truth table?
*\

(define and-gate
  1 1 -> 1
  X Y -> 0
  )

(define or-gate
  0 0 -> 0
  X Y -> 1
  )

(define inverter
  0 -> 1
  1 -> 0
  )

