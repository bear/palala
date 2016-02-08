# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

from flask import Blueprint, current_app, request, Response
from palala.tools import urlExists
from palala.publish import post


wm = Blueprint('webmention', __name__)

@wm.route('/webmention', methods=['GET', 'POST'])
def webmention():
    if request.method == 'POST':
        source = request.form.get('source')
        target = request.form.get('target')
        vouch  = request.form.get('vouch')

        current_app.logger.info('[%s] [%s]' % (source, target))

        if urlExists(target):
            return post(source, target)
        else:
            return Response('invalid post', 404)
    else:
        return Response('method not allowed', 405)
