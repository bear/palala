# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

from flask import current_app


class Palala():
    def __init__(self, keyBase):
        self.keyRoot = '%spalala-' % keyBase

    def domain(self, domain):
        if current_app.dbRedis.exists(domain):
            d              = current_app.dbRedis.hgetall(domain)
            d['domain']    = domain
            d['posts']     = current_app.dbRedis.keys('%s/*' % domain)
            d['postCount'] = len(d['posts'])
            return d
        else:
            return None

    def post(self, domain, postid):
        key = '%s/%s' % (domain, postid)
        current_app.logger.info('post info [%s]' % key)
        if current_app.dbRedis.exists(key):
            return current_app.dbRedis.hgetall(key)
        else:
            return None

    def current(self):
        posts = []
        l     = current_app.dbRedis.lrange('palala-recent', 0, -1)
        current_app.logger.info('pulling current items %s' % len(l))
        for key in l:
            current_app.logger.info('%s %s' % (current_app.dbRedis.exists(key), key))
            if current_app.dbRedis.exists(key):
                posts.append(current_app.dbRedis.hgetall(key))
        current_app.logger.info('%d items found' % len(posts))
        return posts