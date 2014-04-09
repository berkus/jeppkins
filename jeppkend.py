#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import cPickle as pickle
import hashlib
from random import choice
from time import time
import tweepy # Twitter API
import auth # login info
import zmq

reload(sys)
sys.setdefaultencoding('utf-8')

#----------------------------------------------------------------------------------
# This is a backend which runs event loop using zeromq,
# receives jeppking requests, keeps database and posts to twitter.
#----------------------------------------------------------------------------------

def msg_hash(msg):
    h = hashlib.md5()
    h.update(msg)
    return h.digest()


class Twitter:
    def __init__(self):
        oauth = tweepy.OAuthHandler(auth.consumer_key, auth.consumer_secret)
        oauth.set_access_token(auth.access_token, auth.access_token_secret)

        self.api = tweepy.API(oauth)
        print "Logged in to twitter as", self.api.me().name

    def post(self, msg):
        print "Posting jepp:", msg.encode('utf-8','ignore')
        try:
            self.api.update_status(msg)
            print "...posted"
        except:
            print "ERROR POSTING"
            return False
            # queue.append(msg)
        return True

# Tag cloud
class Cloud:
    # Cloud contains jepp from the last 6h
    # Tuples in format (timestamp, jepp, is_posted)
    cloud = []
    # Seen contains hashes of all seen messages
    seen = set()

    def __init__(self):
        # Read in data files on start
        if os.path.isfile('cloud.dat'):
            file = open('cloud.dat', 'rb')
            self.cloud = pickle.load(file)
            file.close()

        if os.path.isfile('seen.dat'):
            file = open('seen.dat', 'rb')
            self.seen = pickle.load(file)
            file.close()

        self.add_cloud_to_seen()
        self.last_zhep_time = time()

    def add(self, msg):
        self.cloud.append([time(), msg, False])
        self.seen.add(hash)
        self.cloud.sort()
        while (len(self.cloud) > 16) and (self.cloud[0][0] < time() - 12*60*60):
            self.cloud.pop(0)

        self.save_files()
        delta = time() - self.last_zhep_time
        self.last_zhep_time = time()
        return delta

    def save_files(self):
        file = open('cloud.dat', 'wb')
        pickle.dump(self.cloud, file, pickle.HIGHEST_PROTOCOL)
        file.close()

        file = open('seen.dat', 'wb')
        pickle.dump(self.seen, file, pickle.HIGHEST_PROTOCOL)
        file.close()

    def have_seen(self, hash):
        return hash in self.seen

    def add_cloud_to_seen(self):
        [self.seen.add(msg_hash(x[1])) for x in self.cloud]

    def clouddump(self):
        return 'Облако тупой фигни: '+' '.join([x[1] for x in self.cloud])

twitter = Twitter()
cloud = Cloud()
replies = ['ЗАЖЕПЛЕНО!!1', 'РАЗЖЕПЛЕНО!!1', 'ZHPLN!!1', 'UPDATED MY JOURNAL', 'WHAT DOES ONE TWEET MATTER?']
v_shtanah = ['ВШТНХ!!1', 'ОТЛЧН!!1', 'ОТКЛЧН!!1', 'OTKLCHN!!1']

# zmq handler for zhepping msg
def run_zhepping(msg):
    print 'Zhep'
    hash = msg_hash(msg)
    if len(msg) > 0 and len(msg) < 140 and not cloud.have_seen(hash):
        twitter.post(msg)

        delta = cloud.add(msg)

        # One more idea: limit the printed cloud size based on backoff time
        if delta > 30*60: # 30 minutes
            return cloud.clouddump()
        elif delta > 2:
            return choice(replies)
        else:
            print "Not saying anything, throttled."
    return ""

# zmq handler for vshtanah msg
def get_vshtanah_text():
    print 'Vshtanah'
    return choice(v_shtanah)

# zmq handler for [o] msg
def get_cloud_dump():
    print 'Cloud'
    return cloud.clouddump()

#----------------------------------------------------------------------------------
# Main
# Create zmq server and loop around serving clients
#----------------------------------------------------------------------------------

print "Starting jeppkend"

# server
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind('ipc:///tmp/jeppkend')
while True:
    msg = socket.recv()
    msg = pickle.loads(msg) # Gives [cmd] and [text], return only [text]
    text = msg['text'].decode('utf-8', 'ignore')
    if msg['cmd'] == 'jepp':
        socket.send(pickle.dumps({'text': run_zhepping(text).encode('utf-8', 'ignore')}))
    elif msg['cmd'] == 'vshtanah':
        socket.send(pickle.dumps({'text': get_vshtanah_text().encode('utf-8', 'ignore')}))
    elif msg['cmd'] == 'dump':
        socket.send(pickle.dumps({'text': get_cloud_dump().encode('utf-8', 'ignore')}))
    elif msg['cmd'] == 'quit':
        cloud.save_files()
        print "Stopping jeppkend"
        sys.exit()
    else:
        cloud.save_files()
        socket.send(pickle.dumps({'text': ''}))




