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

from __future__ import unicode_literals

from PyQt4.QtCore import QUrl, Qt
import PyQt4.QtGui as QtGui

import socket
import json

def fix_url(url):
    """ entra string, sale QUrl """
    if not url:
        return QUrl()
    if url.split(':')[0] == "about":
        return QUrl(url)
    search = False
    if url[:4] in ['http', 'file']:
        return QUrl(url)
    else:
        try: # ingenioso pero feo; con 'bind' local es barato
            socket.gethostbyname(url.split('/')[0])
        except (UnicodeEncodeError, socket.error):
            search = True
    if search:
        #return QUrl("http://localhost:8000/?q=%s" % (url.replace(" ", "+")))
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
        ret[unicode(key)] = unicode(value)
    return json.dumps(ret)

def notnull(data):
    """ Do not insert an empty string on the database """
    if not data:
        return None
    else:
        return data

def set_shortcuts(lista):
    """ Creates QShortcuts from a list of (key, owner, callback) 3-tuples

    """
    for (shortcut, owner, callback) in lista:
        QtGui.QShortcut(shortcut, owner, callback).setContext(
                Qt.WidgetWithChildrenShortcut)

def es_url_local(url):
    """ Predicate for create_request
    Is the URL not making an external request?

    """
    return ((url.scheme() in ['data', 'file']) or
            (url.host() == 'localhost'))

def es_font(url):
    """ Predicate for create_request
    Is requesting for a web font?

    """
    return ((url.path()[-3:] == 'ttf') or
            (url.scheme() == 'data' and url.path()[:4] == 'font') or
            (url.path()[-3:] == 'svg' and
                "font" in url.path()))

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
