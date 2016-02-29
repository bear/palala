# -*- coding: utf-8 -*-
"""
:copyright: (c) 2009-2016 by Mike Taylor
:license: CC0 1.0 Universal, see LICENSE for more details.
"""

import os

_cwd = os.path.dirname(os.path.abspath(__file__))

class Config(object):
    SECRET_KEY     = "bar"
    REDIS_URL      = "redis://127.0.0.1:6379/0"
    STORE_DB       = os.path.join(_cwd, "..", "indienews.db")
    KEY_BASE       = ""
    CLIENT_ID      = "https://indieweb.news"
    AUTH_TIMEOUT   = 300
    VOUCH_REQUIRED = False
    CACHE_TYPE     = "null"
    CACHE_NO_NULL_WARNING = True

class ProdConfig(Config):
    ENV        = 'prod'
    DEBUG      = False
    CACHE_TYPE = 'redis'
    REDIS_URL  = "redis://127.0.0.1:6379/4"
    STORE_DB   = "/home/indienews/indienews.db"

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
