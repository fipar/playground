\\ 3.1.a
(define expt
  M 0 -> 1
  0 N -> 0
  M N -> (expt-h M N 1)
  )

(define expt-h
  M 0 Accum -> Accum 
  M N Accum -> (* M (expt-h M (- N 1) Accum))
  )

\\ 3.1.c

\\ If the number ends in 2, 3, 7 or 8, it is not a perfect square.
\\ Therefore, get last digit from number.
\\ The next function expects D to be the string representation of a number (created with make-string)
(define last-digit-of
  D -> D where (= D (pos D 0))
  D -> (last-digit-of (tlstr D)))

(define last-digit-of-h
  D -> (last-digit-of (make-string "~S" D)))


(define square?
  N -> false where (= "2" (last-digit-of-h N))
  N -> false where (= "3" (last-digit-of-h N))
  N -> false where (= "7" (last-digit-of-h N))
  N -> false where (= "8" (last-digit-of-h N))
  N -> (square-h N 1))

\\ So the previous function is used as a simple heuristic to shortcut failed searches if the number is large

(define square-h
  N M -> true where (= N (* M M))
  N M -> false where (> (* M M) N)
  N M -> (square-h N (+ 1 M)))

\\ 3.1.b

(define remainder
  N D -> N where (> D N)
  N D -> (remainder (- N D) D))

(define integer-part
  N -> N where (integer? N)
  N -> (- N (remainder N 1)))

(define to-power-10
  1 -> 10
  N -> (* 10 (to-power-10 (- N 1))))

\\ first version. does not work properly, at least on sbcl, because new digits are added when adding (/ 1 RoundFactor)

(define round_n
  M N -> (let
	    RoundFactor (to-power-10 N)
	    RoundFactorP1 (to-power-10 (+ N 1))
   	    IntegerPart (integer-part M)
   	    Remainder (remainder M 1)
   	    DecimalPart (integer-part (* RoundFactor (remainder M 1)))
	    DecimalPartP1 (integer-part (* RoundFactorP1 (remainder M 1)))
	    Diff (* RoundFactor (- (/ DecimalPartP1 RoundFactorP1) (/ DecimalPart RoundFactor)))
	    (if (> Diff 0.5) (+ (/ 1 RoundFactor) (+ IntegerPart (/ DecimalPart RoundFactor))) (+ IntegerPart (/ DecimalPart RoundFactor)) ) ))
