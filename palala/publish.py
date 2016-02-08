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


def post(sourceURL, targetURL):
    """Post the sourceURL

    Publishing is handled as a Webmention of our /publish URL
    as the targetURL included somewhere within the sourceURL
    """
    response = None
    mentions = ronkyuu.findMentions(sourceURL)
    for href in mentions['refs']:
        current_app.logger.info('[%s]' % href)
        if href != sourceURL and href == targetURL:
            utcdate   = datetime.datetime.utcnow()
            tzLocal   = pytz.timezone('America/New_York')
            timestamp = tzLocal.localize(utcdate, is_dst=None)
            domain    = baseDomain(sourceURL, includeScheme=False)
            data      = { 'sourceURL':   sourceURL,
                          'targetURL':   targetURL,
                          'postDate':    timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
                        }
            key       = '%s/%s' % (domain, timestamp.strftime('%Y%m%d%H%M%S'))
            event     = { 'type': 'webmention',
                          'key':  key,
                        }

            current_app.dbRedis.set(key, json.dumps(data))
            current_app.dbRedis.rpush('palala-events', json.dumps(event))

            response                     = jsonify(data)
            response.status_code         = 201
            response.headers['location'] = '/posts/%s' % key
            break

    if response is None:
        response = jsonify({ "error": "publish URL cound not be found within target URL"})
        response.status_code = 400

    return response
