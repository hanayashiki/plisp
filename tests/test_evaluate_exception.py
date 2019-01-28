from tests.utils import test_evaluate, print_asserted_expection

print_asserted_expection("""
(define (recurse n) 
  (if (= n 0) ""
    (* n 
      ((recurse (- n 1))))
  )
)

(recurse 5)
""")