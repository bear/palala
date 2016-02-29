#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import os

from palala import create_app

env = os.environ.get('INDIENEWS_ENV', 'dev')
application = create_app('palala.settings.%sConfig' % env.capitalize())

if __name__ == "__main__":
    application.run()
