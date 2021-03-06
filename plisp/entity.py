from typing import *
import re
from plisp.ast import ListNode, AtomNode, Node
import plisp.constants as C

built_in_namespace = {}

class Entity:

  def __init__(self, value=None):
    self.value = value

  def reduce(self, context, _list : ListNode):
    context.raise_eval_exception("%r of %s does not have method %r" % (self.value, type(self), "reduce"))

  def __repr__(self):
    return str(self)

def built_in(name : str, *args, **kwargs):
  def cls_wrapper(cls : type):
    global built_in_namespace
    built_in_namespace[name] = cls(*args, **kwargs)
    cls.op_name = name
    return cls
  return cls_wrapper

@built_in("null")
class Null(Entity):

  def __str__(self):
    return "null"

class Operator(Entity):
  op_name = ""

  def __str__(self):
    return "<Operator %r>" % self.op_name

class Scannable(Operator):

  @staticmethod
  def is_reversed():
    return False

  @staticmethod
  def step(s, new):
    raise NotImplementedError()

  @staticmethod
  def begin():
    raise NotImplementedError()

  @staticmethod
  def type_check(type):
    raise NotImplementedError()

  def reduce(self, context, _list : ListNode):
    s = self.begin()

    if self.is_reversed():
      _list = reversed(_list.container[1:])
    else:
      _list = _list.container[1:]

    for node in _list:
      value = context.evaluate(node)
      if not self.type_check(type(value)):
        context.raise_eval_exception("Operator %s got an unexpected type: %s:%s" % (self.op_name, node, type(value)))
      s = self.step(s, value)
    return s

class BinaryOp(Operator):

  @staticmethod
  def step(left, right):
    raise NotImplementedError()

  @staticmethod
  def type_check(lt, rt):
    raise NotImplementedError()

  def reduce(self, context, _list : ListNode):
    if len(_list) != 3:
      context.raise_eval_exception("Operator %s needs exactly 2 parameters. " % self.op_name)
    left = context.evaluate(_list[1])
    right = context.evaluate(_list[2])
    if not self.type_check(type(left), type(right)):
      context.raise_eval_exception("Operator %s got unexpected types: %s, %s" % (self.op_name, type(left), type(right)))
    return self.step(left, right)

class UnaryOp(Operator):

  @staticmethod
  def step(val):
    raise NotImplementedError()

  @staticmethod
  def type_check(val_type):
    raise NotImplementedError()

  def reduce(self, context, _list : ListNode):
    if len(_list) != 2:
      context.raise_eval_exception("Operator %s needs exactly 1 parameters. " % self.op_name)
    val = context.evaluate(_list[1])
    if not self.type_check(type(val)):
      context.raise_eval_exception("Operator %s got an unexpected type: %s" % (self.op_name, type(val)))
    return self.step(val)

@built_in("+")
class Add(Scannable):

  @staticmethod
  def type_check(t):
    return t == int or t == float

  @staticmethod
  def step(s, new):
    return s + new

  @staticmethod
  def begin():
    return 0


@built_in("*")
class Multiply(Scannable):

  @staticmethod
  def type_check(t):
    return t == int or t == float

  @staticmethod
  def step(s, new):
    return s * new

  @staticmethod
  def begin():
    return 1

@built_in("-")
class Substract(BinaryOp):

  @staticmethod
  def type_check(t1, t2):
    return (t1 == int or t1 == float) and (t2 == int or t2 == float)

  @staticmethod
  def step(left, right):
    return left - right

@built_in("/")
class Divide(BinaryOp):

  @staticmethod
  def type_check(t1, t2):
    return (t1 == int or t1 == float) and (t2 == int or t2 == float)

  @staticmethod
  def step(left, right):
    return left / right

@built_in("=")
class Equal(BinaryOp):

  @staticmethod
  def type_check(t1, t2):
    return ((t1 == int or t1 == float) and (t2 == int or t2 == float)) or (t1 == str and t2 == str) or (t1 == Null or t2 == Null) or (t1 == bool and t2 == bool)

  @staticmethod
  def step(left, right):
    print("left:", left)
    print("right:", right)
    return left == right

@built_in("<")
class Less(BinaryOp):

  @staticmethod
  def type_check(t1, t2):
    return ((t1 == int or t1 == float) and (t2 == int or t2 == float)) or (t1 == str and t2 == str)

  @staticmethod
  def step(left, right):
    return left < right

@built_in(">")
class Greater(BinaryOp):

  @staticmethod
  def type_check(t1, t2):
    return ((t1 == int or t1 == float) and (t2 == int or t2 == float)) or (t1 == str and t2 == str)

  @staticmethod
  def step(left, right):
    return left > right

@built_in("expt")
class Exponential(BinaryOp):

  @staticmethod
  def type_check(t1, t2):
    return (t1 == int or t1 == float) and (t2 == int or t2 == float)

  @staticmethod
  def step(left, right):
    return left ** right

@built_in(C.DEFINE)
class Define(Operator):
  def reduce(self, context, _list : ListNode):
    context.define(_list)
    return None

@built_in(C.LAMBDA)
class Lambda(Operator):
  def reduce(self, context, _list : ListNode):
    return context.lambda_(_list)

class UserDefined(Entity):

  def __init__(self, name, node : Node, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.name = name
    self.node = node

class UserAtom(UserDefined):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def __str__(self):
    return "<UserAtom %r at %x>" % (self.name, id(self))


class UserFunc(UserDefined, Operator):

  def __init__(self, captured : Dict[str, Entity], param_list : List, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.captured = captured
    self.param_list = param_list

  def reduce(self, context, _list : ListNode):
    return context.call(self.node, arg_list=_list, param_list=self.params, captured=self.captured)

  def __str__(self):
    return "<UserFunc %r at %x>" % (self.name, id(self))

  @property
  def params(self):
    return self.param_list


@built_in(C.IF)
class If(Operator):
  def reduce(self, context, _list : ListNode):
    """
    (if predicate
      consequent
      alternative)
    """
    if len(_list) != 4:
      context.raise_eval_exception("Operator %s needs exactly 3 parameters. " % self.op_name)

    predicate = context.evaluate(_list[1])
    if predicate not in [True, False]:
      context.raise_eval_exception("%s should be of type bool, got %s" % (_list[1], type(predicate)))

    if predicate:
      return context.evaluate(_list[2])
    else:
      return context.evaluate(_list[3])

@built_in("cons")
class Cons(BinaryOp):
  @staticmethod
  def type_check(t1, t2):
    return True

  @staticmethod
  def step(left, right):
    return (left, right)

@built_in("car")
class Car(UnaryOp):
  @staticmethod
  def type_check(t):
    return t == tuple

  @staticmethod
  def step(val):
    return val[0]

@built_in("cdr")
class Cdr(UnaryOp):
  @staticmethod
  def type_check(t):
    return t == tuple

  @staticmethod
  def step(val):
    return val[1]

@built_in("strcat")
class Strcat(Scannable):

  @staticmethod
  def type_check(t):
    return t == str

  @staticmethod
  def step(s, new):
    return s + new

  @staticmethod
  def begin():
    return ""

@built_in("char")
class Char(UnaryOp):
  @staticmethod
  def type_check(t):
    return (t == int) or (t == float)

  @staticmethod
  def step(val):
    return str(chr(int(val)))

@built_in("list")
class List(Scannable):

  @staticmethod
  def is_reversed():
    return True

  @staticmethod
  def type_check(t):
    return True

  @staticmethod
  def step(s, new):
    return (new, s)

  @staticmethod
  def begin():
    return Null()