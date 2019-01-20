def assert_exception(func, excp_cls):
  try:
    func()
  except excp_cls:
    return

  raise Exception("Should throw exception %s" % excp_cls)