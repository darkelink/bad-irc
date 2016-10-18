#!/usr/bin/env python

import sys, os, datetime
from ex3utils import Client
from threading import Thread



# give default value to global vars
server = "localhost"
port = 6667
screenName = ""
channels = {}

# create a new channel on the filesystem and start listening for messages
def makeChannel(name):
  if not name in channels:
    channels[name] = Channel(name)
    channels[name].start()
    

class Channel(Thread):
  def __init__(self, name):
    Thread.__init__(self)
    self.name = name
    self.fpath = path + name
    if name != "":
      self.fpath += "/"
    if not os.path.isdir(self.fpath):
      os.makedirs(self.fpath)
    if not os.path.exists(self.fpath + "in"):
      os.mkfifo(self.fpath + "in")
    self.outfile = open(self.fpath + "out", 'a', 0)

  def run(self):
    self.running = True
    while self.running:
      # this will block until there is data
      self.infile = open(self.fpath + "in", 'r')
      for line in self.infile:
        if line[0] == '/':
          if line[1] == 'j':
            nchannel = line[3:].strip(' \t\n\r')
            client.send("JOIN " + nchannel)
          elif line[1] == 'p':
            client.send("PART " + self.name)
          elif line[1] == 'n':
            client.send("NICK " + line[3:].strip(' \t\n\r'))
          elif line[1] == 'l':
            client.send("LIST")
          elif line[1] == 'q':
            client.send("QUIT")
            for c in channels:
              channels[c].running = False
              # stop trying to read from pipes somehow
            root.running = False
            client.stop()
        else:
          # assume everything else is a normal message
          client.send("PRIVMSG %s :%s" % (self.name, line))
          client.printMessage(self.name, screenName, line.strip('\n\r'))
      self.infile.close()
    # delete input when done
    os.unlink(self.fpath + "in")


class IRCClient(Client):
  # print the message to file
  def printMessage(self, channel, sender, message):
    # make sure the channel exists
    makeChannel(channel)
    print >> channels[channel].outfile, "%s <%s> %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), sender, message)

  # for printing anything that isn't a normal message
  def printNotice(self, channel, message):
    makeChannel(channel)
    print >> channels[channel].outfile, "%s -!- %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), message)

  def onMessage(self, socket, message):
    global screenName
    mess = message.split(' ')
    if mess[1] == "PRIVMSG":
      proc = message.split(':', 2)
      if mess[2][0] == '#':
        self.printMessage(mess[2], mess[0][1:].split('!', 1)[0], proc[-1])
      else:
        self.printMessage(mess[0][1:].split('!', 1)[0], mess[2], proc[-1])
    elif mess[1] == "JOIN":
      channel = mess[2][1:].strip(' \t\n\r')
      makeChannel(channel)
      self.printNotice(channel, "%s has joined %s" % (mess[0][1:], channel))
    elif mess[1] == "PART":
      channel = mess[2].strip(' \t\n\r')
      if mess[0][1:] == screenName:
        channels[channel].running = False
      self.printNotice(channel, "%s has left %s" % (mess[0][1:], channel))
    elif mess[1] == "NICK":
      if mess[0][1:] == screenName:
        screenName = mess[2][1:]
      else:
        self.printNotice("", "%s in now know as %s" % (mess[0][1:], mess[2][1:]))
    elif mess[0] == "PING":
        client.send("PONG " + mess[1])
    else:
      # anything we don't recognise goes to root
      print >> root.outfile, message
    return True


server = sys.argv[1]
if len(sys.argv) == 4:
  port = int(sys.argv[2])
  screenName = sys.argv[3]
else:
  screenName = sys.argv[2]
path = "chat/" + server + "/"
# create the client
client = IRCClient()
client.start(server, port)
# add root files
root = Channel("")
root.start()
# register with server
client.send('USER %s 8 * :some guy' % screenName)
client.send('NICK :%s' % screenName)


