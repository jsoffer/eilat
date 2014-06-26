# -*- coding: utf-8 -*-

"""

  Copyright (c) 2013, 2014 Jaime Soffer

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

from PyQt4.QtNetwork import QNetworkCookieJar, QNetworkCookie
from os.path import expanduser

from tldextract import extract

def format_cookie(url, cookies):
    """ Constructs a log message from a list of cookies and the host
    where they're set

    """
    prefix = "\n< COOKIES (%s%s) " % (url.host(), url.path())
    suffix = ", ".join(["[[%s%s] %s => %s]" %
                        (cookie.domain(),
                         cookie.path(),
                         cookie.name(),
                         cookie.value())
                        for cookie in cookies])
    return prefix + suffix

class CookieJar(QNetworkCookieJar):
    """ Logs and intercepts cookies; part of the Network Access Manager

    """
    def __init__(self, parent=None, options=None):
        """ Load cookies from a file

        """
        super(CookieJar, self).__init__(parent)
        print("INIT CookieJar")

        if options['cookie_allow'] is None:
            self.allowed = []
        else:
            self.allowed = options['cookie_allow']

        self.storage = options['cookie_file']
        if self.storage is not None:
            self.storage = expanduser("~/.eilat/cookies/") + self.storage
            print(self.storage)
            try:
                with open(self.storage, "r") as readfile:
                    cookies = [QNetworkCookie.parseCookies(k)
                               for k in readfile.readlines()]
                    cookies = [x for y in cookies for x in y] # flatten
                    self.setAllCookies(cookies)
            except IOError:
                print("LOAD COOKIES: empty?")

    def store_cookies(self):
        """ Saves all cookies to 'storage'; called from the NAM when it
        sends a 'deleted' signal

        """

        if self.storage is not None:
            print("Store cookies...")
            with open(self.storage, "w") as savefile:
                for cookie in self.allCookies():
                    savefile.write(cookie.toRawForm().data().decode()+"\n")

    def set_cookies_from_url(self, cookies, url):
        """ Reimplementation from base class. Prevents cookies from being set
        if not from whitelisted domains.

        """
        (_, domain, suffix) = extract(url.host())
        site = domain + '.' + suffix

        if site not in self.allowed:
            print("COOKIE FROM %s not set" % (url.toString()))
            ret = []
        else:
            print("SET COOKIE FROM %s" % (url.toString()))
            ret = cookies

        return QNetworkCookieJar.setCookiesFromUrl(self, ret, url)

    # Clean reimplement for Qt
    # pylint: disable=C0103
    setCookiesFromUrl = set_cookies_from_url
    # pylint: enable=C0103
