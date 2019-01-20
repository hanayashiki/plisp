from plisp.ast import parse
import io
from tests.utils import assert_exception

def test_ast_one(code : str):
  return parse(io.StringIO(code))[0]

def test_ast(code : str):
  print(code)
  return '\n==============\n'.join([ str(x) for x in parse(io.StringIO(code)) ])

print(test_ast_one("(+ 1 1)"))
print(test_ast_one("(1 2 3)"))
print(test_ast_one("(+ (+ 1 1))"))
print(test_ast_one("(+ (+ 1 1)) "))
print(test_ast_one("(+ (+ 1 (1 2 3 4)) 1 2 3)"))
assert_exception(lambda : test_ast_one("(+ (+ 1 (1 2 3 4)) 1 2 3"), ValueError)
print(test_ast_one("(+ (+ 1 (1 2 3 4)) (1 2 3 4    (1 2   )) 2 def        )"))
assert_exception(lambda : test_ast_one("(+ (+ 1 (1 2 3 4) 1 2 3)"), ValueError)
assert_exception(lambda : test_ast_one("(+ (+ 1 (1 2 3 4) 1 2 3)))"), ValueError)
print(test_ast("(define x 1) x"))

print(test_ast("""
(define x "123") x
"""))

print(test_ast("""
(define x "123\\"") x
"""))

print(test_ast("""
(define x "123\\\\") x
"""))

print(test_ast("""
(define x "123\\n") x
"""))

print(test_ast("""
(define (fuck func x y)
  (define (average a b) 
    (/ (+ a b) 2))
  (define mid-val
    (func (average x y)))
  (define avg-val
    (average (func x) (func y)))
  (- avg-val mid-val))
"""))