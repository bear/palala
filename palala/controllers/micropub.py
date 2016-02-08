# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import uuid
import urllib

from flask import Blueprint, current_app, request
from palala.tokens import checkAccessToken

import requests
import ninka


mp = Blueprint('micropub', __name__)


@mp.route('/token', methods=['POST', 'GET'])
def handleToken():
    current_app.logger.info('handleToken [%s]' % request.method)

    if request.method == 'GET':
        access_token = request.headers.get('Authorization')
        if access_token:
            access_token = access_token.replace('Bearer ', '')
        else:
            access_token
        me, client_id, scope = checkAccessToken(access_token)

        if me is None or client_id is None:
            return ('Token is not valid', 400, {})
        else:
            params = { 'me':        me,
                       'client_id': client_id,
                     }
            if scope is not None:
                params['scope'] = scope
            return (urllib.urlencode(params), 200, {'Content-Type': 'application/x-www-form-urlencoded'})

    elif request.method == 'POST':
        code         = request.form.get('code')
        me           = request.form.get('me')
        redirect_uri = request.form.get('redirect_uri')
        client_id    = request.form.get('client_id')
        state        = request.form.get('state')

        current_app.logger.info('    code         [%s]' % code)
        current_app.logger.info('    me           [%s]' % me)
        current_app.logger.info('    client_id    [%s]' % client_id)
        current_app.logger.info('    state        [%s]' % state)
        current_app.logger.info('    redirect_uri [%s]' % redirect_uri)

        r = ninka.indieauth.validateAuthCode(code=code,
                                             client_id=me,
                                             state=state,
                                             redirect_uri=redirect_uri)
        if r['status'] == requests.codes.ok:
            current_app.logger.info('token request auth code verified')
            scope = r['response']['scope']
            key   = 'app-%s-%s-%s' % (me, client_id, scope)
            token = current_app.dbRedis.get(key)
            if token is None:
                token     = str(uuid.uuid4())
                token_key = 'token-%s' % token
                current_app.dbRedis.set(key, token)
                current_app.dbRedis.set(token_key, key)

            current_app.logger.info('  token generated for [%s] : [%s]' % (key, token))
            params = { 'me': me,
                       'scope': scope,
                       'access_token': token
                     }
            return (urllib.urlencode(params), 200, {'Content-Type': 'application/x-www-form-urlencoded'})
