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

from PyQt4.QtGui import QApplication
from PyQt4.QtNetwork import QNetworkProxy

# local
from InterceptNAM import InterceptNAM
from MainWin import MainWin
from CookieJar import CookieJar

from sys import argv

def atEnd():
    print "CLOSE"

if __name__ == "__main__":

    # Considerations:
    # Will use proxy? (if not google, fb, twitter... then yes)
    USE_PROXY = True
    # Which whitelist will use instead?
    WHITELIST = None
    # Will allow cookies? Which? Where are they saved?
    COOKIE_ALLOW = ["github.com", "linkedin.com"]
    COOKIE_FILE = None

    if len(argv) == 2:
        SITIO = argv[1]
        if (SITIO.split('.')[-2:] == ["facebook","com"]):
            print "FACEBOOK"
            USE_PROXY = False
            WHITELIST = ["facebook.com", "akamaihd.net", "fbcdn.net"]
            COOKIE_ALLOW = ["facebook.com"]
            COOKIE_FILE = "fbcookies.cj"
        elif (SITIO.split('.')[-2:] == ["twitter","com"]):
            print "TWITTER"
            USE_PROXY = False
            WHITELIST = ["twitter.com", "twimg.com"]
            COOKIE_ALLOW = ["twitter.com"]
            COOKIE_FILE = "twcookies.cj"
        elif (SITIO.split('.')[-2:] == ["google","com"]):
            print "GOOGLE"
            USE_PROXY = False
            WHITELIST = [
                    "google.com",
                    "google.com.mx",
                    "googleusercontent.com",
                    "gstatic.com",
                    "googleapis.com"]
            COOKIE_ALLOW = ["google.com"]
            COOKIE_FILE = "gcookies.cj"
        else:
            print "GENERAL"
    else:
        SITIO = None
        print "EMPTY"

    # Proxy
    if USE_PROXY:
        proxy = QNetworkProxy()
        proxy.setType(QNetworkProxy.HttpProxy)
        proxy.setHostName('localhost')
        proxy.setPort(3128)
        QNetworkProxy.setApplicationProxy(proxy)

    app = QApplication([])

    cb = app.clipboard()
    netmanager = InterceptNAM(whitelist = WHITELIST)
    cookiejar = CookieJar(allowed = COOKIE_ALLOW, storage = COOKIE_FILE)
    netmanager.setCookieJar(cookiejar)

    app.setApplicationName("Eilat")
    app.setApplicationVersion("1.002")
    mainwin = MainWin(netmanager, cb)
    mainwin.show()

    if SITIO:
        mainwin.addTab(SITIO)
    else:
        mainwin.addTab()

    def endCall():
        print "END"
        if COOKIE_FILE:
            print "SAVING COOKIES"
            fh = open(COOKIE_FILE,"w")
            for cookie in cookiejar.allCookies():
                fh.write(cookie.toRawForm()+"\n")
            fh.flush()
            fh.close()
    app.lastWindowClosed.connect(endCall)
    app.exec_()
