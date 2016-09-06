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
