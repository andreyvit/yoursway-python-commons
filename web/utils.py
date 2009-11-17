
def escape(html):
    """Returns the given HTML with ampersands, quotes and carets encoded."""
    if not isinstance(html, unicode):
      if not isinstance(html, str):
        html = unicode(html)
      else:
        html = unicode(html, 'utf-8')
    return html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

def js_str(something):
    """Returns a JavaScript string literal representing the given text."""
    if isinstance(something, unicode):
      text = something
    elif isinstance(something, str):
      text = unicode(something, 'utf-8')
    else:
      text = unicode(something)
    return "'" + text.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n") + "'"
