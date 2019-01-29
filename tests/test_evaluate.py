from tests.utils import assert_exception
from tests.utils import test_evaluate
import re

import sys
#sys.setrecursionlimit(2**31 - 1)

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
  (define z (* 1.0 1.0)) z) 
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

print(test_evaluate("""
  (define (acc a b step func)
      (define (acc-iter n sum)
          (if (> n b) sum
              (acc-iter
                  (+ n step)
                  (+ sum (func n)))))
      (acc-iter a 0))

  (define (PI n)
      (define (term n)
          (/ 1 (* n (+ n 2))))
      (* 8 (acc 1 n 4 term)))

  (PI 20000)
  """))

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

print(test_evaluate("""
(define (recurse n) 
  (if (= n 0) 1
    (* n 
      (recurse (- n 1)))
  )
)

(recurse 5)

""", expected="None|120.0"))


print(test_evaluate("""
((lambda (x) (+ x 1)) 1)

""", expected="2.0"))

print(test_evaluate("""
((lambda () 1))
""", expected="1.0"))

print(test_evaluate("""
(define (not x) (if (= x True) True False))
(define (true? x) (not(not x))) 
(true? True)
""", expected="None|None|True"))

print(test_evaluate("""
(define (asd)1) (define (dsa)(asd)) (dsa) 
""", expected="None|None|1.0"))

print(test_evaluate("""
(define (mycons a b) 
  (lambda (getter) (getter a b)))
(define (mycar x)
  (x (lambda (x y) x)))
(define (mycdr x)
  (x (lambda (x y) y)))
  
(mycar (mycons 1 2))
(mycdr (mycons 1 2))
""", expected="None|None|None|1.0|2.0"))

print(test_evaluate("""
(define def define)
(def lam lambda)

(def eq =)

(def nil null)
(def Tru True)
(def Fal False)

(def (nilp x) (eq x nil))
(def (not x) (if (eq x Fal) Tru Fal))
(def (true? x) (not(not x)))

(def (length xs)
  (if (nilp xs) 0
    (+ (length(cdr xs)) 1)
) )
(def len length)

(def (last xs)
  (if (= (len xs) 1.0)
    (car xs)
    123)
) 

(len (cons 1 null))
(= (len (cons 1 null)) 1.0)
(last (cons 1 null))
"""))

print(test_evaluate("""
(define (plus-a a)
  (if (> a 0)
    (lambda (x) (+ x a))
    (lambda (x) (+ x a))
  ))

(define plus-1 (plus-a 1))
(plus-1 1)
""", expected="None|None|2.0"))

print(test_evaluate("""
(list 1 2 3)
""", expected="(1.0, (2.0, (3.0, null)))"))