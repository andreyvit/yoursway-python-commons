import string
from random import Random

def random_string(len = 12, chars = string.letters+string.digits):
  return ''.join(Random().sample(chars, 12))
