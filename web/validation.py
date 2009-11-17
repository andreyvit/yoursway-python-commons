
import re
    
class ValidationErrors(object):
  
  def __init__(self):
    self.messages = {}
    
  def is_valid(self, key=None):
    if key is None:
      return len(self.messages) == 0
    else:
      return not key in self.messages
      
  def invalid(self, key, message):
    self.messages.setdefault(key, message)


class PostbackSession(object):
  
  def __init__(self, request):
    self.errors = ValidationErrors()
    self.request = request
    self.data = {}
    
  def get(self, key):
    value = self.request.get(key)
    self.data[key] = value
    return value
    
  def invalid(self, key, message):
    self.errors.invalid(key, message)
    
  def is_valid(self, key=None):
    return self.errors.is_valid(key)
    
  @property
  def messages(self):
    return self.errors.messages
    
  valid = property(is_valid)


def valid_string(session, key, required=True, use_none=True, min_len=None, max_len=None,
      required_message = "Required.",
      min_len_message = "Please enter at least %(min)d characters.",
      max_len_message = "Cannot be longer that %(max)d characters."):
  value = session.get(key)
  data = dict(value=value, key=key, min=min_len, max=max_len, len=(0 if value==None else len(value)))
  if value != None:
    value = value.strip()
  if value == None or len(value) == 0:
    if required:
      session.invalid(key, required_message % data)
      return value
    else:
      value = None if use_none else ""
  if min_len and len(value) < min_len:
    session.invalid(key, min_len_message % data)
    return value
  if max_len and len(value) > max_len:
    session.invalid(key, max_len_message % data)
    return value
  return value

def valid_int(session, key, required=True, min_value=None, max_value=None,
      required_message = "Required.",
      not_a_number_message = "Must be a number.",
      missing_value=None,
      min_value_message = "Cannot be less than %(minval)d.",
      max_value_message = "Cannot be greater than %(maxval)d."):
  s = valid_string(session, key, required=required, use_none=True, required_message=required_message)
  if s is None:
    return None
  if not session.is_valid(key):
    return s
  if not re.match('^-?[0-9]+$', s):
    import logging
    logging.warn('Not a number: "%s"' % s)
    return session.invalid(key, not_a_number_message)
  i = int(s)
  data = dict(value=i, key=key, min_value=min_value, max_value=max_value)
  if missing_value is not None:
    if ((i in missing_value) if isinstance(missing_value, (list, tuple, set)) else (i == missing_value)):
      if required:
        return session.invalid(key, required_message)
      else:
        return None
  if min_value != None and i < min_value:
    return session.invalid(key, min_value_message % data)
  if max_value != None and i > max_value:
    return session.invalid(key, max_value_message % data)
  return i

def valid_bool(session, key):
  s = session.get(key)
  return s == '1' or s == 'yes' or s == 'on' or s == 'True'
