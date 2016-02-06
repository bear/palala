#!/usr/bin/env python2.6

__author__ = "Mike Taylor (bear@code-bear.com)"
__copyright__ = "Copyright 2009-2010, Mike Taylor"
__license__ = "Apache v2"
__version__ = "0.1"
__contributors__ = []

"""
bSwitch - input bot switch

Loads a process per account to pull down each defined list
"""

import os, sys
import time
import json
import datetime

from xml.etree import cElementTree as ET
from xml.sax.saxutils import escape, quoteattr

from Queue import Empty
from multiprocessing import Process, Queue, current_process, freeze_support

import palala
import palala.xmpp
import palala.utils


log        = None
xmppConfig = {}
inbound    = Queue()
pubsub     = Queue()


def parseXMPPConfig(filename):
    if filename is not None and os.path.exists(filename):
        lines = open(filename, 'r').readlines()

        for line in lines:
            if len(line) > 0 and not line.startswith('#'):
                l = line[:-1].split(',')
                if len(l) > 1:
                    # jid, password
                    jid = l[0].strip()
                    pw  = l[1].strip()

                    if jid not in xmppConfig:
                        xmppConfig[jid] = {}

                    x = xmppConfig[jid]

                    x['jid']      = jid
                    x['password'] = pw


#data = { 'source': { 'type': 'twitter',
#                             'resource': user['id'],
#                   },
#         'timestamp': '%s' % datetime.datetime.now().strftime('%Y-%m-%dT%H%M%SZ'),
#         'metadata':  { 'user': user },
#         'event':     'user',
#       }
#data = { 'source':    { 'type':    'twitter',
#                        'channel': 'friends',
#                        'resource': cfgTwitter['userid'],
#                      },
#         'timestamp': '%s' % datetime.datetime.now().strftime('%Y-%m-%dT%H%M%SZ'),
#         'metadata':  { 'post': item },
#         'event':     'inbound',
#       }
# friends timeline
#{"created_at": "Fri Nov 13 07:45:00 +0000 2009", 
# "favorited": false, 
# "id": 5674211579, 
# "source": "<a href=\"http://blip.fm\" rel=\"nofollow\">Blip.fm</a>", 
# "text": "listening to \"Damien Rice - 9 Crimes - Official Video\" \u266b http://blip.fm/~g9zm7", 
# "truncated": false, 
# "user": {"description": "just a girl in a virtual world - VW developer: www.thevesuviusgroup.com & non-profit web 2.0 gal: olp.globalkids.org", 
#          "favourites_count": 113, 
#          "followers_count": 2144, 
#          "friends_count": 2245, 
#          "id": 816952, 
#          "location": "Boston, MA", 
#          "name": "Joyce Bettencourt", 
#          "profile_background_color": "FFFBF0", 
#          "profile_background_tile": true, 
#          "profile_image_url": "http://a3.twimg.com/profile_images/478765027/09162009587_normal.jpg", 
#          "profile_link_color": "B73030", 
#          "profile_sidebar_fill_color": "http://a3.twimg.com/profile_background_images/3309557/moi-twitter2.jpg", 
#          "profile_text_color": "000000", 
#          "protected": false, 
#          "screen_name": "RhiannonSL", 
#          "statuses_count": 2252, 
#          "time_zone": "Eastern Time (US & Canada)", 
#          "url": "http://joycebettencourt.com", 
#          "utc_offset": -18000
#          }
# }

def toAtom(data):
    xmlTitle = palala.utils.escXML(data['title']).encode('UTF-8')

    atom = ET.Element('{http://www.w3.org/2005/Atom}entry')

    a_title      = ET.Element('title', {'type': 'html'})
    a_title.text = xmlTitle

    a_link      = ET.Element('link',  {'href': data['referenceURL']})
    a_id        = ET.Element('id')
    a_id.text   = data['guid']

    a_uri       = ET.Element('uri')
    a_uri.text  = data['uri']

    a_author    = ET.Element('author')
    a_name      = ET.Element('name')
    a_name.text = data['fullname']

    a_author.append(a_name)
    a_author.append(a_uri)

    a_published      = ET.Element('published')
    a_published.text = data['postDate']
    
    a_updated      = ET.Element('updated')
    a_updated.text = data['postDate']

    a_source           = ET.Element('source')
    a_source_title     = ET.Element('title', {'type': 'html'})
    a_source_id        = ET.Element('id')
    a_source_generator = ET.Element('generator')

    a_source_title.text     = xmlTitle
    a_source_id.text        = data['uri']
    a_source_generator.text = 'Palala %s' % __version__

    a_source.append(a_source_generator)
    a_source.append(a_source_id)
    a_source.append(a_source_title)
    a_source.append(a_updated)

    a_content      = ET.Element('content')
    a_content.text = data['content']

    atom.append(a_id)
    atom.append(a_title)
    atom.append(a_updated)
    atom.append(a_published)
    atom.append(a_link)
    atom.append(a_author)
    atom.append(a_source)
    atom.append(a_content)

    log.debug('xml: %s' % palala.utils.tostring(atom, namespace_map={}, cdata=('encoded',)))

    return atom

def processTwitterPost(xmpp, body):
    jData = json.loads(body)

    guid, atom = twitterToAtom(jData)
    try:
        xmpp.pubsub.setItem(xmpp.rootnode, 'test::atom', [(guid, atom),])
    except:
        palala.utils.dumpException('processXMPP pubsub send')

def twitterToAtom(jData):

    s = jData['timestamp'][:19] # 2008-08-19T19:45:14Z or 2008-08-19T19:45:14.183Z
    t = time.strptime(s, '%Y-%m-%dT%H:%M:%S')
    createDate = datetime.datetime(t[0],t[1],t[2],t[3],t[4],t[5],t[6])

#    s = jData['metadata']['post']['created_at'][:19] # Fri Nov 13 07:45:00 +0000 2009
#    t = time.strptime(s, '%Y-%m-%dT%H:%M:%S')
#    postDate = datetime.datetime(t[0],t[1],t[2],t[3],t[4],t[5],t[6])
    
    postDate = createDate
    postID   = '%s' % jData['metadata']['post']['id']
    userID   = '%s' % jData['metadata']['post']['user']['id']
    username = '%s' % jData['metadata']['post']['user']['screen_name']
    fullname = username

    uData = palala.cache('twitter:user:id:%s' % userID)

    if uData is not None:
        jUser = json.loads(uData)

        fullname = jUser['name']
        username = jUser['screen_name']

    guid    = '%s-%s-%s' % (jData['source']['type'], userID, postID)
    postURL = 'http://twitter.com/%s/status/%s' % (username, postID)

    atom = {}

    atom['guid']         = guid
    atom['referenceURL'] = postURL
    atom['uri']          = postURL
    atom['createDate']   = createDate.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    atom['postDate']     = postDate.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    atom['title']        = 'Post from %s (via )' % username
    atom['fullname']     = fullname
    atom['username']     = username
    atom['content']      = jData['metadata']['post']['text']

    return atom['guid'], toAtom(atom)

def updateTwitterUser(body):
    try:
        jData = json.loads(body)
        user  = jData['metadata']['post']['user']
        palala.cache('twitter:user:id:%s' % user['id'], json.dumps(user))  
    except:
        palala.utils.dumpException('updateTwitterUser()')

def eventHandler(event):
    source, type, exchange, key, body = event
    log.info('switch: %s %s %s %s' % (source, type, exchange, key))

    try:
        if source == 'rmq':
            if type == 'post':
                if key == 'twitter.post':
                    log.info('pushing %s item to inbound queue' % key)
                    inbound.put((key, body))
    except:
        palala.utils.dumpException('rmq eventHandler')

def processInbound(publish, qInbound, qPubsub):
    log.info('processInbound start')
    while True:
        try:
            item = qInbound.get(False)
            if item is not None:
                try:
                    key, body = item
                    #log.info('updating twitter user cache')
                    #try:
                    #    updateTwitterUser(body)
                    #except:
                    #    palala.utils.dumpException('updateTwitterUser()')

                    log.info('pushing to pubsub queue')
                    qPubsub.put((key, body))
                except:
                    palala.utils.dumpException('processInbound loop')
        except Empty:
            time.sleep(1)

    log.info('processInbound stop')

def processXMPP(publish, qPubsub, cfg):
    log.info('processXMPP start')
    try:
        xmpp = palala.xmpp.xmppService(cfg['jid'], cfg['password'], palala.publish)
    
        xmpp.connect()
        xmpp.process(threaded=True)

        while True:
            try:
                item = qPubsub.get(False)
                if item is not None:
                    try:
                        key, body = item
                        processTwitterPost(xmpp, body)
                    except:
                        palala.utils.dumpException('twitterToAtom()')
            except Empty:
                time.sleep(1)
    except:
        palala.utils.dumpException('exception during XMPP startup')

    log.info('processXMPP stop')


_configDefaults = { 'rmqConfig': 'switch.rmq',
                  }
_configItems = { 
                'xmppConfig': ('', '--xmppconfig', 'xmpp-switch.cfg', 'XMPP Config file'),
               }

if __name__ == '__main__':
   palala.init('bSwitch', configDefaults=_configDefaults, configItems=_configItems)

   parseXMPPConfig(palala.options.xmppConfig)

   log = palala.log

   if palala.start(eventHandler):
       for jid in xmppConfig:
           Process(target=processXMPP, args=(palala.publish, pubsub, xmppConfig[jid],)).start()

       Process(target=processInbound, args=(palala.publish, inbound, pubsub)).start()
