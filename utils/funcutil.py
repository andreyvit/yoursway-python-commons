
__all__ = ['non_sig_preserving_decorator']

import functools

def non_sig_preserving_decorator(decorator_wannabe):
  @functools.wraps(decorator_wannabe)
  def decorator_in_law(func):
    @functools.wraps(func)
    def decorated(*args, **kw):
      return decorator_wannabe(func, *args, **kw)
    return decorated
  return decorator_in_law
