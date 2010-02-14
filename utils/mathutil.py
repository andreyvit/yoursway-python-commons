  
def between(value, start, end):
  return value >= start and value <= end

def signum(int):
  if(int < 0): return -1
  elif(int > 0): return 1
  else: return 0
