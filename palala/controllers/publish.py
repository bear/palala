# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

from flask import Blueprint, current_app, request, render_template
from palala.publish import process
from palala.mentions import mention


pub = Blueprint('publish', __name__)

@pub.route('/publish', methods=['GET', 'POST'])
def publish():
    if request.method == 'POST':
        source = request.form.get('source')
        target = request.form.get('target')
        # vouch  = request.form.get('vouch')

        current_app.logger.info('publish [%s] [%s]' % (source, target))

        return process(source, target)
    else:
        return render_template('publish.jinja')

@pub.route('/webmention', methods=['POST'])
def webmention():
    if request.method == 'POST':
        source = request.form.get('source')
        target = request.form.get('target')
        # vouch  = request.form.get('vouch')

        current_app.logger.info('webmention [%s] [%s]' % (source, target))

        if '/publish' in target:
            return process(source, target)
        else:
            return mention(source, target)
