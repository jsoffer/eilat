#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
minimalistic browser levering off of Python, PyQt and Webkit

Original: https://code.google.com/p/foobrowser/
davydm@gmail.com

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

from __future__ import unicode_literals, print_function

import PyQt4.QtGui as QtGui
from PyQt4.QtNetwork import QNetworkProxy

# local
from InterceptNAM import InterceptNAM
from MainWin import MainWin
from CookieJar import CookieJar
from DatabaseLog import DatabaseLog, DatabaseLogLite

from sys import argv
from os.path import expanduser

def all_urls(tab_widget):
    """
    Prints all the urls held on a tab widget
    """
    for i in range(tab_widget.count()):
        print(tab_widget.widget(i).webkit.url().toString())

def extract_options(site):
    """ Given a site, decide if cookies are allowed, if only some sites
    will not be blocked, etc.

    """

    if site is not None:
        host = site.split('.')[-2]

    if site is None or host not in [
            "facebook", "twitter", "google", "linkedin", "youtube"]:
        print("GENERAL")
        return {
                'use_proxy': True,
                'host_whitelist': None,
                'cookie_allow': [
                    "github.com"],
                'cookie_file': None,
                'prefix': ""}
    elif host == "linkedin":
        print("LINKEDIN")
        return {
                'use_proxy': False,
                'host_whitelist': [
                    "linkedin.com",
                    "licdn.com"
                    ],
                'cookie_allow': ["linkedin.com"],
                'cookie_file': "licookies.cj",
                'prefix': "LI"}
    elif host in ["youtube"]:
        print("YOUTUBE")
        return {
                'use_proxy': False,
                'host_whitelist': [
                    "youtube.com",
                    "ytimg.com"
                    ],
                'cookie_allow': None,
                'cookie_file': None,
                'prefix': "YT"}
    elif host == "facebook":
        print("FACEBOOK")
        return {
                'use_proxy': False,
                'host_whitelist': [
                    "facebook.com",
                    "akamaihd.net",
                    "fbcdn.net"],
                'cookie_allow': ["facebook.com"],
                'cookie_file': "fbcookies.cj",
                'prefix': "FB"}
    elif host == "twitter":
        print("TWITTER")
        return {
                'use_proxy': False,
                'host_whitelist': ["twitter.com", "twimg.com"],
                'cookie_allow': ["twitter.com"],
                'cookie_file': "twcookies.cj",
                'prefix': "TW"}
    elif host == "google":
        print("GOOGLE")
        return {
                'use_proxy': False,
                'host_whitelist': [
                    "google.com",
                    "google.com.mx",
                    "googleusercontent.com",
                    "gstatic.com",
                    "googleapis.com"],
                'cookie_allow': ["google.com"],
                'cookie_file': "gcookies.cj",
                'prefix': "G"}

def main():
    """ Catch the url (if any); then choose adequate defaults and build
    a browser window. Save cookies, if appropiate, at close.

    """

    if len(argv) == 2:
        site = argv[1]
    else:
        site = None

    options = extract_options(site)

    if options['cookie_file'] is not None:
        options['cookie_file'] = (
                expanduser("~/.cookies/") + options['cookie_file'])

    # Proxy
    if options['use_proxy']:
        proxy = QNetworkProxy()
        proxy.setType(QNetworkProxy.HttpProxy)
        proxy.setHostName('localhost')
        proxy.setPort(3128)
        QNetworkProxy.setApplicationProxy(proxy)

    app = QtGui.QApplication([])

    clipboard = app.clipboard()
    db_log = DatabaseLog()

    netmanager = InterceptNAM(
            parent=app, name=options['prefix'],
            log=db_log, whitelist=options['host_whitelist'])

    cookiejar = CookieJar(
            parent=app,
            allowed=options['cookie_allow'],
            storage=options['cookie_file'])
    netmanager.setCookieJar(cookiejar)

    app.setApplicationName("Eilat")
    app.setApplicationVersion("1.3.002")
    mainwin = MainWin(netmanager, clipboard, DatabaseLogLite())

    if site:
        mainwin.add_tab(site)
    else:
        mainwin.add_tab()

    mainwin.show()

    def end_call():
        """ The browser is closing - save cookies, if required.

        """
        print("END")
        all_urls(mainwin.tab_widget)
        if options['cookie_file']:
            print("SAVING COOKIES")
            with open(options['cookie_file'], "w") as savefile:
                for cookie in cookiejar.allCookies():
                    savefile.write(cookie.toRawForm()+"\n")
        else:
            for cookie in cookiejar.allCookies():
                print(cookie.toRawForm()+"\n")

    app.lastWindowClosed.connect(end_call)
    app.exec_()

if __name__ == "__main__":
    main()
