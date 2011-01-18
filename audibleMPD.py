#!/usr/bin/env python

import mpd
import threading
import gobject
import subprocess as sp
import re
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

  def volumedown(self):
    self.client.setvol(int(self.client.status()["volume"])-5)    

  def volumeup(self):
    self.client.setvol(int(self.client.status()["volume"])+5)

  def say(self, text, volume = 0):
    text = re.sub("'", "", "\"%s\"" % text)
    print text

    if volume != 0:
      # Cut volume to 'volume' percent of current
      oldvolume = int(self.client.status()["volume"])
      if oldvolume > 0:
        self.client.setvol(int(1.0*oldvolume*volume/100))
    if self.speechproc != None and self.speechproc.poll()==None:
      self.speechproc.kill() # Kill the currently running process, in case we go "next" before it finishes speaking
    cmd = ('/opt/swift/bin/swift "'+text+'" -o say.wav && sox -V1 say.wav'
          ' -t wav speech.wav trim 8 && aplay speech.wav;')
    self.speechproc = sp.Popen(cmd, close_fds = True, stdout = sp.PIPE, stderr = sp.PIPE, shell=True)
    if volume != 0:
      p.communicate()  # block until finished speaking
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
      if code == keycode.KEY_PREVIOUSSONG:
        self.prevSong()
      elif code == keycode.KEY_NEXTSONG:
        self.nextSong()
      elif code == keycode.BTN_RIGHT:
        self.artistChooser()
      elif code == keycode.KEY_PLAYPAUSE:
        self.play_toggle()
      elif code == keycode.KEY_VOLUMEUP:
        self.volumeup()
      elif code == keycode.KEY_VOLUMEDOWN:
        self.volumedown()
    

if __name__ == "__main__":

  mpd = audibleMPD("/dev/input/event3")
  mpd.main()
