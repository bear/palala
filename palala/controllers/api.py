# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

from flask import Blueprint, Response, current_app, jsonify
from flask_restful import Resource, Api


api     = Blueprint('api', __name__)
restApi = Api(api)


class PostList(Resource):
    def get(self):
        return Response('', 200)

class Domains(Resource):
    def get(self, domain):
        d = current_app.palala.domain(domain)
        if d is None:
            r             = jsonify({ 'error': '%s not found' % domain})
            r.status_code = 200
        else:
            r             = jsonify(d)
            r.status_code = 200
        return r

class Posts(Resource):
    def get(self, domain, postid):
        post = current_app.palala.post(domain, postid)
        if post is None:
            r             = jsonify({ 'error': '%s/%s not found' % (domain, postid)})
            r.status_code = 200
        else:
            r             = jsonify(post)
            r.status_code = 200
        return r

restApi.add_resource(PostList, '/v1/posts')
restApi.add_resource(Domains,  '/v1/posts/<domain>')
restApi.add_resource(Posts,    '/v1/posts/<domain>/<postid>')
