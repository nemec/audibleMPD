#!/usr/bin/env python

import mpd
import threading
import gobject
import subprocess
import console
import input_header

keycode = input_header.input_header()

class scroller:

  def __init__(self, audible, scrolllist, startix = 0):
    self.audible = audible
    self.list = scrolllist
    self.size = len(scrolllist)
    self.ix = startix

  def scroll(self):
    self.audible.say(self.list[self.ix])
    while 1:
      code = self.audible.reader.readkey()
      if code == keycode.KEY_RIGHT:
        return (self.ix, self.list[self.ix])
      elif code == keycode.KEY_LEFT:
        return (self.ix, None)
      elif code == keycode.KEY_UP:
        if self.ix <= 0:
          self.ix = self.size-1
        else:
          self.ix = self.ix - 1
        self.audible.say(self.list[self.ix])
      elif code == keycode.KEY_DOWN:
        if self.ix >= self.size-1:
          self.ix = 0
        else:
          self.ix = self.ix + 1
        self.audible.say(self.list[self.ix])

class IO:
  def __init__(self, inp, outp):
    self._commands = {}
    if not (callable(inp) and callable(outp):
      raise TypeError, "both arguments must be callable"
    self._commands['in']  = inp
    self._commands['out'] = outp

  def __getattr__(self, attr):
    try:
        ret = self._commands[attr]
    except KeyError:
        raise AttributeError("'%s' object has no attribute '%s'" %
                             (self.__class__.__name__, attr))

class audibleMPD:

  def __init__(self, eventpath):
    self.initialize_mpd()
    self.reader = console.reader(eventpath)

    #status = self.client.status()
    #print status
    #print self.client.currentsong()

  def set_volume(self, volume):
    if self.volume > 0:
      self.volume = volume
      self.client.setvol(int(self.volume))

  def h_controls(self, widget, data=None):
    if data == "pause":
      self.client.pause()
    elif data == "next":
      self.client.next()
    elif data == "previous":
      self.client.previous()
    elif data == "volumeup":
      self.set_volume(self.volume+1)
    elif data == "volumedown":
      self.set_volume(self.volume-1)

  def initialize_mpd(self):
    self.client = mpd.MPDClient()
    self.client.connect("tails.local",6600)
    self.client._commands["idle"] = self.client._getlist
    self.client._commands["noidle"] = None

  def say(self, text, volume = -1):
    text = "\"%s\"" % text
    print text
    return#*****************************************************

    if 0 <= volume and volume <= 100: # cut volume by X percent
      oldvolume = int(self.client.status()["volume"])
      self.client.setvol(int(1.0*oldvolume*volume/100))
    else: # pause
      self.client.pause()

    p = subprocess.Popen(['espeak', text], close_fds = True)
    p.communicate()

    if 0 <= volume and volume <= 100: # cut volume by X percent
      self.client.setvol(oldvolume)
    else: # pause
      self.client.pause()

  def doUp(self):
    self.say("Up")

  def doDown(self):
    self.say("Down")
  
  def doLeft(self):
    self.say("Left")

  def doRight(self):
    self.say("Right")

  def prevSong(self):
    self.client.prev()
    cur = self.client.currentsong()
    self.say("%s by %s" % (cur['title'], cur['artist']), 0)

  def nextSong(self):
    self.client.next()
    cur = self.client.currentsong()
    self.say("%s by %s" % (cur['title'], cur['artist']))

  def artistChooser(self):
    lix = 0
    while 1: # Letter loop
      lix, letter = scroller(self, map(chr, range(65, 91)), lix).scroll()
      if not letter:
        break
      aix = 0
      while 1: # Artist loop
        artists = [artist for artist in sorted(self.client.list("artist"))
                  if len(artist) > 0 and artist[0].upper() == letter]
        aix, artist = scroller(self, artists, aix).scroll()
        if not artist:
          break
        six = 0
        while 1:
          songlist = self.client.list("title", "artist", artist)
          six, song = scroller(self, songlist, six).scroll()
          if not song:
            break
          # playsong
    
    

if __name__ == "__main__":

  mpd = audibleMPD("/dev/input/event4")

  while 1:
    code = mpd.reader.readkey()
    print code, keycode.KEY_RIGHT
    if code == keycode.KEY_RIGHT:
      mpd.doRight()
    elif code == keycode.KEY_LEFT:
      mpd.doLeft()
    elif code == keycode.KEY_UP:
      mpd.doUp()
    elif code == keycode.KEY_DOWN:
      mpd.doDown()
    elif code == keycode.KEY_COMMA:
      mpd.prevSong()
    elif code == keycode.KEY_DOT:
      mpd.nextSong()
    elif code == keycode.KEY_P:
      mpd.artistChooser()
