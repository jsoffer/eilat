# -*- coding: utf-8 -*-

"""

  Copyright (c) 2012, Davyd McColl; 2013, Jaime Soffer

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
from PyQt4.QtCore import QUrl

import socket

def log(text):
    """ Trivial wrap over print

    """
    print(text)

def register_shortcuts(actions, default_owner):
    """ Takes lists of [fun, key, (opt) owner, description], creates
    QShortCuts

    """
    for action in actions:
        shortcut = actions[action][1]
        if shortcut.lower() == "none":
            continue
        # allow multiple shortcuts with keys delimited by |
        shortcuts = shortcut.split("|")
        for shortcut in shortcuts:
            shortcut = shortcut.strip()
            if shortcut == "":
                continue
            callback = actions[action][0]
            if len(actions[action]) == 2:
                owner = default_owner
            else:
                if type(actions[action][2]) != str:
                    owner = actions[action][2]
                elif len(actions[action]) == 4:
                    owner = actions[action][3]
                else:
                    owner = default_owner
            QShortcut(shortcut, owner, callback)

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
        except socket.error:
            search = True
    if search:
        return QUrl("http://localhost:8000/?q=%s" % (url.replace(" ", "+")))
    else:
        return QUrl.fromUserInput(url)
