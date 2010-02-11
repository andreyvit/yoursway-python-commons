  
def index_by_key(entities):
  return index(lambda e: e.key(), entities)

def group(func, iterable):
    result = {}
    for i in iterable:
        result.setdefault(func(i), []).append(i) 
    return result

def slice(count, iterable):
    result = []
    for i in iterable:
        if len(result) == 0 or len(result[-1]) == count:
            result.append([])
        result[-1].append(i)
    return result
    
def index(func, iterable):
    result = {}
    for i in iterable:
        result[func(i)] = i
    return result
  
def flatten(l, ltypes=(list, tuple)):
  ltype = type(l)
  l = list(l)
  i = 0
  while i < len(l):
    while isinstance(l[i], ltypes):
      if not l[i]:
        l.pop(i)
        i -= 1
        break
      else:
        l[i:i + 1] = l[i]
    i += 1
  return ltype(l)
