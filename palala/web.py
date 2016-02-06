# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import json

class Palala():
    def __init__(self, api_key, keyBase, dbRedis):
        self.db      = dbRedis
        self.keyRoot = '%spalala-' % keyBase

    def clear(self, location):
        key = '%s%s' % (self.keyRoot, location)
        self.db.delete(key)

    def load(self, location):
        """Given a location, return any cached value

        location: string
        returns:  dictionary
        """
        key   = '%s%s' % (self.keyRoot, location)
        value = self.db.get(key)

        if value is not None:
            return json.loads(value)

    def save(self, location, value, expires=300):
        """Save the weather dictionary for the given location

        location: string
        value: dictionary
        """
        key = '%s%s' % (self.keyRoot, location)
        self.db.set(key, json.dumps(value))
        self.db.expire(key, expires)

    def get(self, location):
        """Get the current weather for the given location

        location: string
        returns:  dictionary
        """
        w = self.load(location)
        if w is None:
            w = self.OpenWeatherMap(location)
            self.save(location, w)
        return w
