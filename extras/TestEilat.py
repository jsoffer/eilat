#!/usr/bin/env python3.4dm
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

# to keep some support of python2
import sip
sip.setapi('QString', 2)

import unittest
from PyQt4.QtTest import QTest

from PyQt4.QtCore import Qt
from PyQt4.QtNetwork import QNetworkProxy
from PyQt4.Qt import QApplication

# local
from MainWin import MainWin

from sys import argv
from os.path import expanduser
from re import sub

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
        host = sub("^https?://", "", site).split('/')[0].split('.')[-2]

    private_instances = [
            "facebook", "twitter", "google", "linkedin", "youtube"]

    if site is None or host not in private_instances:
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

APP = QApplication([])
APP.setApplicationName("Eilat")
APP.setApplicationVersion("1.3.002")

CLIPBOARD = APP.clipboard()

class TestEilat(unittest.TestCase):

    def setUp(self):
        if len(argv) == 2:
            site = argv[1]
        else:
            site = None

        options = extract_options(site)

        if options['cookie_file'] is not None:
            options['cookie_file'] = (
                    expanduser("~/.eilat/cookies/") + options['cookie_file'])

        # Proxy
        if options['use_proxy']:
            proxy = QNetworkProxy()
            proxy.setType(QNetworkProxy.HttpProxy)
            proxy.setHostName('localhost')
            proxy.setPort(3128)
            QNetworkProxy.setApplicationProxy(proxy)

        self.mainwin = MainWin(clipboard=CLIPBOARD, options=options, parent=None)

        if site:
            self.mainwin.add_tab(site)
        else:
            self.mainwin.add_tab()

        self.mainwin.show()

    def testExists(self):
        self.assertIsNotNone(APP)
        #APP.close()

    def testEnterUrl(self):
        webtab = self.mainwin.tab_widget.currentWidget()
        #QTest.keyClicks(webtab.webkit, "LA", Qt.ControlModifier)
        QTest.keyClicks(webtab.address_bar, "http://theospark.net")
        QTest.keyClick(webtab.address_bar, "J", Qt.ControlModifier)
        #QTest.keyClick(webtab.address_bar, Qt.Key_Return)
        self.assertEqual(webtab.address_bar.text(), "http://theospark.net")

if __name__ == "__main__":
    unittest.main()
