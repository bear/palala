# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import requests

def urlExists(url):
    """Validate the requested url exists by making a HEAD request for it
    """
    try:
        r = requests.head(url)
        return r.status_code == requests.codes.ok
    except:
        return 404
