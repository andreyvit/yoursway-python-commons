
from django import template as templ
from django.utils.safestring import mark_safe

register = templ.Library()

@register.tag(name='field')
def parse_field_tag(parser, token):
  bits = token.contents.split()
  
  tag_name  = bits.pop(0)
  expr      = bits.pop(0)
  cell_name = (bits.pop(0) if len(bits) > 0 else None)
  
  if '.' not in expr: expr = 'form.' + expr
  form_expr, field_name = expr.rsplit('.', 1)
  form_expr = parser.compile_filter(form_expr)
  
  import logging
  params = []
  try:
    logging.info("parsing " + token.contents)
    while parser.tokens:
      token = parser.next_token()
      logging.info(repr(token.__dict__))
      bits = token.contents.split(None, 2)
      
      if token.token_type == 0 and len(bits) == 0:
        pass
      elif token.token_type == 2 and bits[0] == 'param':
        _        = bits.pop(0)
        var_name = bits.pop(0)
        
        if len(bits) > 0:
          value, value_nodelist = bits.pop(0), None
        else:
          value, value_nodelist = None, parser.parse(('endparam',))
          parser.delete_first_token()
        
        params.append((var_name, value, value_nodelist))
      else:
        parser.prepend_token(token)
        break
    
  except Exception, e:
    import logging
    logging.error(str(e))

  if cell_name == '': cell_name = None
  
  return PythonFieldNode(form_expr, field_name, cell_name, params)

class PythonFieldNode(templ.Node):
  def __init__(self, form_expr, field_name, cell_name, params):
    self.form_expr  = form_expr
    self.field_name = field_name
    self.cell_name  = cell_name
    self.params     = params

  def render(self, context):
    form  = self.form_expr.resolve(context)
    field = getattr(form, self.field_name + '_field')

    name = field.name
    error = (form.session.messages.get(field.name) if form.session else None)
    
    context.push()
    try:
      param_values = {}
      for var_name, value, value_nodelist in self.params:
        if value_nodelist:
          value = value_nodelist.render(context)
        context[var_name] = mark_safe(value)
        param_values[var_name] = value
        
      rendered = mark_safe(field.render(form, param_values))
    
      if self.cell_name:
        cell = context.get('%s_cell' % self.cell_name)
        if cell is None:
          return "(! cell %s is missing !)" % self.cell_name
        else:
          context.push()
          context['f'] = name
          context['v'] = rendered
          context['ec'] = ('error' if error else '')
          context['e'] = (error or '')
          result = cell.render_cell(context)
          context.pop()
          return result
      else:
        return rendered
    finally:
      context.pop()

@register.tag(name='defcell')
def parse_defcell_tag(parser, token):
  bits = token.contents.split()
  if len(bits) != 2:
    raise TemplateSyntaxError, "'%s' tag takes only one argument" % bits[0]
  cell_name = bits[1]
  nodelist = parser.parse(('endcell', 'endcell %s' % cell_name))
  parser.delete_first_token()
  return CellNode(cell_name, nodelist)

class CellNode(templ.Node):
  def __init__(self, cell_name, nodelist):
    self.cell_name = cell_name
    self.nodelist  = nodelist

  def render(self, context):
    context['%s_cell' % self.cell_name] = self
    return u''
    
  def render_cell(self, context):
    return self.nodelist.render(context)

@register.tag(name='default')
def parse_default_tag(parser, token):
  bits = token.contents.split()
  if len(bits) != 2:
    raise TemplateSyntaxError, "'%s' tag takes only one argument" % bits[0]
  var_name = bits[1]
  nodelist = parser.parse(('enddefault',))
  parser.delete_first_token()
  return DefaultNode(var_name, nodelist)

class DefaultNode(templ.Node):
  def __init__(self, var_name, nodelist):
    self.var_name = var_name
    self.nodelist = nodelist

  def render(self, context):
    if context.get(self.var_name, None) is None:
      context[self.var_name] = self.nodelist.render(context)
    return u''
