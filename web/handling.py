
__all__ = ('fetcher', 'provider', 'StopRequest', 'YSHandler', 'can_redirect')

import functools
import re
import logging
from decorator import decorator
from yoursway.utils.funcutil import non_sig_preserving_decorator

def fetcher(fetch_func):
  """ Decorates a two-argument function: func(self, path_element). """
  @functools.wraps(fetch_func)
  @non_sig_preserving_decorator
  def fetch_decorator(func, self, *args):
    if hasattr(args[0], '__call__'):
      # support for dispatch_request method
      arg, args = args[1], args[0:1] + args[2:]
    else:
      arg, args = args[0], args[1:]
    fetch_func(self, arg)
    return func(self, *args)
  fetch_decorator._autodecorate_request = True
  return fetch_decorator

def before_request(fetch_func):
  """ Decorates a one-argument function: func(self). """
  @functools.wraps(fetch_func)
  @non_sig_preserving_decorator
  def fetch_decorator(func, self, *args):
    fetch_func(self)
    return func(self, *args)
  fetch_decorator._autodecorate_request = True
  return fetch_decorator
  
def access_check(check_func):
  """ Decorates a one-argument function: func(handler). """
  @functools.wraps(check_func)
  @non_sig_preserving_decorator
  def check_decorator(func, handler, *args, **kw):
    try:
      check_func(handler)
    except AccessDenied, e:
      from google.appengine.api import users
      if users.get_current_user() is None and can_redirect(handler.request):
        raise Redirect(users.create_login_url(handler.request.uri))
      else:
        raise e
    return func(handler, *args, **kw)
  check_decorator._autodecorate_request = True
  return check_decorator

class StopRequest(Exception):
  pass
  
class NotFound(Exception):
  pass
  
class AccessDenied(Exception):
  pass
  
class BadRequest(Exception):
  pass
  
class Redirect(Exception):
  
  def __init__(self, location):
    self.location = location
  
@decorator
def with_stop_request_support(func, handler, *args, **kw):
  try:
    func(handler, *args, **kw)
  except Redirect, redirect:
    handler.redirect(redirect.location)
  except StopRequest:
    pass
  
@decorator
def with_request_decoration_support(func, self, *args, **kw):
  self.dispatch_request(func, *args, **kw)
  
class YSHandlerMetaclass(type):
  def __new__(cls, name, bases, dct):
    # wrap GET, POST, HEAD methods
    for k in ('get', 'post', 'head'):
      if k in dct:
        dct[k] = with_stop_request_support(with_request_decoration_support(dct[k]))

    # decorators = (dec1, dec2) support
    decorators = list(dct.get('decorators', []))
    
    # @before_request method support
    for k, v in dct.iteritems():
      if v is not None and hasattr(v, '_autodecorate_request'):
        decorators.append(v)
        
    # apply decorators to overloaded dispatch_request
    dispatch_request = dct.get('dispatch_request')
    if dispatch_request is None:
      def dispatch_request(self, func, *args, **kw):
        super(getattr(self.__class__, '_%s_klass' % name), self).dispatch_request(func, *args, **kw)
    for dec in reversed(decorators):
      dispatch_request = dec(dispatch_request)
    dct['dispatch_request'] = dispatch_request
      
    klass = type.__new__(cls, name, bases, dct)
    setattr(klass, '_%s_klass' % name, klass)
    return klass
    
CAMELCASE_BOUNDARY_RE = re.compile('([a-z0-9])([A-Z])')
EXCLUDED_EXCEPTION_CLASSES = set((Exception, BaseException, object))

CONTENT_TYPES = (
  ('html', lambda req: True),
)

def recognize_format(request):
  for format, tester in CONTENT_TYPES:
    if tester(request):
      return format
      
def can_redirect(request):
  return request.method == 'GET' and recognize_format(request) == 'html'

class YSHandler(object):
  __metaclass__ = YSHandlerMetaclass
  
  def dispatch_request(self, func, *args, **kw):
    func(self, *args, **kw)
    
  def switch_on_format(self, func_name_prefix, *args, **kw):
    format = recognize_format(self.request)
    func = getattr(self, func_name_prefix + '_' + format, None)
    if func is None:
      raise BadRequest, "Output in %s format is not supported" % format
    func(*args, **kw)
    
    
  ########################
  #  Exception Handling  #
  ########################
    
  def handle_not_found(self, exception, debug_mode):
    self.render_not_found_error(exception, debug_mode)
    
  def render_not_found_error(self, exception, debug_mode):
    self.error(404)
    self.switch_on_format('render_not_found_error', exception, debug_mode)
    
  def render_not_found_error_html(self, exception, debug_mode):
    self.response.out.write("Page not found.")
    
  def render_not_found_error_ajaxhtml(self, exception, debug_mode):
    self.response.out.write("Page not found.")
    
  def render_not_found_error_json(self, exception, debug_mode):
    pass
    
  def render_not_found_error_xml(self, exception, debug_mode):
    pass
    
    
  def handle_access_denied(self, exception, debug_mode):
    self.render_access_denied_error(exception, debug_mode)
    
  def render_access_denied_error(self, exception, debug_mode):
    self.error(403)
    self.switch_on_format('render_access_denied_error', exception, debug_mode)

  def render_access_denied_error_html(self, exception, debug_mode):
    self.response.out.write("Access denied.")

  def render_access_denied_error_ajaxhtml(self, exception, debug_mode):
    self.response.out.write("Access denied.")

  def render_access_denied_error_json(self, exception, debug_mode):
    pass

  def render_access_denied_error_xml(self, exception, debug_mode):
    pass
    
    
  def handle_bad_request(self, exception, debug_mode):
    self.render_bad_request_error(exception, debug_mode)
    
  def render_bad_request_error(self, exception, debug_mode):
    self.error(400)
    self.switch_on_format('render_bad_request_error', exception, debug_mode)

  def render_bad_request_error_html(self, exception, debug_mode):
    self.response.out.write("Bad request.")

  def render_bad_request_error_ajaxhtml(self, exception, debug_mode):
    self.response.out.write("Bad request.")

  def render_bad_request_error_json(self, exception, debug_mode):
    pass

  def render_bad_request_error_xml(self, exception, debug_mode):
    pass
    
    
  def handle_unknown_exception(self, exception, debug_mode):
    self.render_unknown_exception_error(exception, debug_mode)

  def render_unknown_exception_error(self, exception, debug_mode):
    self.error(500)
    self.switch_on_format('render_unknown_exception_error', exception, debug_mode)

  def render_unknown_exception_error_html(self, exception, debug_mode):
    self.response.out.write("Internal server error.")

  def render_unknown_exception_error_ajaxhtml(self, exception, debug_mode):
    self.response.out.write("Internal server error.")

  def render_unknown_exception_error_json(self, exception, debug_mode):
    pass

  def render_unknown_exception_error_xml(self, exception, debug_mode):
    pass
    
    
  @with_stop_request_support
  def dispatch_exception(self, exception, debug_mode):
    for klass in exception.__class__.__mro__:
      if klass not in EXCLUDED_EXCEPTION_CLASSES:
        method_name = 'handle_' + CAMELCASE_BOUNDARY_RE.sub('\\1_\\2', klass.__name__).lower()
        if hasattr(self, method_name):
          getattr(self, method_name)(exception, debug_mode)
          return
    self.handle_unknown_exception(exception, debug_mode)
  
  def handle_exception(self, exception, debug_mode):
    self.dispatch_exception(exception, debug_mode)
    logging.exception("Error processing request because of %s: %s", exception.__class__.__name__, str(exception) )
