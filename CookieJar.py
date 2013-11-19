# -*- coding: utf-8 -*-

"""

  Copyright (c) 2013, Jaime Soffer

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
from libeilat import log

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
    return (prefix + suffix)

class CookieJar(QNetworkCookieJar):
    """ Logs and intercepts cookies; part of the Network Access Manager

    """
    def __init__(self, parent=None, allowed=None, storage=None):
        """ Load cookies from a file

        """
        super(CookieJar, self).__init__(parent)
        print "INIT CookieJar"
        if not allowed:
            self.allowed = []
        else:
            self.allowed = allowed
        if storage:
            try:
                with open(storage,"r") as readfile:
                    cookies = [QNetworkCookie.parseCookies(k)
                            for k in readfile.readlines()]
                    cookies = [x for y in cookies for x in y] # flatten
                    self.setAllCookies(cookies)
            except IOError:
                print "LOAD COOKIES: empty?"


    # Reimplemented from PyQt
    # pylint: disable=C0103
    def setCookiesFromUrl(self, cookies, url):
        """ Reimplementation from base class. Prevents cookies from being set
        if not from whitelisted domains.

        """
        if ".".join(unicode(url.host()).split('.')[-2:]) not in self.allowed:
            ret = []
        else:
            ret = cookies
        if ret:
            log(format_cookie(url, ret))
        return QNetworkCookieJar.setCookiesFromUrl(self, ret, url)
    # pylint: enable=C0103
