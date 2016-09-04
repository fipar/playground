\\ 2.1
(output "The sum of the two is ~A~%" (+ (input)(input)))

\\ 2.2

(define cent-to-far
  X -> (+ 32 (* X 1.8))
  )

(define fahr-to-cent
  X -> (/ (- X 32) 1.8) 
  )
