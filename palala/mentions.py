# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import json
import datetime

from flask import current_app, jsonify

from urlparse import urlparse
from bearlib.tools import baseDomain
# from mf2py.parser import Parser

import pytz
# import ronkyuu


def extractHCard(mf2Data):
    result = { 'name': '',
               'url':  '',
             }
    if 'items' in mf2Data:
        for item in mf2Data['items']:
            if 'type' in item and 'h-card' in item['type']:
                result['name'] = item['properties']['name']
                if 'url' in item['properties']:
                    result['url'] = item['properties']['url']
    return result

def generateSafeName(sourceURL):
    urlData = urlparse(sourceURL)
    result  = '%s_%s.mention' % (urlData.netloc, urlData.path.replace('/', '_'))
    return result

def processVouch(sourceURL, targetURL, vouchDomain):
    """Determine if a vouch domain is valid.
    """
    # result = ronkyuu.vouch(sourceURL, targetURL, vouchDomain, vouchDomains)
    if vouchDomain is None:
        return False
    else:
        return current_app.dbRedis.exists('vouched-%s' % vouchDomain.lower())

def mention(sourceURL, targetURL, vouchDomain=None, vouchRequired=False):
    """Process the Webmention of the targetURL from the sourceURL.
    """
    # mentions = ronkyuu.findMentions(sourceURL)
    vouched  = True
    if vouchRequired:
        vouched = processVouch(sourceURL, targetURL, vouchDomain)

    if vouched:
        utcdate   = datetime.datetime.utcnow()
        tzLocal   = pytz.timezone('America/New_York')
        timestamp = tzLocal.localize(utcdate, is_dst=None)
        domain    = baseDomain(sourceURL, includeScheme=False)
        # mf2Data   = Parser(doc=mentions['content']).to_dict()
        # hcard     = extractHCard(mf2Data)
        data      = { 'sourceURL':   sourceURL,
                      'targetURL':   targetURL,
                      'vouchDomain': vouchDomain,
                      'vouched':     vouched and vouchRequired,
                      'postDate':    timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
                      # 'hcard':       hcard,
                      # 'mf2data':     mf2Data,
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
    else:
        response                     = jsonify(data)
        response.status_code         = 400

    return response
