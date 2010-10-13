#!/usr/bin/env python

import mpd
import threading
import gobject
import subprocess

from struct import unpack

class Input:
  KEY_UP    = 103
  KEY_DOWN  = 108
  KEY_LEFT  = 105
  KEY_RIGHT = 106
  KEY_P     = 25
  KEY_COMMA = 51
  KEY_DOT   = 52

class audibleMPD:

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

  def __init__(self):
    self.initialize_mpd()

    #status = self.client.status()
    #print status
    #print self.client.currentsong()

  def say(self, text):
    text = "\"%s\"" % text
    p = subprocess.Popen(['espeak', text], close_fds = True)
    p.communicate()

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
    self.client.pause()
    cur = self.client.currentsong()
    self.say("%s by %s" % (cur['title'], cur['artist']))
    self.client.pause()

  def nextSong(self):
    self.client.next()
    self.client.pause()
    cur = self.client.currentsong()
    self.say("%s by %s" % (cur['title'], cur['artist']))
    self.client.pause()

if __name__ == "__main__":

  mpd = audibleMPD()
  port = open("/dev/input/event4","rb")
  lockcode = 0
  pressed = False

  while 1:
    time,typ,code,val = unpack("4B",port.read(4))
    if not pressed:
      pressed = True
      lockcode = code
      if code == Input.KEY_RIGHT:
        mpd.doRight()
      elif code == Input.KEY_LEFT:
        mpd.doLeft()
      elif code == Input.KEY_UP:
        mpd.doUp()
      elif code == Input.KEY_DOWN:
        mpd.doDown()
      elif code == Input.KEY_COMMA:
        mpd.prevSong()
      elif code == Input.KEY_DOT:
        mpd.nextSong()
      else:
        pressed = False
    elif code == lockcode:
        pressed = False
        lockcode = 0
