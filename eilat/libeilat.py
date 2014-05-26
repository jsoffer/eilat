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

from PyQt4.QtGui import QShortcut
from PyQt4.QtCore import QUrl, Qt
from PyQt4.Qt import QClipboard
from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply

import json

# to keep some support of python2
try:
    from urllib.parse import parse_qsl, urlparse
except ImportError:
    from urlparse import parse_qsl, urlparse

from base64 import encodestring
from subprocess import Popen, PIPE

from threading import Thread

def fix_url(url):
    """ entra string, sale QUrl """

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
              not url.split('/')[0].split('.')[-1] in TLDS)

    url = url.lstrip()

    if search:
        return QUrl(
            "http://duckduckgo.com/html/?q=%s" % (url.replace(" ", "+")))
    else:
        return QUrl.fromUserInput(url)

def filtra(keyvalues):
    """ Converts a [(key,value)] list of cookies first to a dictionary
    and then to JSON. Single quotes are NOT escaped (the escape happens
    when passing the string as second argument to .execute in psycopg)

    """
    if not keyvalues:
        return None
    ret = {}
    for (key, value) in keyvalues:
        ret[key] = value
    return json.dumps(ret)

def notnull(data):
    """ Do not insert an empty string on the database """
    if not data:
        return None
    else:
        return data

def set_shortcuts(lista, context=Qt.WidgetWithChildrenShortcut):
    """ Creates QShortcuts from a list of (key, owner, callback) 3-tuples

    """
    for (shortcut, owner, callback) in lista:
        QShortcut(shortcut, owner, callback).setContext(context)

def es_url_local(url):
    """ Predicate for create_request
    Is the URL not making an external request?

    """
    return (url.isLocalFile() or
            url.host() == 'localhost' or
            url.scheme() == 'data')

def es_num_ip(url):
    """ Predicate for create_request
    Is the URL an already resolved numeric ip address?

    """
    if url in ["192.168.1.254"]:
        return False
    return not ([k for k in url if k not in "0123456789."])

def es_font(url):
    """ Predicate for create_request
    Is requesting for a web font? Include icons, too

    """
    return ((url.path()[-4:] == '.ttf') or
            (url.path()[-4:] == '.ico') or
            (url.path()[-5:] == '.woff') or
            (url.scheme() == 'data' and url.path()[:4] == 'font') or
            (url.scheme() == 'data' and
             url.path()[:22] == 'application/x-font-ttf') or
            (url.scheme() == 'data' and
             url.path()[:21] == 'application/font-woff') or
            (url.path()[-4:] == '.svg' and "font" in url.path()))

def usando_whitelist(whitelist, url):
    """ Predicate for create_request
    If 'whitelist' active, is the URL host listed on it? Allow to pass.
    If 'whitelist' is not active, allow too.

    """
    return (whitelist and
            (not any(
                [url.host()[-len(k):] == k
                 for k in whitelist])))

TLDS = ["ac", "academy", "ad", "ae", "aero", "af", "ag", "ai", "al", "am", "an",
        "ao", "aq", "ar", "arpa", "as", "asia", "at", "au", "aw", "ax", "az",
        "ba", "bb", "bd", "be", "bf", "bg", "bh", "bi", "bike", "biz", "bj",
        "bm", "bn", "bo", "br", "bs", "bt", "bv", "bw", "by", "bz", "ca", "cab",
        "camera", "camp", "careers", "cat", "cc", "cd", "center", "cf", "cg",
        "ch", "ci", "ck", "cl", "clothing", "cm", "cn", "co", "com", "company",
        "computer", "construction", "contractors", "coop", "cr", "cu", "cv",
        "cw", "cx", "cy", "cz", "de", "diamonds", "directory", "dj", "dk", "dm",
        "do", "domains", "dz", "ec", "edu", "ee", "eg", "enterprises",
        "equipment", "er", "es", "estate", "et", "eu", "fi", "fj", "fk", "fm",
        "fo", "fr", "ga", "gallery", "gb", "gd", "ge", "gf", "gg", "gh", "gi",
        "gl", "gm", "gn", "gov", "gp", "gq", "gr", "graphics", "gs", "gt", "gu",
        "guru", "gw", "gy", "hk", "hm", "hn", "holdings", "hr", "ht", "hu",
        "id", "ie", "il", "im", "in", "info", "int", "io", "iq", "ir", "is",
        "it", "je", "jm", "jo", "jobs", "jp", "ke", "kg", "kh", "ki", "kitchen",
        "km", "kn", "kp", "kr", "kw", "ky", "kz", "la", "land", "lb", "lc",
        "li", "lighting", "limo", "lk", "lr", "ls", "lt", "lu", "lv", "ly",
        "ma", "management", "mc", "md", "me", "menu", "mg", "mh", "mil", "mk",
        "ml", "mm", "mn", "mo", "mobi", "mp", "mq", "mr", "ms", "mt", "mu",
        "museum", "mv", "mw", "mx", "my", "mz", "na", "name", "nc", "ne", "net",
        "nf", "ng", "ni", "nl", "no", "np", "nr", "nu", "nz", "om", "org", "pa",
        "pe", "pf", "pg", "ph", "photography", "photos", "pk", "pl", "plumbing",
        "pm", "pn", "post", "pr", "pro", "ps", "pt", "pw", "py", "qa", "re",
        "recipes", "ro", "rs", "ru", "ruhr", "rw", "sa", "sb", "sc", "sd", "se",
        "sexy", "sg", "sh", "shoes", "si", "singles", "sj", "sk", "sl", "sm",
        "sn", "so", "sr", "st", "su", "sv", "sx", "sy", "systems", "sz",
        "tattoo", "tc", "td", "technology", "tel", "tf", "tg", "th", "tips",
        "tj", "tk", "tl", "tm", "tn", "to", "today", "tp", "tr", "travel", "tt",
        "tv", "tw", "tz", "ua", "ug", "uk", "uno", "us", "uy", "uz", "va", "vc",
        "ve", "ventures", "vg", "vi", "viajes", "vn", "voyage", "vu", "wf",
        "ws", "xn--3e0b707e", "xn--45brj9c", "xn--55qw42g", "xn--80ao21a",
        "xn--80asehdb", "xn--80aswg", "xn--90a3ac", "xn--clchc0ea0b2g2a9gcd",
        "xn--fiqs8s", "xn--fiqz9s", "xn--fpcrj9c3d", "xn--fzc2c9e2c",
        "xn--gecrj9c", "xn--h2brj9c", "xn--j1amh", "xn--j6w193g", "xn--kprw13d",
        "xn--kpry57d", "xn--l1acc", "xn--lgbbat1ad8j", "xn--mgb9awbf",
        "xn--mgba3a4f16a", "xn--mgbaam7a8h", "xn--mgbayh7gpa", "xn--mgbbh1a71e",
        "xn--mgbc0a9azcg", "xn--mgberp4a5d4ar", "xn--mgbx4cd0ab",
        "xn--ngbc5azd", "xn--o3cw4h", "xn--ogbpf8fl", "xn--p1ai", "xn--pgbs0dh",
        "xn--q9jyb4c", "xn--s9brj9c", "xn--unup4y", "xn--wgbh1c", "xn--wgbl6a",
        "xn--xkc2al3hye2a", "xn--xkc2dl3a5ee0h", "xn--yfro4i67o",
        "xn--ygbi2ammx", "xn--zfr164b", "xxx", "ye", "yt", "za", "zm", "zw"]

def real_host(url):
    """ Extracts the last not-tld term from the url """
    return [i for i in url.split('.') if i not in TLDS][-1]

GLOBAL_CSS = b""" *:focus { border: #00a 1px solid ! important; }
* { box-shadow: none ! important; }
/* * { position: inherit ! important ; } */
"""

def encode_css(style):
    """ Takes a css as string, returns a proper base64 encoded "file" """
    header = b"data:text/css;charset=utf-8;base64,"
    content = encodestring(GLOBAL_CSS + style.encode())
    return (header + content).decode()

def user_agent_for_url(*args):
    """ Returns a User Agent that will be seen by the website.
    The loose array for arguments is because this function is used to
    replace a class method. The only justification is that 'self' will not
    be used. May not be a sane idea.

    """

    if real_host(args[1].host()) in ['whatsmyuseragent']:
        user_agent = (
            "Mozilla/5.0 (X11; FreeBSD amd64; rv:27.0) " +
            "(Hello WIMUA) " +
            "Gecko/20100101 Firefox/27.0")
    else:
        user_agent = (
            "Mozilla/5.0 (X11; FreeBSD amd64; rv:27.0) " +
            "Gecko/20100101 Firefox/27.0")

    return user_agent

def copy_to_clipboard(clipboard, request):
    """ Write the requested download to the PRIMARY clipboard,
    so it can be easily pasted with middle click (or shift+insert,
    or xsel, or xclip, or 'Y' keybinding) anywhere it's needed


    """

    if isinstance(request, QUrl):
        qstring_to_copy = request.toString()
    elif (isinstance(request, QNetworkRequest) or
          isinstance(request, QNetworkReply)):
        qstring_to_copy = request.url().toString()
    elif callable(request):
        qstring_to_copy = request()

    print("CLIPBOARD: " + qstring_to_copy)
    clipboard.setText(qstring_to_copy, mode=QClipboard.Selection)

def osd(message, corner=False):
    """ Call the external program osd_cat from a non-blocking thread """

    params_color = ['-cblack', '-uwhite', '-O3']
    params_font = ['-f-*-*-*-*-*-*-20-*-*-*-*-*-*-*']
    params_time = ['-d8000']

    if corner:
        params_position = ['-ptop', '-Aright']
    else:
        params_position = ['-pmiddle', '-Acenter']

    def call_osd():
        """ As a lambda it would be too long """
        try:
            Popen(['osd_cat_', '-l2'] +
                  params_position +
                  params_color +
                  params_font +
                  params_time,
                  stdin=PIPE).communicate(input=message.encode())
        except FileNotFoundError:
            print("OSD not available - install osd_cat from xosd")
            print("OSD Message was: " + message)

    Thread(target=call_osd).start()

def extract_url(url):
    """ From string to string.

    Takes a "facebook.com/something/q?u=http://something.com/&etc..." form
    Returns the http://something.com

    """
    if url is None:
        return

    query = urlparse(url).query
    for (_, value) in parse_qsl(query):
        if value[:4] == 'http':
            return value
