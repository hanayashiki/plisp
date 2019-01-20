from plisp.evaluate import evaluate_list
from plisp.ast import parse
from io import StringIO
from tests.utils import assert_exception
import re

import sys
#sys.setrecursionlimit(2**31 - 1)

def test_evaluate(code : str, expected=None):
  node = parse(StringIO(code))
  result = '|'.join(map(str, evaluate_list(node)))
  if expected and result != expected:
    raise ValueError("Got [\n%s\n] when [\n%s\n] is expected. \nCode: \n=================\n%s\n=================\n" % (result, expected, code))
  return result

print(test_evaluate("(+ 1 2 3)"))

print(test_evaluate("""
(define x 1) (define y 2) x y
"""))

print(test_evaluate("""
(define 1.0 2) (define y 1.0) 1.0 y
""", expected="None|None|2.0|2.0"))

print(test_evaluate("""
(define z 19260817)
(define 1.0 2) 
(define y 
  (define z (* 1.0 y)) z) 
1.0
y
""", expected="None|None|None|2.0|4.0"))

print(test_evaluate("""
(define (z a b) (+ a b))
(z 1 2)
""", expected="None|3.0"))

print(test_evaluate("""
(define (two)
  (+ 1 1))
(two)
""", expected="None|2.0"))

print(test_evaluate("""
(define (two_plus)
  (define a 1)
  (define (fuckyou x y) 
    (+ x y a))
  fuckyou)
((two_plus) 0.5 0.5)
""", expected="None|2.0"))

print(test_evaluate("""
(define (fuck func x y)
  (define (average a b) 
    (/ (+ a b) 2))
  (define mid-val
    (func (average x y)))
  (define avg-val
    (average (func x) (func y)))
  (- avg-val mid-val))

(define a 2)

(define (func x) (define a 1) (* x x a))

(fuck func 0 1)

""", expected="None|None|None|0.25"))

print(test_evaluate("""
(if True 1 0)
""", expected="1.0"))

# print(test_evaluate("""
#   (define (acc a b step func)
#       (define (acc-iter n sum)
#           (if (> n b) sum
#               (acc-iter
#                   (+ n step)
#                   (+ sum (func n)))))
#       (acc-iter a 0))
#
#   (define (PI n)
#       (define (term n)
#           (/ 1 (* n (+ n 2))))
#       (* 8 (acc 1 n 4 term)))
#
#   (PI 2000)
#   """))

print(test_evaluate("""
(define (acc a b step func)
    (define (acc-iter n sum)
        (if (> n b) sum
            (acc-iter 
                (+ n step) 
                (+ sum (func n)))))
    (acc-iter a 0))

(define (PI2 n)
    (define (term n) 
        (*  (expt -1 n) 
            (/ 1
               (* (expt 3 n) (+ 1 (* 2 n))))))
    (* 3.46410161514 (acc 0 n 1 term)))

(PI2 100)

"""))

assert_exception(lambda : test_evaluate(
"""
(- "abc" 1)
"""), ValueError)

quine = \
r"""

(define code
    (cons "(define dq (char 34))"
    (cons "(define nl ' ')"
    (cons "define (iter prepend aopend cur acc end)"
    (cons "    (if (= cur null)"
    (cons "        (strcat acc end)"
    (cons "        (iter prepend append (cdr cur) (strcat prepend acc (car cur) append) end)"
    (cons "    )"
    (cons ")"
    (cons "(iter (strcat '    (cons ' dq) (strcat dq nl) code (strcat '(define code' nl) ' null))))))))))))')"
    (cons "(iter '' nl code '' '')"
    (cons "" null))))))))))))

(define dq (char 34))
(define nl ' ')
(define (iter prepend append cur acc end)
    (if (= cur null) 
        (strcat acc end)
        (iter prepend append (cdr cur) (strcat acc prepend (car cur) append) end)
    )
)
(iter (strcat '    (cons ' dq) (strcat dq nl) code (strcat '(define code' nl) ' null))))))))')
(iter '' nl code '' '')
""".strip()

print(test_evaluate(
  quine
, quine))