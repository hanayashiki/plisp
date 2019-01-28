from tests.utils import assert_exception
from tests.utils import test_evaluate

test_evaluate("""
(define (fact n sum)
  (if (= n 0) sum
    (fact (- n 1) (* n sum)))
)
(fact 3 1)
""", "None|6.0")