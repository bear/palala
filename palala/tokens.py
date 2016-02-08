# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""


from flask import current_app


def checkAccessToken(access_token=None):
    if access_token is not None:
        key = current_app.dbRedis.get('token-%s' % access_token)
        if key:
            data      = key.split('-')
            me        = data[1]
            client_id = data[2]
            scope     = data[3]
            current_app.logger.info('access token valid [%s] [%s] [%s]' % (me, client_id, scope))
            return me, client_id, scope
    else:
        return None, None, None
