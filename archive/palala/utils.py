#!/usr/bin/env python

__author__       = "Mike Taylor (bear@code-bear.com)"
__copyright__    = "Copyright 2009-2010, Mike Taylor"
__license__      = "Apache v2"
__version__      = "0.1"
__contributors__ = []

"""
Palala internal helper classes and routines
"""

import os, sys
import types
import logging
import traceback

from xml.etree import cElementTree as ET
from xml.sax.saxutils import escape, quoteattr

log = logging.getLogger()


def dumpException(msg):
    """
    Gather information on the current exception stack and log it
    """
    t, v, tb = sys.exc_info()
    s        = '%s\n%s\n' % (msg, ''.join(traceback.format_exception(t, v, tb)))
    if log is None:
        print s
    else:
        log.exception(s)

def tostring(xml, xmlns='', stringbuffer='', namespace_map={}, root=True, cdata=()):
    newoutput = [stringbuffer]
    itag = xml.tag.split('}', 1)[-1]
    if '}' in xml.tag:
        ixmlns = xml.tag.split('}', 1)[0][1:]
    else:
        ixmlns = ''
    nsbuffer = ''
    if xmlns != ixmlns and ixmlns != '':
        if ixmlns in namespace_map:
            if namespace_map[ixmlns] != '':
                itag = "%s:%s" % (namespace_map[ixmlns], itag)
        else:
            nsbuffer = """ xmlns="%s\"""" % ixmlns
    newoutput.append("<%s" % itag)
    newoutput.append(nsbuffer)
    for attrib in xml.attrib:
        newoutput.append(""" %s="%s\"""" % (attrib, escXML(xml.attrib[attrib])))
    if root:
        for namespace in namespace_map:
            newoutput.append(""" xmlns:%s="%s\"""" % (namespace_map[namespace], namespace))
    if len(xml):
        newoutput.append(">")
        for child in xml.getchildren():
            newoutput.append(tostring(child, ixmlns, namespace_map=namespace_map, root=False, cdata=cdata))
        newoutput.append("</%s>" % (itag, ))
    elif xml.text:
        if itag in cdata:
            newoutput.append("><![CDATA[%s]]></%s>" % (xml.text, itag))
        else:
            newoutput.append(">%s</%s>" % (escXML(xml.text), itag))
    else:
        newoutput.append(" />")
    return ''.join(newoutput)

def escXML(text, escape_quotes=False):
    if type(text) != types.UnicodeType:
        if type(text) == types.IntType:
            s = str(text)
        else:
            s = text
        s = list(unicode(s, 'utf-8', 'ignore'))
    else:
        s = list(text)

    cc      = 0
    matches = ('&', '<', '"', '>')

    for c in s:
        if c in matches:
            if c == '&':
                s[cc] = u'&amp;'
            elif c == '<':
                s[cc] = u'&lt;'
            elif c == '>':
                s[cc] = u'&gt;'
            elif escape_quotes:
                s[cc] = u'&quot;'
        cc += 1
    return ''.join(s)

def handle_sigterm(signum, frame):
    log.info('handling SIGTERM [%s]' % _daemon.pidfile)

    if _daemon.pidfile is not None:
        try:
            os.remove(_daemon.pidfile)
        except (KeyboardInterrupt, SystemExit):
            dumpException('KI, SE trapped during PID removal')
            raise
        except Exception:
            dumpException('Exception trapped during PID removal')

    raise Exception('stopping')

