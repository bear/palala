#!/usr/bin/env python2.6

__author__ = "Mike Taylor (bear@code-bear.com)"
__copyright__ = "Copyright 2009-2010, Mike Taylor"
__license__ = "Apache v2"
__version__ = "0.1"
__contributors__ = []

"""
bTwitter - Twitter input bot

Loads a process per account to pull down each defined list
"""

import os, sys
import time
import json
import datetime

from multiprocessing import Process, Queue, current_process, freeze_support

import palala
import twitter


log           = None
twitterConfig = {}

def parseTwitterConfig(filename):
    if filename is not None and os.path.exists(filename):
        lines = open(filename, 'r').readlines()

        for line in lines:
            if len(line) > 0 and not line.startswith('#'):
                l = line[:-1].split(',')
                # twitter name, oauth, password/key

                userid = l[0].strip()

                if userid not in twitterConfig:
                    twitterConfig[userid] = {}

                t = twitterConfig[userid]

                t['userid'] = userid
                t['oauth']  = l[1].strip().lower().startswith('y')
                t['key']    = l[2].strip()


def eventHandler(event):
    pass
    #print event

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

def processTwitter(publish, cfgTwitter):
    api = twitter.Api(username=cfgTwitter['userid'], password=cfgTwitter['key'])
    try:
        since_id = long(palala.cache('twitter:%s:friends:sinceid' % cfgTwitter['userid']))
    except:
        since_id = None

    while True:
        print 'polling Friends Timeline'
        try:
            for status in api.GetFriendsTimeline(since_id=since_id):
                item = status.AsDict()
                data = { 'source':    { 'type':    'twitter',
                                        'channel': 'friends',
                                        'resource': cfgTwitter['userid'],
                                      },
                         'timestamp': '%s' % datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                         'metadata':  { 'post': item },
                         'event':     'inbound',
                       }
    
                publish('twitter', 'post', 'inbound', 'twitter.post', json.dumps(data))
    
                if not since_id or item['id'] > since_id:
                    since_id = item['id']
    
            palala.cache('twitter:%s:friends:sinceid' % cfgTwitter['userid'], '%s' % since_id)

        except:
            palala.dumpException('exception during Timeline poll')
        
        time.sleep(60)

_configItems = { 
                'twitterConfig': ('', '--twitterconfig', 'twitter.cfg', 'Twitter Config file'),
               }

if __name__ == '__main__':
    palala.init('bTwitter', configItems=_configItems)

    log = palala.log

    parseTwitterConfig(palala.options.twitterConfig)

    if palala.start(eventHandler):
        for userid in twitterConfig:
            item = twitterConfig[userid]

            Process(target=processTwitter, args=(palala.publish, item,)).start()
