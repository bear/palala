# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

from flask import Blueprint, Response, current_app, render_template, g
from palala.extensions import cache


main = Blueprint('main', __name__)

@main.route('/')
@cache.cached(timeout=1000)
def index():
    return render_template('home.jinja')

@main.route('/static/<path:path>')
def static_proxy(path):
    return main.send_from_directory('static', path)

@main.route('/testing')
def testing():
    return render_template('home.jinja')

@main.route('/posts/<domain>')
def domain(domain):
    """Locate the given domain in our database and
    render an info page for it.
    """
    current_app.logger.info('domain [%s]' % domain)
    g.domain = current_app.palala.domain(domain)
    if g.domain is None:
        return Response('', 404)
    else:
        return render_template('domain.jinja')

@main.route('/posts/<domain>/<postid>')
def domainPosts(domain, postid):
    """Locate the requested domain / postid in our database
    and render an info page for it.
    """
    current_app.logger.info('domain post [%s] [%s]' % (domain, postid))
    g.post = current_app.palala.post(domain, postid)
    if g.post is None:
        return Response('', 404)
    else:
        return render_template('post.jinja')
