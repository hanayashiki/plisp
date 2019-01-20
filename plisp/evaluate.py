from plisp import ast
from plisp.entity import Entity, built_in_namespace, UserFunc
from typing import *
import plisp.constants as C

class Context:

  def __init__(self):
    self.namespace_stack = [built_in_namespace]

  @property
  def current_namespace(self):
    return self.namespace_stack[-1]

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

  def evaluate(self, node : ast.Node):
    if isinstance(node, ast.AtomNode):
      lookup = self.atom_lookup(node)
      if lookup is None:
        raise ValueError("Unknown literal %s. " % node)
      return lookup
    elif isinstance(node, ast.ListNode):
      if isinstance(node[0], ast.ListNode):
        operator = self.evaluate(node[0])
      else:
        operator = self.lookup(node[0])
      return operator.reduce(self, node)
    else:
      raise ValueError("Unexpected type: %s of node", type(node))

  def check_len(self, node, min_len=0, max_len=2**31, exact_len=-1):
    if exact_len != -1:
      if len(node) != exact_len:
        raise ValueError("%s needs to be exactly %d in length, got %d. " % (node, exact_len, len(node)))
    elif len(node) < min_len or len(node) > max_len:
      raise ValueError("%s needs to be be between [%d, %d], got %d. " % (node, min_len, max_len, len(node)))

  def define(self, node : ast.ListNode):
    first_node = node[1]
    self.check_len(node, min_len=3)
    if isinstance(first_node, ast.AtomNode):
      entity = self.call(node)
      self.current_namespace[first_node.name] = entity
    elif isinstance(first_node, ast.ListNode):
      #print("defining function%s" % node[1])
      entity = UserFunc(name=node[1][0].name, node=node, captured=self.capture(node))
      #print(node[1][0].name + " is defined to be %s" % entity)
      print("closure of %s is %s" % (node[1][0].name, entity.captured))
      self.current_namespace[entity.name] = entity
    else:
      raise ValueError()

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
        raise ValueError("%s is used before defined. " % atom)
      return not_bounded and can_lookup and not self.is_literal(atom)

    # node: (define (...) (define ...) (define ...) () )
    for i in range(2, len(func_node)):
      node = func_node[i]
      if isinstance(node, ast.ListNode):
        if isinstance(node[1], ast.AtomNode) and node[0].name == C.DEFINE:
          root_bound_names.add(node[1].name)
          captured.update(self.capture(node, root_bound_names.copy()))
        elif isinstance(node[1], ast.ListNode) and node[0].name == C.DEFINE:
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

  def call(self, node : ast.ListNode, arg_list : ast.ListNode = None, captured : Dict[str, Any] = None):

    param_namespace = {}
    if arg_list:
      param_list = node[1]
      if len(arg_list) != len(param_list):
        raise ValueError("Length of parameters and arguments are mismatched for user function %s. " % node[1][0].name)
      for i in range(1, len(arg_list)):
        param_name = param_list[i].name
        value = self.evaluate(arg_list[i])
        param_namespace[param_name] = value
      self.push_np(param_namespace)

    if captured:
      self.push_np(captured.copy())
    else:
      self.push_np()
    try:
      # node: (define (...) (define ...) (define ...) () )
      for i in range(2, len(node)):
        result = self.evaluate(node[i])
        # Search non-define
        if result is not None:
          return result
      raise ValueError("User function %s should contain one body. " % node[1][0].name) # Not good!
    finally:
      self.pop_np()
      if arg_list:
        self.pop_np()

  def add_to_namespace(self, name, Entity):
    self.namespace_stack[-1][name] = Entity


def evaluate_list(node_list : List[ast.Node]):
  context = Context()
  return context.evaluate_list(node_list)