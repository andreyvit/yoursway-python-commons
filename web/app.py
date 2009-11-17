
def load_url_mapping(*components):
  url_mapping = []
  for component in components:
    if isinstance(component, (list, tuple, set)):
      url_mapping += load_url_mapping(*component)
    else:
      module = __import__(component, globals(), locals(), ['url_mapping'], 0)
      url_mapping += getattr(module, 'url_mapping')
  return url_mapping
