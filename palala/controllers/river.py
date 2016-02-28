# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

from flask import Blueprint, render_template, current_app, g
from palala.extensions import cache


river = Blueprint('river', __name__)

@river.route('/en')
@cache.cached(timeout=1000)
def river_english():
    g.posts = current_app.palala.current()
    return render_template('posts-en.jinja')
