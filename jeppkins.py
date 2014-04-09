#!/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------------
# This is a Skype plugin for jeppkins, it interfaces with skypekit
# to receive/send messages and forwards them to jeppkend via zmq.
#----------------------------------------------------------------------------------

import sys
import keypair
from time import sleep
import os.path
import zmq
import cPickle as pickle

reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(keypair.distroRoot + '/ipc/python')
sys.path.append(keypair.distroRoot + '/interfaces/skype/python')

try:
    import Skype
except ImportError:
    raise SystemExit('Program requires Skype and skypekit modules')

import re, support

import auth # login info

#----------------------------------------------------------------------------------
# ZMQ client
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('ipc:///tmp/jeppkend')

def perform_command(cmd, text):
    socket.send(pickle.dumps({'cmd': cmd, 'text': text.encode('utf-8', 'ignore')}))
    msg = socket.recv()
    return pickle.loads(msg)['text'].decode('utf-8', 'ignore')


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
# ACCOUNT LOGIN
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------

loggedIn    = False

def AccountOnChange (self, property_name):
    global loggedIn
    if property_name == 'status':
        print ('Login sequence: ' + self.status)
        if self.status == 'LOGGED_IN':
            loggedIn = True
        if self.status == 'LOGGED_OUT':
            loggedIn = False

Skype.Account.OnPropertyChange = AccountOnChange

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
# CALLS HANDLING (REJECTING THEM!)
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------

def RejectCall(self):
    print('Incoming call, dropping')
    self.LeaveLiveSession()

Skype.Conversation.RejectCall = RejectCall

#----------------------------------------------------------------------------------
# Conversation.OnPropertyChange event will only fire when the corresponding
# Conversation object is already created. This means that we will not get
# this event when the object is created as a -result- of a property change.
# The -first- Conversation.local_livestatus == 'RINGING_FOR_ME' will -not-
# fire for us, because we only get the conversation object as a result of this
# property change, in Skype.OnConversationListChange callback.

def ConversationOnChange (self, property_name):
    if property_name == 'local_livestatus':
        if self.local_livestatus == 'RINGING_FOR_ME':
            print(self.displayname + ' RING! RING! (from Conversation.OnPropertyChange)')
            self.RejectCall()

Skype.Conversation.OnPropertyChange = ConversationOnChange

#----------------------------------------------------------------------------------
# Skype.Skype (basically our Skype class)
# Now, Skype.OnConversationListChange -will- fire on the first incoming call,
# as we already have a Skype object and OnConversationListChange is a method of that
# class. So the first incoming call in any given conversation we can pick up here,
# when the local_livestatus goes 'RINGING_FOR_ME'.
#
# The problem here is that if the call drops and immediately after that, another call
# comes in from the same conversation - the OnConversationListChange event will not
# fire again. The reason is that conversations remain in the LIVE_CONVERSATIONS list
# for several seconds after the call goes down. Solution is to keep the conversation
# object somewhere (in our case the SkyLib.liveSession variable) so that OnPropertyChange
# callback will fire, when the second call comes. Then we can pick the call up from there.

def SkypeOnConversationListChange (self, conversation, type, added):
    if type == 'LIVE_CONVERSATIONS':
        if conversation.local_livestatus == 'RINGING_FOR_ME':
            print(conversation.displayname + ' RING! RING! (from Skype.OnConversationListChange).')
            conversation.RejectCall()

        if added == True:
            conversation.RejectCall()
            print(conversation.displayname + ' added to live list.')

        if added == False:
            print(conversation.displayname + ' is no longer in live list.')

Skype.Skype.OnConversationListChange = SkypeOnConversationListChange


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
# CHAT MESSAGES
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------

# A checked PostText - before posting verifies that we have posting rights there
# (rights are WRITER and above). This prevents (not fully - races possible) a nasty
# exception in the Skype IPC layer where it raises decode error when you try to post
# in a convo where you have no rights.
# This has to be fixed in either skypekit IPC or skypekit itself, so no luck with that.
def PostTextChecked(self, message, isXml = False):
    me = self.GetParticipants("MYSELF")[0]
    if Skype.Participant.RANK[me.rank] <= Skype.Participant.RANK["WRITER"]:
        self.PostText(message, isXml)
    else:
        print "I'm not allowed to post, so I won't"

Skype.Conversation.PostTextChecked = PostTextChecked
# /PostTextChecked

def set_mood_message(acc, msg):
    global MySkype
    if MySkype.ValidateProfileString(Skype.Account.P_MOOD_TEXT, msg):
        acc.SetStrProperty(Skype.Account.P_MOOD_TEXT, msg)

def ignored_author(author):
    return author in [auth.accountName, 'vosyana', 'the.zhazha', 'pdobot']

def OnMessage(self, message, changesInboxTimestamp, supersedesHistoryMessage, conversation):
    global account
    if (message.type == 'POSTED_TEXT') and not ignored_author(message.author):
        if message.body_xml.endswith('[o]'):
            text = perform_command('dump','')
            if text:
                conversation.PostTextChecked(text, False)

        if message.body_xml.endswith('[x]'):
            msg = support.html_to_text(message.body_xml[:-3].strip())
            reply = perform_command('jepp', msg)
            if reply:
                conversation.PostTextChecked(reply, True)
                set_mood_message(account, msg)

    elif 'в штанах' in message.body_xml.lower():
                conversation.PostTextChecked(perform_command('vshtanah',''), True)

Skype.Skype.OnMessage = OnMessage


#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
# MAIN LOOP
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------

#----------------------------------------------------------------------------------
# Creating our main Skype object

try:
    MySkype = Skype.GetSkype(keypair.keyFileName)
#    MySkype = Skype.GetSkype(keypair.keyFileName, True, '127.0.0.1', 8963, "transportlog", True)
except Exception:
    raise SystemExit('Unable to create Skype instance')

#----------------------------------------------------------------------------------
# Retrieving account and logging in with it. Then waiting in loop.

account = MySkype.GetAccount(auth.accountName)

print('Logging in with ' + auth.accountName)
account.LoginWithPassword(auth.accountPsw, False, False)

while loggedIn == False:
    sleep(1)

print('Now running..')
raw_input("Press ENTER to exit\n\n")

print('Exiting..')
MySkype.stop()

