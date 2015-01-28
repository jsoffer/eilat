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

from PyQt5.QtGui import QMouseEvent, QCursor
from PyQt5.QtCore import QUrl, QEvent, Qt
from PyQt5.Qt import QApplication, QShortcut

from urllib.parse import parse_qsl, urlparse

import tldextract

import http

from base64 import encodestring

from eilat.global_store import mainwin


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
            "http://duckduckgo.com/html/?q={}".format(url.replace(" ", "+")))
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
    return ((qurl.path().endswith(('.ttf', '.ico', '.woff', '.otf')) or
             (qurl.scheme() == 'data' and qurl.path().split(';')[0] in [
                 'font/opentype',
                 'application/x-font-ttf',
                 'application/x-font-opentype',
                 'application/font-woff',
                 'application/font-sfnt',
                 'application/vnd.ms-fontobject',
                 'image/svg+xml'  # may not be a font?
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


def encode_blocked(message, url):
    """ Generates a 'data:' string to use as reply when blocking an URL """
    header = b"data:text/html;base64,"
    content = """<html><head></head><body><div class="eilat_blocked"> {}
    <a href={}>{}</a></div></body>""".format(message, url, url)
    encoded = encodestring(content.encode())
    return (header + encoded).decode()


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


def notify(text):
    """ Pushes a notification to the main window's notifier label

    Blueish, big fonts, transparent, in the center of the window;
    always transient

    """

    if not text:
        return

    label = mainwin().tooltip
    label.push_text(text)
    label.adjustSize()

    label.move(mainwin().width() // 2 - label.width() // 2,
               mainwin().height() // 2 - label.height() // 2)

    label.show()

SHORTENERS = [
    "t.co", "bit.ly", "tinyurl.com", "po.st", "buff.ly", "dlvr.it",
    "dailym.ai", "fb.me", "wp.me", "amzn.to", "slate.me", "ht.ly",
    "ow.ly", "j.mp", "met.org", "youtu.be", "tmblr.co", "owl.li"
]

REDIRECTORS = [
    "lm.facebook.com/l.php", "m.facebook.com/l.php", "l.facebook.com/l.php",
    "www.google.com.mx/url"
]


def do_redirect(qurl):
    """ either follow the facebook/google in-url redirect, or retrieve the
    first redirect target not on SHORTENERS for an url

    """

    if qurl.host() + qurl.path() in REDIRECTORS:
        # was 'extract_url'; finds the 'http://...' inside of a
        # "facebook.com/something/q?u=http://something.com/&etc..." form
        query = urlparse(qurl.toString()).query
        for (_, value) in parse_qsl(query):
            if value[:4] == 'http':
                return QUrl(value)

    while qurl.host() in SHORTENERS:
        if qurl.scheme() == "http":
            connection = http.client.HTTPConnection(qurl.host())
        elif qurl.scheme() == "https":
            connection = http.client.HTTPSConnection(qurl.host())
        else:
            raise Exception("bad scheme")
        connection.request("HEAD", qurl.path())
        response = connection.getresponse()
        connection.close()
        # if location is empty, the shortener was the final destination...
        # that case should be handled elsewere since it may only useful to
        # create a shortened link
        location = response.getheader("location")
        print("UNSHORTEN: ", location)
        qurl = QUrl(location)

    return qurl
