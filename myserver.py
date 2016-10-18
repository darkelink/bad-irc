#!/usr/bin/env python

import sys
from ex3utils import Server

users = {}

class User(object):
  channels = []
  def __init__(self, nick, socket):
    self.socket = socket
    self.nick = nick
    users[nick] = self

  def send(self, message):
    self.socket.send(message)

  def disconnect(self):
    pass
    # self.socket.close()

  def addChannel(self, channel):
    self.channels.append(channel)

  def setNick(self, nick):
    for c in self.channels:
      for u in c.cUsers:
        u.send(":%s NICK :%s" % (self.nick, nick))
    self.send(":%s NICK :%s" % (self.nick, nick))
    users[self.nick] = None
    users[nick] = self
    self.nick = nick

  def leaveChannel(self, channel):
    self.channels.remove(channel)
    channel.removeUser(self)

  def __str__(self):
    return self.nick


class Channel(object):
  def __init__(self, name):
    self.name = name
    self.cUsers = []

  def addUser(self, user):
    if not user in self.cUsers:
      self.cUsers.append(user)
      return True
    return False

  def removeUser(self, user):
    if user in self.cUsers:
      for u in self.cUsers:
        u.send(":%s PART %s :Leaving" % (str(user), self.name))
      self.cUsers.remove(user)

  def getUsers(self):
    return self.cUsers

  def sendMessage(self, user, message):
    for u in self.cUsers:
      if u != user:
        u.send(":%s PRIVMSG %s :%s" % (str(user), self.name, message))


class Commands():
  def nick(args, longArg, socket):
    if not longArg in users:
      if hasattr(socket, "user"):
        socket.user.setNick(longArg)
      else:
        socket.user = User(longArg, socket)

  def join(args, longArg, user):
    global channels
    if longArg[0] == '#':
      if longArg not in channels:
        channels[longArg] = Channel(longArg)
      if channels[longArg].addUser(user):
        user.addChannel(channels[longArg])
        mess = ":%s 353 %s = %s :" % (ip, user.nick, longArg)
        for u in channels[longArg].getUsers():
          mess += str(u) + " "
          u.send(":%s JOIN :%s" % (str(user), longArg))
        user.send(mess)
        user.send(":%s 366 %s %s :End of /NAMES list." % (ip, user.nick, longArg))

  def part(args, longArg, user):
    global channels
    if not args:
      ch = longArg
    else:
      ch = args[0]
    user.leaveChannel(channels[ch])

  def privmsg(args, longArg, user):
    global channels
    sender = args[0]
    if args[0][0] == '#':
      if args[0] in channels and user in channels[args[0]].cUsers:
        channels[args[0]].sendMessage(user, longArg)
    elif args[0] in users:
      users[args[0]].send(":%s PRIVMSG %s :%s" % (str(user), args[0], longArg))
      user.send("channel not found")

  def quit(args, longArg, user):
    for ch in user.channels:
      user.leaveChannel(ch)
    user.disconnect()

  def listChannels(args, longArg, user):
    for name, users in channels.iteritems():
      user.send(":%s 322 %s %s %s" % (ip, user.nick, name, len(users.cUsers)))

  def user(args, longArg, user):
    pass

  commands = { "NICK"    : nick,
               "JOIN"    : join,
               "PART"    : part,
               "PRIVMSG" : privmsg,
               "QUIT"    : quit,
               "LIST"    : listChannels,
               "USER"    : user
             }
  
  @staticmethod
  def parseMessage(message, socket):
    (command, sep, params) = message.strip().partition(' ')

    command = command.upper()
    params = params.split(':', 1)
    args = params[0].split(' ')
    args = filter(None, args)
    longArg = params[-1].strip()

    if command in Commands.commands:
      if command == "NICK":
        Commands.commands["NICK"](args, longArg, socket)
      elif hasattr(socket, "user"):
        Commands.commands[command](args, longArg, socket.user)
      else:
        socket.send("You have not registered")
    else:
        socket.send("Command not found: " + command)


class Server(Server):
  def onStart(self):
    print "Server has started"

  def onStop(self):
    print "Server shutting down"

  def onConnect(self, socket):
    global userCount
    print "User connected"
    userCount += 1
    print "Connected users: " + str(userCount)

  def onDisconnect(self, socket):
    global userCount
    print "User disconnected"
    userCount -= 1
    print "Connected users: " + str(userCount)
		
  def onMessage(self, socket, message):
    Commands.parseMessage(message, socket)
    return True


ip = sys.argv[1]
port = int(sys.argv[2])

channels = {}
userCount = 0
server = Server()

server.start(ip, port)

