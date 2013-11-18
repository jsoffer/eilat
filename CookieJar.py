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

class CookieJar(QNetworkCookieJar):
    def __init__(self, parent=None, allowed = [], storage=None):
        super(CookieJar, self).__init__(parent)
        print "INIT CookieJar"
        self.allowed = allowed
        if storage:
            try:
                fh = open(storage,"r")
                cookies = map(lambda k: QNetworkCookie.parseCookies(k), fh.readlines())
                cookies = [x for y in cookies for x in y]
                #print unicode(cookies)
                self.setAllCookies(cookies)
            except Exception as e:
                print e
                print "\nCOOKIES: empty?"

    def setCookiesFromUrl(self,cookies,url):
        if ".".join(url.host().split('.')[-2:]) not in self.allowed:
            ret = []
        else:
            ret = cookies
        if ret:
            print "\n< COOKIES " + url.host() + url.path() + ": " + ", ".join(map(lambda k: "["+unicode(k.domain())+unicode(k.path())+"]" + unicode(k.name()) + " => " + unicode(k.value()), ret))
        return QNetworkCookieJar.setCookiesFromUrl(self,ret,url)
    def cookiesForUrl(self,url):
        ret = QNetworkCookieJar.cookiesForUrl(self,url)
        #if ret:
            #print "> COOKIES " + unicode(map(lambda k: k.toRawForm(), ret))
        #    print "> COOKIES " + url.host() + url.path() + ": " + ", ".join(map(lambda k: "["+unicode(k.domain())+unicode(k.path())+"]" + unicode(k.name()) + " => " + unicode(k.value()), ret))
        return ret
