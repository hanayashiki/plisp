from typing import *
import io

class CodePos():
  def __init__(self, row, column):
    self.row : int = row
    self.column : int = column

  def __str__(self):
    return str((self.row, self.column))

  def copy(self):
    return CodePos(self.row, self.column)

class Node():
  position : CodePos

  def __init__(self, position : CodePos):
    self.position = position

  def indent_str(self, indent=0):
    return ""


class AtomNode(Node):
  name : str

  def __init__(self, name : str, position : CodePos, str_value=False):
    super().__init__(position)
    self.name = name
    self.str_value = str_value

  def __str__(self):
    return self.indent_str()

  def indent_str(self, indent=0):
    if self.str_value:
      return '"' + self.name + '"'
    else:
      return self.name

class ListNode(Node):
  container : List[Node]

  def __init__(self, container : List[Node], position : CodePos):
    super().__init__(position)
    self.container = container

  def __str__(self):
    return self.indent_str().strip()

  def indent_str(self, indent=0):
    return "\n" +  " "* indent + '(' + ' '.join([x.indent_str(indent+4) for x in self.container]) + ')'

  def __iter__(self):
    return iter(self.container)

  def __len__(self):
    return len(self.container)

  def __getitem__(self, item):
    return self.container[item]


def parse(stream) -> Union[List[ListNode], List[AtomNode], None]:
  cur_pos = CodePos(1, 0)
  current_line = stream.readline()

  def get_char(allow_eof=True) -> Union[str, None]:
    nonlocal current_line, current_char
    if cur_pos.column >= len(current_line):
      current_line = stream.readline()

      if current_line is None or len(current_line) == 0:
        if allow_eof:
          current_char = None
          return None
        raise ValueError("Unexpected EOF at %s. " % get_position())

      cur_pos.row += 1
      cur_pos.column = 0

    c = current_line[cur_pos.column]
    cur_pos.column += 1
    current_char = c
    return c

  def get_position() -> CodePos:
    return cur_pos.copy()

  current_char = get_char()

  def get_current_char() -> str:
    return current_char

  def skip_white_and_get_cur():
    if get_current_char() == ')':
      raise ValueError("Miss matched ')' at %s. " % get_position())
    while get_current_char() is not None and get_current_char().isspace():
      get_char()
    return get_current_char()

  eval_list = []
  while skip_white_and_get_cur() != None:
    parse_res = _parse(get_char, get_position, get_current_char)
    eval_list.append(parse_res)

  return eval_list


def _parse(get_char : Callable[[Optional[bool]], str],
           get_position : Callable[[], CodePos],
           get_cur_char : Callable[[], str]) -> Union[ListNode, AtomNode]:

  c = get_cur_char()
  while c is None or c.isspace():
    c = get_char(False)

  if c == '(':
    return _parse_list(get_char, get_position, get_cur_char)
  else:
    return _parse_atom(get_char, get_position, get_cur_char)

def _parse_list(get_char : Callable[[], str],
                get_position : Callable[[], CodePos],
                get_cur_char : Callable[[], str]) -> ListNode:

  sub_nodes = []
  pos = get_position()
  get_char()

  while True:
    token = _parse(get_char, get_position, get_cur_char)

    if isinstance(token, AtomNode) and len(token.name) > 0:
      sub_nodes.append(token)
    elif isinstance(token, ListNode):
      sub_nodes.append(token)

    while get_cur_char() is not None and get_cur_char().isspace():
      get_char()

    if get_cur_char() == ')':
      get_char()
      break

    if get_cur_char() == None:
      raise ValueError("Unexpected EOF at %s" % get_position())

  return ListNode(sub_nodes, pos)

def _parse_atom(get_char : Callable[[], str],
                get_position : Callable[[], CodePos],
                get_cur_char : Callable[[], str]) -> AtomNode:

  c = get_cur_char()
  token = ""

  if c == "\'" or c == '\"':
    return _parse_str(get_char, get_position, get_cur_char)

  while not c.isspace() and c != '(' and c != ')':
    token += c
    c = get_char()
    if c is None:
      break

  return AtomNode(token, get_position())

def _parse_str(get_char, get_position, get_cur_char) -> AtomNode:

  quote = get_cur_char()

  token = ""

  while True:
    c = get_char(False)
    if c == '\\':
      c = get_char(False)
      if c == quote:
        token += quote
      if c == 'n':
        token += '\n'
      if c == 't':
        token += '\t'
      if c == '\\':
        token += c
      if c == 'r':
        token += '\r'
    elif c == quote:
      get_char()
      break
    else:
      token += c


  return AtomNode(token, get_position(), str_value=True)
