from plisp.evaluate import evaluate_list
from plisp.ast import parse
from io import StringIO
from tests.utils import assert_exception
import re

import sys
#sys.setrecursionlimit(2**31 - 1)


def test_evaluate(code : str, expected=None):
  node = parse(StringIO(code))
  r = map(str, evaluate_list(node))
  result = filter(lambda x : x != "None", r)
  result = '\n'.join(list(result))

  if expected and result != expected:


    for i in range(1, len(expected)):
      if expected[:i] != result[:i]:
        print("correct until :\n==================", file=sys.stderr)
        print(result[:i], file=sys.stderr)
        print("==================", file=sys.stderr)

        break
    raise ValueError("Got [\n%s\n] when [\n%s\n] is expected. \nCode: \n=================\n%s\n=================\n" % (result, expected, code))

  return result == expected

quine = \
r"""(define code
    (cons "(define dq (char 34))"
    (cons "(define nl (char 10))"
    (cons "(define (iter prepend append cur acc end)"
    (cons "    (if (= cur null)"
    (cons "        (strcat acc end)"
    (cons "        (iter prepend append (cdr cur) (strcat acc prepend (car cur) append) end)"
    (cons "    )"
    (cons ")"
    (cons "(iter (strcat '    (cons ' dq) (strcat dq nl) code (strcat '(define code' nl) '        null)))))))))))')"
    (cons "(iter '' nl code '' '')"
        null)))))))))))
(define dq (char 34))
(define nl (char 10))
(define (iter prepend append cur acc end)
    (if (= cur null)
        (strcat acc end)
        (iter prepend append (cdr cur) (strcat acc prepend (car cur) append) end)
    )
)
(iter (strcat '    (cons ' dq) (strcat dq nl) code (strcat '(define code' nl) '        null)))))))))))')
(iter '' nl code '' '')
"""

test_evaluate(quine, quine)

quine_cmd = \
r"""!e (define code
    (cons "(define dq (char 34))"
    (cons "(define nl (char 10))"
    (cons "(define (iter prepend append cur acc end)"
    (cons "    (if (= cur null)"
    (cons "        (strcat acc end)"
    (cons "        (iter prepend append (cdr cur) (strcat acc prepend (car cur) append) end)"
    (cons "    )"
    (cons ")"
    (cons "(iter (strcat '    (cons ' dq) (strcat dq nl) code (strcat '!e (define code' nl) '        null)))))))))))')"
    (cons "(iter '' nl code '' '')"
        null)))))))))))
(define dq (char 34))
(define nl (char 10))
(define (iter prepend append cur acc end)
    (if (= cur null)
        (strcat acc end)
        (iter prepend append (cdr cur) (strcat acc prepend (car cur) append) end)
    )
)
(iter (strcat '    (cons ' dq) (strcat dq nl) code (strcat '!e (define code' nl) '        null)))))))))))')
(iter '' nl code '' '')
"""