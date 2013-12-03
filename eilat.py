#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
minimalistic browser levering off of Python, PyQt and Webkit

Original: https://code.google.com/p/foobrowser/
davydm@gmail.com

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

import PyQt4.QtGui as QtGui
from PyQt4.QtNetwork import QNetworkProxy

# local
from InterceptNAM import InterceptNAM
from MainWin import MainWin
from CookieJar import CookieJar
from DatabaseLog import DatabaseLog

from libeilat import set_shortcuts

from sys import argv

def main():
    """ Catch the url (if any); then choose adequate defaults and build
    a browser window. Save cookies, if appropiate, at close.

    """

    # Considerations:
    # Will use proxy? (if not google, fb, twitter... then yes)
    use_proxy = True
    # Which whitelist will use instead?
    host_whitelist = None
    # Will allow cookies? Which? Where are they saved?
    cookie_allow = ["github.com", "linkedin.com", "freerepublic.com"]
    cookie_file = None

    if len(argv) == 2:
        sitio = argv[1]
        if (sitio.split('.')[-2:] == ["facebook","com"]):
            print "FACEBOOK"
            use_proxy = False
            host_whitelist = ["facebook.com", "akamaihd.net", "fbcdn.net"]
            cookie_allow = ["facebook.com"]
            cookie_file = "fbcookies.cj"
        elif (sitio.split('.')[-2:] == ["twitter","com"]):
            print "TWITTER"
            use_proxy = False
            host_whitelist = ["twitter.com", "twimg.com"]
            cookie_allow = ["twitter.com"]
            cookie_file = "twcookies.cj"
        elif (sitio.split('.')[-2:] == ["google","com"]):
            print "GOOGLE"
            use_proxy = False
            host_whitelist = [
                    "google.com",
                    "google.com.mx",
                    "googleusercontent.com",
                    "gstatic.com",
                    "googleapis.com"]
            cookie_allow = ["google.com"]
            cookie_file = "gcookies.cj"
        else:
            print "GENERAL"
    else:
        sitio = None
        print "EMPTY"

    # Proxy
    if use_proxy:
        proxy = QNetworkProxy()
        proxy.setType(QNetworkProxy.HttpProxy)
        proxy.setHostName('localhost')
        proxy.setPort(3128)
        QNetworkProxy.setApplicationProxy(proxy)


    app = QtGui.QApplication([])


    clipboard = app.clipboard()
    db_log = DatabaseLog()
    netmanager = InterceptNAM(
            parent = app, log = db_log, whitelist = host_whitelist)
    cookiejar = CookieJar(
            parent = app, allowed = cookie_allow, storage = cookie_file)
    netmanager.setCookieJar(cookiejar)

    app.setApplicationName("Eilat")
    app.setApplicationVersion("1.2.001")
    mainwin = MainWin(netmanager, clipboard)

    mainwin.show()

    if sitio:
        mainwin.add_tab(sitio)
    else:
        mainwin.add_tab()

    def end_call():
        """ The browser is closing - save cookies, if required.

        """
        print "END"
        if cookie_file:
            print "SAVING COOKIES"
            with open(cookie_file, "w") as savefile:
                for cookie in cookiejar.allCookies():
                    savefile.write(cookie.toRawForm()+"\n")

    app.lastWindowClosed.connect(end_call)
    app.exec_()

if __name__ == "__main__":
    main()
