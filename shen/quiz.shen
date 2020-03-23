\* q1 *\

(define minusX
  [X] X -> []
  [] _ -> []
  [X | Y] X -> Y
  [X | Y] Z -> (cons X (minusX Y Z)))

(let List ["bar" "foo" "baz"]
  (map (minusX List) List))

\* q2 *\

(define minus
  [] _ -> []
  [H] [H] -> []
  [H1|T1] [H2|T2] -> (cons H1 (minus T1 T2)) where (not (= H1 H2))
  [_|T1] [_|T2] -> (minus T1 T2))

(let A ["bar" "foo" "baz"] B ["bar" "moo" "gaz"]
  (minus A B))

(let A ["bar" "foo" "baz"] B ["bar" "moo" "gaz"]
  (minus B A))


