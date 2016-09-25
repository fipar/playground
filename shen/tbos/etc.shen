\\ 3rd ed, page 73

(define double-everything
  X -> (map (* 2) X))

\\ to map elements as the second arg to the function, an abstraction is needed: 
(define divide-by-ten
  X -> (map (/. X (/ X 10)) X))

\\ macro example
(defmacro infixplus
 [X ++ Y] -> [+ X Y])
