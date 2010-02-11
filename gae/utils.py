
from google.appengine.api import users

from yoursway.web.handling import can_redirect, access_check, Redirect, AccessDenied

@access_check
def requires_admin(handler):
  if not users.is_current_user_admin():
    raise AccessDenied
