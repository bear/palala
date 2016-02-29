# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

from flask import current_app


class IndieNews():
    def __init__(self, keyBase):
        self.keyRoot = '%sindienews-' % keyBase

    # execute the query
    def query(self, sql, args=()):
        cur  = current_app.dbStore.cursor()
        cur.execute(sql, args)
        rows = [dict(r) for r in cur.fetchall()]
        return rows

    # execute the query
    # return either a single dictionary item or a list of rows
    def run(self, sql):
        cur = current_app.dbStore.cursor()
        cur.execute(sql)
        current_app.dbStore.commit()

    def domain(self, domain):
        d = { 'domain':    domain,
              'created':   None,
              'updated':   None,
              'postCount': 0,
              'posts':     [],
            }
        r = self.query('select * from domains where domain = "{domain}"'.format(domain=domain))
        if len(r) > 0:
            d['created']   = r[0]['created']
            d['updated']   = r[0]['updated']
            d['posts']     = self.query('select * from posts where domain = "{domain}"'.format(domain=domain))
            d['postCount'] = len(d['posts'])
        return d

    def post(self, domain, postid):
        current_app.logger.info('post info [%s][%s]' % (domain, postid))
        d = { 'domain':  domain,
              'postid':  postid,
              'created': None,
              'updated': None,
              'source':  None,
              'target':  None
            }
        r = self.query('select * from domains where domain = "{domain}"'.format(domain=domain))
        if len(r) > 0:
            d['created'] = r[0]['created']
            d['updated'] = r[0]['updated']
            p = self.query('select * from posts where postid = "{postid}"'.format(postid=postid))
            d['source'] = p[0]['source']
            d['target'] = p[0]['target']
        return d

    def current(self):
        posts = []
        l     = current_app.dbRedis.lrange('indienews-recent', 0, -1)
        current_app.logger.info('pulling current items %d' % len(l))
        for postid in l:
            current_app.logger.info('post {postid}'.format(postid=postid))
            p = self.query('select * from posts where postid = "{postid}"'.format(postid=postid))
            current_app.logger.info('%d' % len(p))
            d = {}
            for key in p[0].keys():
                d[key] = p[0][key]
            print d
            posts.append(d)
        current_app.logger.info('%d items found' % len(posts))
        return posts