#!/usr/bin/env python

__author__       = "Mike Taylor (bear@code-bear.com)"
__copyright__    = "Copyright 2009-2010, Mike Taylor"
__license__      = "Apache v2"
__version__      = "0.1"
__contributors__ = []

"""
Palala internal helper classes and routines
"""

import os, sys
import time
import types
import logging
import traceback
import subprocess

from xml.etree import cElementTree as ET
from xml.sax.saxutils import escape, quoteattr

from Queue import Empty
from multiprocessing import Process, Queue, current_process, freeze_support

from optparse import OptionParser

import sleekxmpp
from sleekxmpp.xmlstream.matcher.xpath import MatchXPath
from sleekxmpp.xmlstream.handler.callback import Callback

import daemon
import amqplib.client_0_8 as amqp
import pytyrant


log       = None
options   = None
_daemon   = None
_callback = None
_rmq      = None
_tyrant   = None
_admins   = ( 'bear@xmppnews.com', 'bear@twit.im', 'bear@code-bear.com', 'bear42@gmail.com', )

inbound   = Queue()


def dumpException(msg):
    """
    Gather information on the current exception stack and log it
    """
    t, v, tb = sys.exc_info()
    s        = '%s\n%s\n' % (msg, ''.join(traceback.format_exception(t, v, tb)))
    if log is None:
        print s
    else:
        log.exception(s)

def tostring(xml, xmlns='', stringbuffer='', namespace_map={}, root=True, cdata=()):
    newoutput = [stringbuffer]
    itag = xml.tag.split('}', 1)[-1]
    if '}' in xml.tag:
        ixmlns = xml.tag.split('}', 1)[0][1:]
    else:
        ixmlns = ''
    nsbuffer = ''
    if xmlns != ixmlns and ixmlns != '':
        if ixmlns in namespace_map:
            if namespace_map[ixmlns] != '':
                itag = "%s:%s" % (namespace_map[ixmlns], itag)
        else:
            nsbuffer = """ xmlns="%s\"""" % ixmlns
    newoutput.append("<%s" % itag)
    newoutput.append(nsbuffer)
    for attrib in xml.attrib:
        newoutput.append(""" %s="%s\"""" % (attrib, escXML(xml.attrib[attrib])))
    if root:
        for namespace in namespace_map:
            newoutput.append(""" xmlns:%s="%s\"""" % (namespace_map[namespace], namespace))
    if len(xml):
        newoutput.append(">")
        for child in xml.getchildren():
            newoutput.append(tostring(child, ixmlns, namespace_map=namespace_map, root=False, cdata=cdata))
        newoutput.append("</%s>" % (itag, ))
    elif xml.text:
        if itag in cdata:
            newoutput.append("><![CDATA[%s]]></%s>" % (xml.text, itag))
        else:
            newoutput.append(">%s</%s>" % (escXML(xml.text), itag))
    else:
        newoutput.append(" />")
    return ''.join(newoutput)

def escXML(text, escape_quotes=False):
    if type(text) != types.UnicodeType:
        if type(text) == types.IntType:
            s = str(text)
        else:
            s = text
        s = list(unicode(s, 'utf-8', 'ignore'))
    else:
        s = list(text)

    cc      = 0
    matches = ('&', '<', '"', '>')

    for c in s:
        if c in matches:
            if c == '&':
                s[cc] = u'&amp;'
            elif c == '<':
                s[cc] = u'&lt;'
            elif c == '>':
                s[cc] = u'&gt;'
            elif escape_quotes:
                s[cc] = u'&quot;'
        cc += 1
    return ''.join(s)

def handle_sigterm(signum, frame):
    log.info('handling SIGTERM [%s]' % _daemon.pidfile)

    if _daemon.pidfile is not None:
        try:
            os.remove(_daemon.pidfile)
        except (KeyboardInterrupt, SystemExit):
            dumpException('KI, SE trapped during PID removal')
            raise
        except Exception:
            dumpException('Exception trapped during PID removal')

    raise Exception('stopping')

def cache(id, value=None):
    if value is None:
        try:
            result = _tyrant[id]
        except KeyError:
            result = None
        return result
    else:
        _tyrant[id] = value

class xmppService(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, basename=None, ssl=False):

        self.plugin_config = {}

        self.jid      = jid
        self.password = password

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
            publish('xmpp', 'im', 'inbound', 'xmpp.%s/%s' % (event['jid'], event['resource']), event['message'])
        except:
            dumpException('exception during on_message callback')

    def on_muc(self, event):
        try:
            publish('xmpp', 'muc', 'inbound', '%s/%s: %s' % (event['room'], event['name'], event['message']))
        except:
            dumpException('exception during on_muc')

    def on_payload(self, event):
        try:
            publish('xmpp', 'payload', 'inbound', 'xmpp.payload', tostring(event.xml, namespace_map={}, cdata=('encoded',)))
        except:
            dumpException('exception during on_payload')

    def handleError(self, xml):
        error          = xml.find('{jabber:client}error')
        self.lasterror = error.getchildren()[0].tag.split('}')[-1]

    def ping(self, jid=None, priority=None):

        if priority is None:
            p = self._priority
        else:
            p = priority

        if jid is None:
            self.sendPresence(ppriority=p)
        else:
            self.sendPresence(pto=jid, ppriority=p)

    def joinRoom(self, room, nick=None, password=None):
        if nick is not None:
            nickname = nick
        else:
            nickname = self.basename

        log.info('joining %s' % room)

        self.muc.joinMUC(room, nickname, maxhistory="0", password=password)

class rmqService():
    """
    Initialize by passing in the RabbitMQ server connection information
    and a list of queues to create.
    
    Queues parameter is a list of queue items, which is a text file
    with each line defining a queue:

        queue name, exchange to bind to, routing key, True/False (if queue should be read/write)
    """
    def __init__(self, server, userid, password, config, callback):
        self.server     = server
        self.password   = password
        self.connection = None
        self.channel    = None
        self.exchanges  = []
        self.config     = {}

        self._parseConfig(config)

        try:
            log.info('rmq: building connection %s %s' % (server, userid))
            self.connection = amqp.Connection(server, userid, password, use_threading=False)

            log.debug('rmq: creating channel')
            self.channel = self.connection.channel()

            log.debug('rmq: ticket')
            self.ticket = self.channel.access_request('/data', active=True, write=True)

            for key in self.config:
                item        = self.config[key]
                exchange    = item['exchange']
                routing_key = item['key']

                if exchange not in self.exchanges:
                    log.debug('rmq: declaring exchange %s' % exchange)
                    self.channel.exchange_declare(exchange, type="topic", durable=False, auto_delete=False)
                    self.exchanges.append(exchange)

                if 'queue' in item:
                    log.debug('declaring queue %s' % item['queue'])
                    qname, qcount, ccount = self.channel.queue_declare(item['queue'], durable=False, exclusive=False, auto_delete=False)
    
                    log.info('binding queue %s to exchange %s [%s]' % (item['queue'], exchange, routing_key))
                    self.channel.queue_bind(item['queue'], exchange, routing_key)
    
                    if item['listen']:
                        self.channel.basic_consume(item['queue'], callback=callback)

        except:
            self.channel    = None
            self.connection = None
            dumpException('error during RMQ setup')

    def stop(self):
        self.channel.close()
        self.connection.close()

    def check(self):
        result = True
        for exchange in self.exchanges:
            try:
                self.post('***ping***', 'inbound', exchange)
            except:
                result = False
                dumpException('error during rmq sanity check')
        return result

    def post(self, data, key, exchange):
        msg = amqp.Message(data)
        msg.properties["delivery_mode"] = 1

        self.channel.basic_publish(msg, exchange, key)

    def _parseConfig(self, filename):
        if filename is not None and os.path.exists(filename):
            lines = open(filename, 'r').readlines()

            for line in lines:
                if len(line) > 0 and not line.startswith('#'):
                    l = line[:-1].split(',')
                    # queue name, exchange to bind to, routing key, listen (true/false)

                    if l[0] not in self.config:
                        self.config[l[0]] = {}

                    q = self.config[l[0]]

                    q['queue']    = l[0].strip()
                    q['exchange'] = l[1].strip()
                    q['key']      = l[2].strip()
                    q['listen']   = l[3].strip().lower().startswith('t')

def initOptions(defaults=None):
    global options

    error   = False
    usage   = "usage: %prog [options]\n"
    parser  = OptionParser(usage=usage, version="%prog")

    if defaults:
        for key in defaults:
            items = defaults[key]

            if len(items) == 4:
                (shortCmd, longCmd, defaultValue, helpText) = items
                optionType = 's'
            else:
                (shortCmd, longCmd, defaultValue, helpText, optionType) = items

            if optionType == 'b':
                parser.add_option(shortCmd, longCmd, dest=key, action='store_true', default=defaultValue, help=helpText)
            else:
                parser.add_option(shortCmd, longCmd, dest=key, default=defaultValue, help=helpText)

    (options, args) = parser.parse_args()
    options.args    = args

    options.config = os.path.abspath(options.config)

    if not os.path.isfile(options.config):
        options.config = os.path.join(options.config, '%s.cfg' % options.basename)

    if not os.path.isfile(options.config):
        options.config = os.path.abspath(os.path.join(os.getcwd(), '%s.cfg' % options.basename))

    if os.path.isfile(options.config):
        for line in open(options.config, 'r').readlines():
            item = line[:-1].split('=')
            if len(item) == 2:
                setattr(options, item[0], item[1])

    if options.logpath is not None:
        options.logpath = os.path.abspath(options.logpath)

    if os.path.isdir(options.logpath):
        options.logfile = os.path.join(options.logpath, '%s.log'% options.basename)
    else:
        sys.stderr.write('Log path [%s] not found\n' % options.logpath)
        error = True

    if options.daemon:
        options.pidpath = os.path.abspath(options.pidpath)

        if not os.path.isdir(options.pidpath):
            sys.stderr.write('PID path [%s] not found\n' % options.pidpath)
            error = True

        options.pidfile = os.path.join(options.pidpath, '%s.pid' % options.basename)
        options.daemon  = None

    if error:
        sys.exit(1)

def initLogging():
    """
    Initialize the logging environment and setup a console
    echo if required.
    
    This does no rotation of logs as the current TimedRotate*
    handlers are buggy.
    """
    global log

    log = logging.getLogger()

    fileHandler   = logging.FileHandler(options.logfile)
    fileFormatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    fileHandler.setFormatter(fileFormatter)

    log.addHandler(fileHandler)
    log.fileHandler = fileHandler

    if options.console:
        echo          = logging.StreamHandler()
        echoFormatter = logging.Formatter('%(levelname)-8s %(message)s')

        log.addHandler(echo)
        log.info('echoing')

    if options.debug:
        log.setLevel(5)
        log.info('debug on')
    else:
        log.setLevel(logging.INFO)

def init(basename, configDefaults=None, configItems=None):
    global _daemon

    cwd  = os.path.abspath(os.getcwd())
    home = os.path.expanduser('~')

    _configDefaults = { 'basename':    basename,
                        'daemon':      False,
                        'pidpath':     cwd,
                        'logpath':     cwd,
                        'uid':         None,
                        'console':     True,
                        'debug':       True,
                        'rmqServer':   None,
                        'rmqUser':     'guest',
                        'rmqPassword': None,
                        'rmqConfig':   None,
                       }

    palalaConfig = os.path.join(cwd, 'palala.cfg')

    if os.path.isfile(palalaConfig):
        for line in open(palalaConfig, 'r').readlines():
            if not line.startswith('#'):
                item = line[:-1].split('=')
                if len(item) == 2:
                    _configDefaults[item[0]] = item[1]

    if configDefaults is not None:
        for key in configDefaults:
            _configDefaults[key] = configDefaults[key]

    _configItems = { 
        'basename':    ('',   '--name',      _configDefaults['basename'],    'Name of the bot'),
        'daemon':      ('',   '--daemon',    _configDefaults['daemon'],      'run as a daemon',        'b'),
        'pidpath':     ('',   '--pidpath',   _configDefaults['pidpath'],     'pid file path'),
        'logpath':     ('',   '--logpath',   _configDefaults['logpath'],     'log file path'),
        'uid':         ('',   '--uid',       _configDefaults['uid'],         'uid to run as'),
        'console':     ('-e', '--echo',      _configDefaults['console'],     'echo to console',        'b'),
        'debug':       ('-d', '--debug',     _configDefaults['debug'],       'turn on debug messages', 'b'),
        'rmqServer':   ('',   '--rmqserver', _configDefaults['rmqServer'],   'Hostname for RMQ Server'),
        'rmqUser':     ('',   '--rmquser',   _configDefaults['rmqUser'],     'Username to login to RMQ Server'),
        'rmqPassword': ('',   '--rmqpw',     _configDefaults['rmqPassword'], 'User password for RMQ Server'),
        'rmqConfig':   ('',   '--rmqconfig', _configDefaults['rmqConfig'],   'Queue Config file for RMQ Server'),
    }

    if configItems is not None:
        for key in configItems:
            _configItems[key] = configItems[key]

    if 'config' not in _configItems:
        s = os.path.join(home, 'etc', '%s.cfg' % _configDefaults['basename'])
        _configItems['config'] = ('-c', '--config', s, 'Configuration file to load',)

    initOptions(_configItems)
    initLogging()

    if options.daemon:
        try:
            _daemon = daemon.Daemon(pidfile=options.pidfile, user=options.uid, sigterm=handle_sigterm, log=log.fileHandler)
        except:
            dumpException('exception setting up daemon')
            sys.exit(1)

        log.info('forking daemon - pidfile is %s' % options.pidfile)
        _daemon.start()

    log.info('%s starting' % options.basename)

def publish(source, type, exchange, key, body):
    log.info('publish: %s %s %s %s' % (source, type, exchange, key))
    _rmq.post(body, key, exchange)

def push(source, type, exchange, key, body):
    log.info('push: %s %s %s %s' % (source, type, exchange, key))
    inbound.put((source, type, exchange, key, body))

def rmqCallback(msg):
        # for key, val in msg.properties.items():
        #     log.debug('property %s: %s' % (key, str(val)))
        # for key, val in msg.delivery_info.items():
        #     log.debug('info %s: %s' % (key, str(val)))

    try:
        log.debug('msg body: %s' % msg.body)

        try:
            inbound.put(('rmq', 'post', msg.delivery_info['exchange'], msg.delivery_info['routing_key'], msg.body))
            # push('rmq', 'post', msg.delivery_info['exchange'], msg.delivery_info['routing_key'], msg.body)
        except:
            dumpException('error during rmq callback')
    finally:
        msg.channel.basic_ack(msg.delivery_tag)

def processRMQ(rmq):
    if rmq.channel is not None:
        while rmq.channel.callbacks:
            rmq.channel.wait()
    else:
        while True:
            time.sleep(5)

def defaultHandler(qInbound):
    while True:
        try:
            event = qInbound.get(False)
        
            if event is not None:
                _callback(event)
        except Empty:
            time.sleep(0.2)

def start(eventHandler):
    global _callback, _rmq, _tyrant

    log.info('Starting process loop')
    try:
        _callback = eventHandler
        _tyrant   = pytyrant.PyTyrant.open('palala.org', 10101)
        _rmq      = rmqService(options.rmqServer, options.rmqUser, options.rmqPassword, options.rmqConfig, rmqCallback)

        if _rmq.check():
            Process(target=defaultHandler, args=(inbound,)).start()
            Process(target=processRMQ, args=(_rmq,)).start()
            result = True
        else:
            log.error('RMQ Environment is not setup as expected')
            result = False
    except:
        dumpException('Error during pull.start()')

    return result
