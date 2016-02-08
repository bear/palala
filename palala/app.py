# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import json
from flask import current_app


class Palala():
    def __init__(self, keyBase):
        self.keyRoot = '%spalala-' % keyBase

    def domain(self, domain):
        if current_app.dbRedis.exists(domain):
            return json.loads(current_app.dbRedis.get(domain))
        else:
            return None

    def post(self, domain, postid):
        key = '%s/%s' % (domain, postid)
        if current_app.dbRedis.exists(key):
            return json.loads(current_app.dbRedis.get(key))
        else:
            return None
