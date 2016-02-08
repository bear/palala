# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

from flask import Blueprint, render_template
from palala.extensions import cache


river = Blueprint('river', __name__)

@river.route('/en')
@cache.cached(timeout=1000)
def river_english():
    return render_template('posts-en.jinja')
