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

import sip
sip.setapi('QString',2)

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QTimer
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
  use_proxy = True
  # Which whitelist will use instead?
  hosts_whitelist = None
  # Will allow cookies? Which? Where are they saved?
  cookies_allowed = ["github.com", "linkedin.com"]
  cookies_storage = None

  if len(argv) == 2:
      sitio = argv[1]
      if (sitio.split('.')[-2:] == ["facebook","com"]):
          print "FACEBOOK"
          use_proxy = False
          hosts_whitelist = ["facebook.com", "akamaihd.net", "fbcdn.net"]
          cookies_allowed = ["facebook.com"]
          cookies_storage = "fbcookies.cj"
      elif (sitio.split('.')[-2:] == ["twitter","com"]):
          print "TWITTER"
          use_proxy = False
          hosts_whitelist = ["twitter.com", "twimg.com"]
          cookies_allowed = ["twitter.com"]
          cookies_storage = "twcookies.cj"
      elif (sitio.split('.')[-2:] == ["google","com"]):
          print "GOOGLE"
          use_proxy = False
          hosts_whitelist = ["google.com","google.com.mx","googleusercontent.com","gstatic.com","googleapis.com"]
          cookies_allowed = ["google.com"]
          cookies_storage = "gcookies.cj"
      else:
          print "GENERAL"
  else:
      sitio = None
      print "EMPTY"

  # Proxy
  if use_proxy:
      proxy = QNetworkProxy()
      proxy.setType(QNetworkProxy.HttpProxy)
      proxy.setHostName('localhost');
      proxy.setPort(3128)
      QNetworkProxy.setApplicationProxy(proxy);

  app = QApplication([])

  # This timer allows catching signals even if the app is inactive
  # timer = QTimer()
  # timer.start(5000)
  # timer.timeout.connect(lambda: None)

  cb = app.clipboard()
  netmanager = InterceptNAM(whitelist = hosts_whitelist)
  cookiejar = CookieJar(allowed = cookies_allowed, storage = cookies_storage)
  netmanager.setCookieJar(cookiejar)

  app.setApplicationName("Eilat")
  app.setApplicationVersion("1.001")
  mainwin = MainWin(netmanager, cb)
  mainwin.show()

  if sitio:
      mainwin.addTab(sitio)
  else:
      mainwin.addTab()

  def endCall():
      print "END"
      if cookies_storage:
          print "SAVING COOKIES"
          fh = open(cookies_storage,"w")
          for cookie in cookiejar.allCookies():
              fh.write(cookie.toRawForm()+"\n")
          fh.flush()
          fh.close()
  app.lastWindowClosed.connect(endCall)
  app.exec_()
