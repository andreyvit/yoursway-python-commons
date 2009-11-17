
from yoursway.web.utils import escape
from yoursway.web.validation import PostbackSession, valid_string, valid_int

from django.utils.safestring import mark_safe
from datetime import date

class Field(object):
  
  instance_counter = 0  # incremented on each creation to establish ordering of fields inside a class
  
  def __new__(self, *args, **kw):
    result = object.__new__(self, *args, **kw)
    result.instance_index = Field.instance_counter
    Field.instance_counter += 1
    return result
  
  def set_name(self, name):
    self.name = name
    self.derive_names()

  def derive_names(self):
    pass # override point
    
  def initialize(self, form):
    value = (self.default_value() if hasattr(self.default_value, '__call__') else self.default_value)
    setattr(form, self.name, value)
  
  def load(self, form, model):
    setattr(form, self.name, getattr(model, self.name))
  
  def save(self, form, model):
    setattr(model, self.name, getattr(form, self.name))

import logging
class FormMeta(type):
  def __new__(cls, name, bases, dct):
    new_dict = {}
    fields = []
    for k, v in dct.iteritems():
      if isinstance(v, Field):
        if hasattr(v, 'depends_on_fields'):
          for f in v.depends_on_fields:
            if f not in fields:
              fields.append(f)
        if v not in fields:
          fields.append(v)
        v.set_name(k)
        new_dict[k+'_field'] = v
      new_dict[k] = v
      
    fields.sort(lambda a, b: a.instance_index - b.instance_index)
      
    new_dict['fields'] = fields
    
    return type.__new__(cls, name, bases, new_dict)
    
  def __init__(cls, name, bases, dct):
    super(FormMeta, cls).__init__(name, bases, dct)

class Form:
  __metaclass__ = FormMeta
  
  def __init__(self):
    self.session = None
    for field in self.fields:
      field.initialize(self)
  
  def postback(self, handler):
    self.session = PostbackSession(handler.request)
    for field in self.fields:
      field.postback(self, self.session)
    return self.session
    
  @property
  def valid(self):
    return self.session.is_valid()
    
  def first_invalid(self):
    for field in self.fields:
      if not self.session.is_valid(field.name):
        return (field.name, self.session.messages[field.name])
    return self.session.messages.items()[0]
    
  def load(self, model):
    for field in self.fields:
      field.load(self, model)
    
  def save(self, model):
    for field in self.fields:
      field.save(self, model)

def render_tag(tag, content=None, **attrs):
  text = '<' + tag
  for k, v in attrs.iteritems():
    if k == 'klass': k = 'class'
    if v is None:  continue
    if v is False: continue
    if v is True:  v = k
    if isinstance(v, (list, tuple)):
      v = " ".join(filter(lambda x: x is not None, v))  # useful for CSS classes or styles
    text = text + ' ' + k + '="' + escape(v) + '"'
  if content or tag == 'textarea':
    if isinstance(content, (list, tuple)):
      content = "".join(content)
    return text + '>' + content + '</' + tag + '>'
  else:
    return text + ' />'

def render_option(name, value, current_value):
  return render_tag('option', escape(unicode(name)), value=value, selected=(value == current_value))

def render_select(options, value=None, name=None, **attrs):
  options = map(lambda option: (option if isinstance(option, dict) else dict(name=option, value=option)), options)
  rendered_options = map(lambda option: render_option(current_value=value, **option), options)
  return render_tag('select', rendered_options, id=name, name=name, **attrs)
  
class StringField(Field):
  
  def __init__(self, default_value='', required=True, klass=None, attrs={},
        use_none=True, min_len=None, max_len=None,
        required_message = "Required.",
        min_len_message = "Please enter at least %(min)d characters.",
        max_len_message = "Cannot be longer that %(max)d characters.",
        placeholder=None, style=None):
    self.default_value = default_value
    self.required = required
    self.attrs = {}
    self.klass = klass
    self.use_none = use_none
    self.min_len = min_len
    self.max_len = max_len
    self.min_len_message = min_len_message
    self.max_len_message = max_len_message
    self.required_message = required_message
    self.attrs['placeholder'] = placeholder
    self.attrs['style'] = style
    
  def render(self, form, params):
    value = getattr(form, self.name, None) or ''
    return render_tag('input', id=self.name, name=self.name, type='text', klass=[self.klass, params.get('klass')], value=value, **self.attrs)
    
  def postback(self, form, session):
     setattr(form, self.name, valid_string(session, self.name, required=self.required, use_none=self.use_none,
      min_len=self.min_len, max_len=self.max_len,
      min_len_message=self.min_len_message, max_len_message=self.max_len_message,
      required_message=self.required_message))
  
class TextField(Field):
  
  def __init__(self, default_value='', required=True, klass=None, attrs={},
        use_none=True, min_len=None, max_len=None,
        required_message = "Required.",
        min_len_message = "Please enter at least %(min)d characters.",
        max_len_message = "Cannot be longer that %(max)d characters.",
        placeholder=None, style=None, rows=3):
    self.default_value = default_value
    self.required = required
    self.attrs = {}
    self.klass = klass
    self.use_none = use_none
    self.min_len = min_len
    self.max_len = max_len
    self.min_len_message = min_len_message
    self.max_len_message = max_len_message
    self.required_message = required_message
    self.attrs['placeholder'] = placeholder
    self.attrs['style'] = style
    self.rows = rows
    
  def render(self, form, params):
    value = getattr(form, self.name, None) or ''
    return render_tag('textarea', value, id=self.name, name=self.name, type='text', klass=[self.klass, params.get('klass')], rows=self.rows, **self.attrs)
    
  def postback(self, form, session):
     setattr(form, self.name, valid_string(session, self.name, required=self.required, use_none=self.use_none,
      min_len=self.min_len, max_len=self.max_len,
      min_len_message=self.min_len_message, max_len_message=self.max_len_message,
      required_message=self.required_message))

class DateField(Field):
  
  MONTH_FULL = '%B'
  MONTH_ABBREV = '%b'
  MONTH_ORDINAL_AND_FULL = '%m - %B'
  
  def __init__(self, default_value=(lambda: date.today()), reference_date=None, past=True, future=True, past_years=10, future_years=10,
               order=('month', 'day', 'year'), month_format='%B', day_with_zeros=True,
               no_such_day_message='No such day in %B %Y', klass=None):
    self.default_value = default_value
    self.past = past
    self.future = future
    self.past_years = past_years
    self.future_years = future_years
    self.order = order
    self.month_format = month_format
    self.day_format = ('%02d' if day_with_zeros else '%d')
    self.reference_date = (reference_date or date.today())
    self.no_such_day_message = no_such_day_message
    self.klass = klass
    
    self.min_year = (self.reference_date.year-self.past_years if self.past else self.reference_date.year)
    self.max_year = (self.reference_date.year+self.future_years if self.future else self.reference_date.year)
  
  def derive_names(self):
    self.year_name, self.month_name, self.day_name = self.name+'_year', self.name+'_month', self.name+'_day'
  
  def render(self, form, params):
    value = getattr(form, self.name)
    
    years  = range(self.min_year, self.max_year+1)
    months = (dict(value=m, name=date(2000, m, 1).strftime(self.month_format)) for m in range(1,13))
    days   = (dict(value=d, name=self.day_format % d) for d in range(1,32))
    
    year, month, day = ((value.year,value.month,value.day) if value else (-1,-1,-1))
    year_select  = render_select(years,  name=self.year_name,  value=year,  klass=[self.klass, 'year-select', params.get('klass')])
    month_select = render_select(months, name=self.month_name, value=month, klass=[self.klass, 'month-select', params.get('klass')])
    day_select   = render_select(days,   name=self.day_name,   value=day,   klass=[self.klass, 'day-select', params.get('klass')])
    
    components = dict(year=year_select, month=month_select, day=day_select)
    ordered = map(lambda c: components[c], self.order)
    return "".join(ordered)
    
  def postback(self, form, session):
    year  = valid_int(session, self.year_name,  min_value=self.min_year, max_value=self.max_year, missing_value=-1)
    month = valid_int(session, self.month_name, min_value=1, max_value=12, missing_value=-1)
    day   = valid_int(session, self.day_name,   min_value=1, max_value=31, missing_value=-1)
    if year is None or month is None or day is None:
      value = None
    else:
      try:
        value = date(year, month, day)
      except ValueError:
        session.invalid(self.day_name, date(year, month, 1).strftime(no_such_day_message))
        value = None
    setattr(form, self.name, value)
  
