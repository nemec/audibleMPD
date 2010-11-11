#!/usr/bin/env python

import mpd
import threading
import gobject
import subprocess
from sys import exit
from types import MethodType
import console
import input_header

keycode = input_header.input_header()

class scroller:

  def __init__(self, io, scrolllist, startix = 0):
    self.io = io
    self.list = scrolllist
    self.size = len(scrolllist)
    self.ix = startix

  def scroll(self):
    self.io.output(self.list[self.ix])
    while 1:
      code = self.io.input()
      if code == keycode.KEY_ENTER:
        return (-1, self.list[self.ix])
      elif code == keycode.KEY_RIGHT:
        return (self.ix, self.list[self.ix])
      elif code == keycode.KEY_LEFT:
        return (self.ix, None)
      elif code == keycode.KEY_UP:
        if self.ix <= 0:
          self.ix = self.size-1
        else:
          self.ix = self.ix - 1
        self.io.output(self.list[self.ix])
      elif code == keycode.KEY_DOWN:
        if self.ix >= self.size-1:
          self.ix = 0
        else:
          self.ix = self.ix + 1
        self.io.output(self.list[self.ix])

class IO:
  def __init__(self, inp, outp):
    self._commands = {}
    if not (callable(inp) and callable(outp)):
      raise TypeError, "both arguments must be callable"
    setattr(self, 'input', inp)
    setattr(self, 'output', outp)

class audibleMPD:

  def __init__(self, eventpath):
    self.initialize_mpd()
    self.reader = console.reader(eventpath)
    self.speechproc = None

  def initialize_mpd(self):
    self.client = mpd.MPDClient()
    self.client.connect("localhost",6600)
    version = map(lambda x: int(x), self.client.mpd_version.split('.'))
    if (version[0] == 0) and (version[1] < 16):
      print "MPD version must be 0.16.0 or greater,",
      print "currently %s" % self.client.mpd_version
      exit()

  def say(self, text, volume = 80):
    text = "\"%s\"" % text
    print text

    # Cut volume to 'volume' percent of current
    oldvolume = int(self.client.status()["volume"])
    if oldvolume > 0:
      self.client.setvol(int(1.0*oldvolume*volume/100))
    if self.speechproc != None and self.speechproc.poll()==None:
      self.speechproc.kill() # Kill the currently running process, in case we go "next" before it finishes speaking
    self.speechproc = subprocess.Popen(['espeak', text], close_fds = True)
    #p.communicate()  We don't want to block
    
    
    if oldvolume > 0:
      self.client.setvol(oldvolume)

  def play_toggle(self):
    if self.client.status()['state'] == "stop":
      self.client.play()
    else:
      self.client.pause()

  def prevSong(self):
    if self.client.status()['state'] == "stop":
      self.client.play()
    self.client.previous()
    cur = self.client.currentsong()
    self.say("%s by %s" % (cur['title'], cur['artist']), 0)

  def nextSong(self):
    if self.client.status()['state'] == "stop":
      self.client.play()
    self.client.next()
    cur = self.client.currentsong()
    self.say("%s by %s" % (cur['title'], cur['artist']))

  def artistChooser(self):
    io = IO(self.reader.readkey, self.say)
    lix = 0
    while 1: # Letter loop
      lix, letter = scroller(io, map(chr, range(65, 91)), lix).scroll()
      if not letter or lix < 0:
        break
      aix = 0
      while 1: # Artist loop
        artists = [artist for artist in sorted(self.client.list("artist"))
                  if len(artist) > 0 and artist[0].upper() == letter]
        aix, artist = scroller(io, artists, aix).scroll()
        if not artist:
          break
        if aix < 0:
          self.client.findadd("artist", artist)
          return
        six = 0
        while 1: # Song loop
          songlist = sorted(self.client.list("title", "artist", artist))
          six, song = scroller(io, songlist, six).scroll()
          if not song:
            break
          self.client.findadd("artist", artist, "title", song)
          return

  def main(self):
    while 1:
      code = self.reader.readkey()
      if code == keycode.KEY_COMMA:
        self.prevSong()
      elif code == keycode.KEY_DOT:
        self.nextSong()
      elif code == keycode.KEY_P:
        self.artistChooser()
      elif code == keycode.KEY_SLASH:
        self.play_toggle()
    
    

if __name__ == "__main__":

  mpd = audibleMPD("/dev/input/event4")
  mpd.main()
