# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import json
import datetime

from flask import current_app, jsonify

from bearlib.tools import baseDomain

import pytz
import ronkyuu

def process(sourceURL, targetURL):
    """Publish webmention for sourceURL

    Publishing is handled as a Webmention sent to the /publish URL
    as the targetURL included somewhere within the sourceURL

    All you need is to include the following:
      <a href="https://palala.org/publish"></a>

    somewhere in the sourceURL
    """
    response = None
    mentions = ronkyuu.findMentions(sourceURL)
    for href in mentions['refs']:
        current_app.logger.info('process [%s]' % href)
        if href != sourceURL and href == targetURL:
            utcdate   = datetime.datetime.utcnow()
            tzLocal   = pytz.timezone('America/New_York')
            timestamp = tzLocal.localize(utcdate, is_dst=None)
            postDate  = timestamp.strftime('%Y-%m-%dT%H:%M:%S')
            domain    = baseDomain(sourceURL, includeScheme=False)
            post      = '%s/%s' % (domain, timestamp.strftime('%Y%m%d%H%M%S'))
            data      = { 'sourceURL': sourceURL,
                          'targetURL': targetURL,
                          'created':   postDate,
                          'post':      post,
                        }
            event     = { 'type': 'publish',
                          'key':  post,
                        }

            if not current_app.dbRedis.exists(domain):
                current_app.dbRedis.hset(domain, 'created', postDate)
            current_app.dbRedis.hset(domain, 'updated', postDate)

            for key in data:
                current_app.dbRedis.hset(post, key, data[key])

            current_app.dbRedis.rpush('palala-recent', post)
            current_app.dbRedis.ltrim('palala-recent', 1, 10)
            current_app.dbRedis.rpush('palala-events', json.dumps(event))

            response                     = jsonify(data)
            response.status_code         = 201
            response.headers['location'] = '/posts/%s' % post
            break

    if response is None:
        response = jsonify({ "error": "publish URL cound not be found within target URL"})
        response.status_code = 400

    return response
