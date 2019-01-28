from plisp.evaluate import evaluate_list
from plisp.ast import parse
from io import StringIO
from plisp.evaluate import EvalException

def assert_exception(func, excp_cls):
  try:
    func()
  except excp_cls:
    return

  raise Exception("Should throw exception %s" % excp_cls)

def print_asserted_expection(code):
  try:
    test_evaluate(code)
  except EvalException as e:
    print(e, e.plisp_trace_back)
    print(e.track_back2str())
    return

  raise Exception("Should throw exception %s" % EvalException)

def test_evaluate(code : str, expected=None):
  node = parse(StringIO(code))
  result = '|'.join(map(str, evaluate_list(code, node)))
  if expected and result != expected:
    raise ValueError("Got [\n%s\n] when [\n%s\n] is expected. \nCode: \n=================\n%s\n=================\n" % (result, expected, code))
  return result