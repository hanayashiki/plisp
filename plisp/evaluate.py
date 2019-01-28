from plisp import ast
from plisp.entity import Entity, built_in_namespace, UserDefined, UserFunc, If
from typing import *
import plisp.constants as C
import threading

class AtomicSignal():
  def __init__(self, value=""):
    self._value = value
    self._lock = threading.Lock()

  @property
  def lock(self):
    return self._lock

  @property
  def value(self):
    with self._lock:
      return self._value

  @value.setter
  def value(self, v):
    with self._lock:
      self._value = v
      return self._value

class EvalException(ValueError):

  def __init__(self, *args, plisp_trace_back=None, context=None):
    if plisp_trace_back:
      self.plisp_trace_back = plisp_trace_back
    else:
      self.plisp_trace_back = []
    self.context = context
    super().__init__(*args)

  def track_back2str(self):
    def display_stack(x : Entity):
      if isinstance(x, UserDefined):
        return "  line %d, in %s\n    %s" % (x.node.position.row, x, self.context.code.split('\n')[x.node.position.row - 1])
      else:
        return "  %s" % x
    return 'Plisp Traceback: \n' +  '\n'.join([display_stack(x) for x in self.plisp_trace_back])

class TailRecursiveSignal:

  def __init__(self, node : ast.Node):
    self.node = node

class Context:

  def __init__(self, code, signal : AtomicSignal):
    self.code = code
    self.namespace_stack = [built_in_namespace]
    self.stack_trace = []
    self.signal = signal

  def check_signal(self):
    if self.signal.value == "kill":
      self.raise_eval_exception("killed")

  @property
  def current_namespace(self):
    return self.namespace_stack[-1]

  def push_stack_trace(self, e):
    self.stack_trace.append(e)

  def pop_stack_trace(self):
    return self.stack_trace.pop()

  def push_np(self, d=None):
    if d:
      self.namespace_stack.append(d)
    else:
      self.namespace_stack.append({})

  def pop_np(self):
    return self.namespace_stack.pop()

  @staticmethod
  def from_str(atom):
    string = atom.name
    try:
      if atom.str_value:
        return atom.name
      elif string == "True":
        return True
      elif string == "False":
        return False
      else:
        return float(string)
    except:
      return None

  @staticmethod
  def is_literal(atom):
    return Context.from_str(atom) != None

  def lookup(self, atom):
    for np in reversed(self.namespace_stack):
      if atom.name in np:
        return np[atom.name]
    return None

  def evaluate_list(self, node_list : List[ast.Node]):
    return [self.evaluate(node) for node in node_list]

  def raise_eval_exception(self, message):
    e = EvalException(message, plisp_trace_back=self.stack_trace.copy(), context=self)
    raise e

  @staticmethod
  def level_lookup(name, *funcs):
    for func in funcs:
      r = func(name)
      if r is not None:
        return r
    return None

  def atom_lookup(self, atom):
    if atom.str_value:
      return atom.name
    return self.level_lookup(atom, self.lookup, self.from_str)

  def is_tail_recursive(self, operator : Entity):
    if len(self.stack_trace) > 0 and self.stack_trace[-1] is operator:
      return True
    elif len(self.stack_trace) > 1 and isinstance(self.stack_trace[-1], If) and self.stack_trace[-2] is operator:
      return True

    return False

  def evaluate(self, node : ast.Node):
    self.check_signal()

    if isinstance(node, ast.AtomNode):
      lookup = self.atom_lookup(node)
      if lookup is None:
        self.raise_eval_exception("Unknown literal '%s'. " % node)
      return lookup
    elif isinstance(node, ast.ListNode):
      if isinstance(node[0], ast.ListNode):
        operator = self.evaluate(node[0])
      else:
        operator = self.lookup(node[0])
      if operator is None:
        self.raise_eval_exception("Unknown literal '%s'. " % node[0])

        if not isinstance(operator, Entity):
          operator = Entity(operator)

      if self.is_tail_recursive(operator) and isinstance(operator, UserFunc):
        return TailRecursiveSignal(node)
      else:
        try:
          self.push_stack_trace(operator)
          return operator.reduce(self, node)
        finally:
          self.pop_stack_trace()
    else:
      self.raise_eval_exception("Unexpected type: %s of node" % type(node))

  def check_len(self, node, min_len=0, max_len=2**31, exact_len=-1):
    if exact_len != -1:
      if len(node) != exact_len:
        self.raise_eval_exception("%s needs to be exactly %d in length, got %d. " % (node, exact_len, len(node)))
    elif len(node) < min_len or len(node) > max_len:
      self.raise_eval_exception("%s needs to be be between [%d, %d], got %d. " % (node, min_len, max_len, len(node)))

  def define(self, node : ast.ListNode):
    first_node = node[1]
    self.check_len(node, min_len=3)
    if isinstance(first_node, ast.AtomNode):
      entity = self.call(node)
      self.current_namespace[first_node.name] = entity
    elif isinstance(first_node, ast.ListNode):
      #print("defining function%s" % node[1])
      entity = UserFunc(name=node[1][0].name, node=node, captured=self.capture(node), param_list=[x for x in first_node[1:]])
      #print(node[1][0].name + " is defined to be %s" % entity)
      #print("closure of %s is %s" % (node[1][0].name, entity.captured))
      #print(node)
      self.current_namespace[entity.name] = entity

  def lambda_(self, node : ast.ListNode):
    first_node = node[1]
    self.check_len(node, min_len=3)
    if isinstance(first_node, ast.AtomNode):
      self.raise_eval_exception("The second parameter of 'lambda' should be a list. ")
    elif isinstance(first_node, ast.ListNode):
      entity = UserFunc(name="__lambda", node=node, captured=self.capture(node), param_list=[x for x in first_node])
      return entity

  def capture(self, func_node : Union[ast.AtomNode, ast.ListNode], root_bound_names=None):
    captured = {}

    if isinstance(func_node[1], ast.ListNode):
      bound_names = set(map(lambda x : x.name, func_node[1]))
    else:
      bound_names = set()
    if root_bound_names is None:
      root_bound_names = set()
    root_bound_names.update(bound_names)

    #print("root_bound_names: ", root_bound_names)

    def is_free(atom):
      not_bounded = atom.name not in root_bound_names and atom.name not in built_in_namespace
      can_lookup = not (self.atom_lookup(atom) is None)
      if not_bounded and not can_lookup:
        self.raise_eval_exception("%s is used before defined. " % atom)
      return not_bounded and can_lookup and not self.is_literal(atom)

    # node: (define (...) (define ...) (define ...) () )
    for i in range(2, len(func_node)):
      node = func_node[i]
      if isinstance(node, ast.ListNode):
        if isinstance(node[1], ast.AtomNode) and (node[0].name == C.DEFINE or node[0].name == C.LAMBDA):
          root_bound_names.add(node[1].name)
          captured.update(self.capture(node, root_bound_names.copy()))
        elif isinstance(node[1], ast.ListNode) and (node[0].name == C.DEFINE or node[0].name == C.LAMBDA):
          root_bound_names.add(node[1][0].name)
          captured.update(self.capture(node, root_bound_names.copy()))
        else:
          for atom in self.iter_atom(node):
            if is_free(atom):
              captured[atom.name] = self.lookup(atom)
      elif isinstance(node, ast.AtomNode):
        if is_free(node):
          captured[node.name] = self.lookup(node)

    return captured

  @staticmethod
  def iter_atom(list_node : ast.ListNode):
    for node in list_node:
      if isinstance(node, ast.AtomNode):
        yield node
      else:
        for _node in Context.iter_atom(node):
          yield _node

  def call(self, node : ast.ListNode,
           arg_list : ast.ListNode = None,
           param_list : List[ast.AtomNode] = None,
           captured : Dict[str, Any] = None):
    param_namespace = {}
    if arg_list:
      if len(arg_list) - 1 != len(param_list):
        self.raise_eval_exception("Length of arguments and parameters are mismatched for user function %s: %d vs. %d " %
                                  (node[1][0].name, len(arg_list) - 1, len(param_list)))
      for i in range(1, len(arg_list)):
        param_name = param_list[i - 1].name
        value = self.evaluate(arg_list[i])
        param_namespace[param_name] = value
      self.push_np(param_namespace)

    while True:  # For tail-recursive function
      if captured:
        self.push_np(captured.copy())
      else:
        self.push_np()
      try:
        tail_recursive = False
        result = None
        # node: (define (...) (define ...) (define ...) () )
        for i in range(2, len(node)):
          result = self.evaluate(node[i])
          # Search non-define
          if result is not None:
            if isinstance(result, TailRecursiveSignal):
              #print("tail_recursive")
              tail_recursive = True
              arg_list = result.node
              updates = {}
              for i in range(1, len(arg_list)):
                param_name = param_list[i - 1].name
                value = self.evaluate(arg_list[i])
                updates[param_name] = value
              param_namespace.update(updates)
              break
            else:
              return result

        if tail_recursive:
          continue
        self.raise_eval_exception("User function %s should contain one body. " % node[1][0].name) # Not good!
      finally:
        self.pop_np()
        if captured:
          self.pop_np()


  def add_to_namespace(self, name, Entity):
    self.namespace_stack[-1][name] = Entity


def evaluate_list(code, node_list : List[ast.Node], timeout=10):

  signal = AtomicSignal()
  context = Context(code, signal)

  import time

  class MyThread(threading.Thread):
    def __init__(self, func, args=()):
      super(MyThread, self).__init__()
      self.func = func
      self.args = args
      self.exception = None

    def run(self):
      try:
        self.result = self.func(*self.args)
      except Exception as e:
        self.exception = e

    def get_result(self):
      try:
        return self.result
      except Exception:
        return None

  worker = MyThread(func=context.evaluate_list, args=(node_list,))
  worker.start()
  worker.join(timeout)

  if worker.isAlive():
    signal.value = "kill"
    raise EvalException("Evaluation timeout! ")
  else:
    if worker.exception:
      raise worker.exception
    return worker.get_result()