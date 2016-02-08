# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import os

_owm_key  = ''
_owm_file = os.path.expanduser('~/.openweathermap.key')

if os.path.exists(_owm_file):
    with open(_owm_file, 'r') as h:
        _owm_key = h.readline().strip()

class Config(object):
    SECRET_KEY     = "bar"
    REDIS_URL      = "redis://127.0.0.1:6379/0"
    KEY_BASE       = ""
    CLIENT_ID      = "https://palala.org"
    AUTH_TIMEOUT   = 300
    VOUCH_REQUIRED = False
    CACHE_TYPE     = "null"
    CACHE_NO_NULL_WARNING = True

class ProdConfig(Config):
    ENV        = 'prod'
    DEBUG      = False
    CACHE_TYPE = 'redis'

class DevConfig(Config):
    ENV   = 'dev'
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

class TestConfig(Config):
    ENV   = 'test'
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    KEY_BASE = "test-"

    CACHE_TYPE = 'null'
    WTF_CSRF_ENABLED = False
