# -*- coding: utf-8 -*-

"""

  Copyright (c) 2014 Jaime Soffer

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

from PyQt4.QtCore import QUrl
from PyQt4.QtNetwork import QNetworkReply, QNetworkRequest
from PyQt4.Qt import QClipboard

CLIPBOARD = None
MAINWIN = None
DATABASE = None
MANAGERS = {}

def has_manager(prefix):
    """ Is a network manager registered for this web instance?

    """
    return prefix in MANAGERS.keys()

# intentionally updating (initializing) global constants
# pylint: disable=W0603
def register_manager(prefix, manager):
    """ Make a web instance specific network access manager globally
    accessible

    """
    #global MANAGERS

    if not prefix in MANAGERS.keys():
        MANAGERS[prefix] = manager
# pylint: enable=W0603

def get_manager(prefix):
    """ Retrieve the network access manager for 'prefix' web instance

    """
    return MANAGERS[prefix]

def close_managers():
    """ Do cleanup on all the cookie jars """

    for prefix in MANAGERS:
        MANAGERS[prefix].cookie_jar.store_cookies()

# intentionally updating (initializing) global constants
# pylint: disable=W0603
def export_database(datab):
    """ Initialize the application; give global access to the clipboard """

    global DATABASE

    if DATABASE is None:
        DATABASE = datab
    else:
        raise RuntimeError("Attempting to initialize database twice")
# pylint: enable=W0603

def database():
    """ global access """
    return DATABASE

# intentionally updating (initializing) global constants
# pylint: disable=W0603



def export_clipboard(clipb):
    """ Initialize the application; give global access to the clipboard """

    global CLIPBOARD

    if CLIPBOARD is None:
        CLIPBOARD = clipb
    else:
        raise RuntimeError("Attempting to initialize main window twice")
# pylint: enable=W0603


# intentionally updating (initializing) global constants
# pylint: disable=W0603
def export_mainwin(win):
    """ Copy an initialized mainwin so it will be globally accessible

    """
    global MAINWIN

    if MAINWIN is None:
        MAINWIN = win
    else:
        raise RuntimeError("Attempting to initialize main window twice")
# pylint: enable=W0603

def mainwin():
    """ Access the main window globally (fixable after passing 'options' in
    a more sane way than through the window; imprement "add tab" directly")

    """
    return MAINWIN

def clipboard(request=None):
    """ Globally handle PRIMARY clipboard's contents

    Write the requested download to the PRIMARY clipboard,
    so it can be easily pasted with middle click (or shift+insert,
    or xsel, or xclip, or 'Y' keybinding) anywhere it's needed

    Accepting a callable is required because binding the function to
    a QLineEdit.text() will bind forever to the content of the line edit
    at bind time, but a binding to QLineEdit.text will be evaluated
    when the shortcut is called
    """

    if request is not None:
        if isinstance(request, str):
            string_to_copy = request
        elif isinstance(request, QUrl):
            string_to_copy = request.toString()
        elif (isinstance(request, QNetworkRequest) or
              isinstance(request, QNetworkReply)):
            string_to_copy = request.url().toString()
        elif callable(request):
            string_to_copy = request()
        else:
            raise RuntimeError("Attempt to store non-text on clipboard")

        CLIPBOARD.setText(string_to_copy,
                          mode=QClipboard.Selection)
    else:
        return CLIPBOARD.text(mode=QClipboard.Selection).strip()
