# -*- coding: utf-8 -*-

"""

  Copyright (c) 2012, Davyd McColl; 2013, 2014 Jaime Soffer

   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

   Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   Neither the name of the involved organizations nor the names of its
   contributors may be used to endorse or promote products derived from this
   software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
   ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
   LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
   SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
   INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
   CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
   THE POSSIBILITY OF SUCH DAMAGE.

"""

from PyQt4.QtGui import QShortcut, QMouseEvent, QKeyEvent, QCursor
from PyQt4.QtCore import QUrl, QEvent, Qt
from PyQt4.Qt import QApplication

from urllib.parse import parse_qsl, urlparse

import tldextract

from base64 import encodestring

from eilat.global_store import get_manager

def fix_url(url):
    """ Converts an url string to a QUrl object; checks if turning to
    search query is necessary

    No-op if already a QUrl

    """

    if isinstance(url, QUrl):
        return url

    # clean entry; standard case
    if url.strip()[:4] in ['http', 'file']:
        return QUrl(url.strip())

    # empty case
    if not url.strip():
        return QUrl()

    # 'maybe url, maybe not' case
    url = url.rstrip()

    # search if a non-alphanum (including space, that will be stripped) leads;
    # also search if the text has no url structure
    search = (not url[0].isalnum() or
              not ('.' in url) or
              tldextract.extract(url).suffix == '')

    url = url.lstrip()

    if search:
        return QUrl(
            "http://duckduckgo.com/html/?q=%s" % (url.replace(" ", "+")))
    else:
        return QUrl.fromUserInput(url)

def set_shortcuts(lista, context=Qt.WidgetWithChildrenShortcut):
    """ Creates QShortcuts from a list of (key, owner, callback) 3-tuples

    """
    for (shortcut, owner, callback) in lista:
        QShortcut(shortcut, owner, callback).setContext(context)

def is_local(url):
    """ Predicate for create_request
    Is the URL not making an external request?

    """
    return (url.isLocalFile() or
            url.host() == 'localhost' or
            url.scheme() == 'data')

def is_numerical(url):
    """ Predicate for create_request
    Is the URL an already resolved numeric ip address?

    """
    if url in ["192.168.1.254"]:
        return False
    return not ([k for k in url if k not in "0123456789."])

def is_font(qurl):
    """ Predicate for create_request
    Is requesting for a web font? Include icons, too

    """
    return ((qurl.path().endswith(('.ttf', '.ico', '.woff')) or
             (qurl.scheme() == 'data' and qurl.path().split(';')[0] in [
                 'font/opentype',
                 'application/x-font-ttf',
                 'application/x-font-opentype',
                 'application/font-woff',
                 'application/font-sfnt',
                 'application/vnd.ms-fontobject',
                 'image/svg+xml' # may not be a font?
             ]) or
             (qurl.path().endswith('.svg') and "font" in qurl.path())))

def non_whitelisted(whitelist, url):
    """ Predicate for create_request
    If 'whitelist' active, is the URL host listed on it? Allow to pass.
    If 'whitelist' is not active, allow too.

    """

    parsed = tldextract.extract(url.host())
    host = parsed.domain + "." + parsed.suffix
    path = url.path()

    return whitelist and not (
        host in whitelist or
        any([(host + path).startswith(k) for k in whitelist]))

def real_host(url):
    """ Extracts the last not-tld term from the url """
    return tldextract.extract(url).domain

GLOBAL_CSS = b""" :focus > img, a:focus {
outline-color: rgba(160, 160, 255, 0.6) ! important;
outline-width: 10px ! important;
/* outline-offset: 1px ! important; */
outline-style: ridge ! important;
}
* { box-shadow: none ! important; }
"""

_GLOBAL_CSS = b""" * { box-shadow: none ! important; } """

def encode_css(style):
    """ Takes a css as string, returns a proper base64 encoded "file" """
    header = b"data:text/css;charset=utf-8;base64,"
    encoded = encodestring(GLOBAL_CSS + style.encode())
    return (header + encoded).decode()

def encode_blocked(message, url):
    """ Generates a 'data:' string to use as reply when blocking an URL """
    header = b"data:text/html;base64,"
    content = """<html><head></head><body><div class="eilat_blocked"> %s
    <a href=%s>%s</a></div></body>""" % (message, url, url)
    encoded = encodestring(content.encode())
    return (header + encoded).decode()

def extract_url(url):
    """ From string to string.

    Takes a "facebook.com/something/q?u=http://something.com/&etc..." form
    Returns the http://something.com

    python3-only, because of urlparse, parse_qsl; fixable, is it worth it?

    """
    if url is None:
        return

    query = urlparse(url).query
    for (_, value) in parse_qsl(query):
        if value[:4] == 'http':
            return value

# Poor man's symbols (enum would be better - Python 3.4 and up only)
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3

def node_neighborhood(rect, direction):
    """ Finds a rectangle next to the node, where close by
    nodes could be

    """

    if direction == RIGHT:
        rect.translate(rect.width(), rect.height() // 2)
        rect.setWidth(15)
        rect.setHeight(3)
    elif direction == LEFT:
        rect.translate(-15, rect.height() // 2)
        rect.setWidth(15)
        rect.setHeight(3)
    elif direction == DOWN:
        rect.translate(0, rect.height())
        rect.setHeight(15)
    # up
    else:
        rect.translate(0, -15)
        rect.setHeight(15)

    return rect


def fake_key(widget, key):
    """ Generate a fake key click in the widget """
    enter_event = QKeyEvent(
        QEvent.KeyPress, key,
        Qt.KeyboardModifiers())
    QApplication.sendEvent(widget, enter_event)

def fake_click(widget):
    """ Generate a fake mouse click in the cursor position inside 'widget' """
    enter_event = QMouseEvent(
        QEvent.MouseButtonPress,
        widget.mapFromGlobal(QCursor.pos()),
        Qt.LeftButton,
        Qt.MouseButtons(),
        Qt.KeyboardModifiers())

    QApplication.sendEvent(widget, enter_event)

    exit_event = QMouseEvent(
        QEvent.MouseButtonRelease,
        widget.mapFromGlobal(QCursor.pos()),
        Qt.LeftButton,
        Qt.MouseButtons(),
        Qt.KeyboardModifiers())

    QApplication.sendEvent(widget, exit_event)

def toggle_show_logs(prefix, detail=False):
    """ Inverts a value, toggling between printing responses
    that were accepted by the webkit or (some of) those that
    were filtered at some point.

    """

    netmanager = get_manager(prefix())
    if detail:
        netmanager.show_detail ^= True
        if netmanager.show_detail:
            print("---- SHOWING DETAILS ----")
        else:
            print("---- HIDING DETAILS ----")
    else:
        netmanager.show_log ^= True
        if netmanager.show_log:
            print("---- SHOWING LOG ----")
        else:
            print("---- HIDING LOG ----")
