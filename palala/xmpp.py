#!/usr/bin/env python

__author__       = "Mike Taylor (bear@code-bear.com)"
__copyright__    = "Copyright 2009-2010, Mike Taylor"
__license__      = "Apache v2"
__version__      = "0.1"
__contributors__ = []

"""
Palala XMPP
"""

import os, sys
import logging

from xml.etree import cElementTree as ET
from xml.sax.saxutils import escape, quoteattr

import sleekxmpp
from sleekxmpp.xmlstream.matcher.xpath import MatchXPath
from sleekxmpp.xmlstream.handler.callback import Callback

import utils

log = logging.getLogger()


class xmppService(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, callback, basename=None, ssl=False):

        self.plugin_config = {}

        self.jid      = jid
        self.password = password
        self.callback = callback

        if basename is None:
            self.basename = self.jid
        else:
            self.basename = basename

        self._priority = 100
        self.botActive = False

        sleekxmpp.ClientXMPP.__init__(self, self.jid, self.password, ssl, self.plugin_config, {})

        self.registerPlugin('xep_0092', { 'name': 'XMPP Daemon', 'version': __version__ })
        self.registerPlugin('xep_0004')
        self.registerPlugin('xep_0030')
        self.registerPlugin('xep_0060', {})
        self.registerPlugin('xep_0045', {})

        self.site_values    = []
        self.auto_authorize = True
        self.auto_subscribe = True

        self.pubsub = self.plugin['xep_0060']
        self.muc    = self.plugin['xep_0045']

        # [(room, nick, password)]
        self.roomlist = []

        self.lasterror = ''

        self.add_event_handler("session_start",     self.on_start,   threaded=True)
        self.add_event_handler("message",           self.on_message, threaded=True)
        self.add_event_handler("groupchat_message", self.on_muc,     threaded=True)

        self.add_handler("<iq type='error' />", self.handleError)

        self.registerHandler(Callback("payload", MatchXPath("{jabber:client}message/{http://jabber.org/protocol/pubsub#event}event"), self.on_payload, thread=True))

        self.rootnode = 'pubsub.%s' % self.getjidbare(jid).split('@')[1]

    def on_start(self, event):
        self.getRoster()
        self.ping()
        self.ping(self.rootnode)

        self.botActive = True

        for room in self.roomlist:
            self.joinRoom(room[0], room[1], room[2])

    def on_message(self, event):
        try:
            # source, type, exchange, key, body
            self.callback('xmpp', 'im', 'inbound', 'xmpp.%s/%s' % (event['jid'], event['resource']), event['message'])
        except:
            utils.dumpException('exception during on_message callback')

    def on_muc(self, event):
        try:
            self.callback('xmpp', 'muc', 'inbound', '%s/%s: %s' % (event['room'], event['name'], event['message']))
        except:
            utils.dumpException('exception during on_muc')

    def on_payload(self, event):
        try:
            self.callback('xmpp', 'payload', 'inbound', 'xmpp.payload', utils.tostring(event.xml, namespace_map={}, cdata=('encoded',)))
        except:
            utils.dumpException('exception during on_payload')

    def handleError(self, xml):
        error          = xml.find('{jabber:client}error')
        self.lasterror = error.getchildren()[0].tag.split('}')[-1]

    def ping(self, jid=None, priority=None):

        if priority is None:
            p = self._priority
        else:
            p = priority

        if jid is None:
            log.info('Sending presence with priority %s' % p)
            self.sendPresence(ppriority=p)
        else:
            log.info('Sending presence with priority %s to %s' % (p, jid))
            self.sendPresence(pto=jid, ppriority=p)

    def joinRoom(self, room, nick=None, password=None):
        if nick is not None:
            nickname = nick
        else:
            nickname = self.basename

        log.info('joining %s' % room)

        self.muc.joinMUC(room, nickname, maxhistory="0", password=password)

