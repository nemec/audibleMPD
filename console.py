from struct import unpack

#@TODO  Does not queue up keypresses. If you press a second key before you
#       release the first, the second keypress will be lost.

class reader():
  DEFAULT_EVENT_PATH = "/dev/input/event4"

  def __init__(self, eventpath = "/dev/input/event4", keywatches = None):
    self.eventpath = eventpath
    self.watch = keywatches

  def readkeyevent(self):
    port = open(self.eventpath,"rb")
    unpack("26B",port.read(26))
    ret = unpack("2H",port.read(4))
    port.read(16) # This is all 0s in my tests, so ignore it
    return ret

  def readkey(self):
    while True:
      code, val = self.readkeyevent()
      if val > 0:
        lockcode = code
        while True:
          code, val = self.readkeyevent()
          if code == lockcode and val != 1: # returns on key-release or key-hold
            return code

if __name__ == "__main__":
  r = reader()
  while 1:
    print r.readkey()
