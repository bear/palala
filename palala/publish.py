# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import json
import uuid
import datetime

from flask import current_app

from bearlib.tools import baseDomain

import pytz
import ronkyuu

def process(sourceURL, targetURL):
    """Publish webmention for sourceURL

    Publishing is handled as a Webmention sent to the /publish URL
    as the targetURL included somewhere within the sourceURL

    All you need is to include the following:
      <a href="https://indieweb.news/publish"></a>

    somewhere in the sourceURL
    """
    current_app.logger.info('process [%s][%s]' % (sourceURL, targetURL))
    result   = None
    mentions = ronkyuu.findMentions(sourceURL)
    for href in mentions['refs']:
        current_app.logger.info('process href [%s]' % href)
        if href != sourceURL and href == targetURL:
            utcdate   = datetime.datetime.utcnow()
            tzLocal   = pytz.timezone('America/New_York')
            timestamp = tzLocal.localize(utcdate, is_dst=None)
            postDate  = timestamp.strftime('%Y-%m-%dT%H:%M:%S')
            domain    = baseDomain(sourceURL, includeScheme=False)
            postID    = str(uuid.uuid4())
            data      = { 'source':  sourceURL,
                          'target':  targetURL,
                          'created': postDate,
                          'updated': postDate,
                          'postid':  postID,
                          'domain':  domain,
                        }
            event     = { 'type': 'publish',
                          'key':  postID,
                        }

            r = current_app.palala.query('select * from domains where domain = "{domain}"'.format(**data))
            if len(r) > 0:
                current_app.palala.run('update domains set updated = "{updated}" where domain = "{domain}"'.format(domain=domain, updated=postDate))
            else:
                current_app.palala.run('insert into domains (domain, created, updated) values ("{domain}","{created}","{updated}");'.format(domain=domain,created=postDate,updated=postDate))

            current_app.palala.run('insert into posts (postid, domain, source, target, created, updated) values ("{postid}","{domain}","{source}","{target}","{created}","{updated}")'.format(**data))

            current_app.dbRedis.lpush('indienews-recent', postID)
            current_app.dbRedis.ltrim('indienews-recent', 0, 50)
            current_app.dbRedis.rpush('indienews-events', json.dumps(event))

            result = data
            break

    return result
