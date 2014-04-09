#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy
import simplejson
import datetime
import cPickle as pickle
import support
import sys
import re
import os
import zmq

reload(sys)
sys.setdefaultencoding('utf-8')

#----------------------------------------------------------------------------------
# ZMQ client
class ZmqClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect('ipc:///tmp/jeppkend')

    def perform_command(self, cmd, text):
        self.socket.send(pickle.dumps({'cmd': cmd, 'text': text.encode('utf-8', 'ignore')}))
        msg = self.socket.recv()
        return pickle.loads(msg)['text'].decode('utf-8', 'ignore')

class FrontendApp(object):
    exposed = True
    def POST(self, *args, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        # Auth check
        if (kwargs['token'] != auth.slash_team_token):
            return simplejson.dumps(dict(text=''))
        # Prevent own messages
        if (kwargs['user_id'] == u'USLACKBOT'):
            return simplejson.dumps(dict(text=''))

        message = kwargs['text'].decode('utf-8', 'ignore')
        zq = ZmqClient()

        if message.endswith('[o]'):
            text = zq.perform_command('dump','')
            if text:
                return simplejson.dumps(dict(text=text.encode('utf-8','ignore')))

        if message.endswith('[x]'):
            msg = support.html_to_text(message[:-3].strip())
            reply = zq.perform_command('jepp', msg)
            if reply:
                return simplejson.dumps(dict(text=reply.encode('utf-8','ignore')))

        if 'в штанах' in message.lower():
            return simplejson.dumps(dict(text=zq.perform_command('vshtanah','').encode('utf-8','ignore')))

        return simplejson.dumps(dict(text=''))

if __name__ == '__main__':
    cherrypy.log.screen = True
    print 'App starting'
    cherrypy.config.update({'server.socket_host': '127.0.0.1',
            'server.socket_port': 8511})
    cherrypy.tree.mount(
        FrontendApp(), '/message',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.engine.start()
    print 'App started'
    cherrypy.engine.block()
