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

if __name__ == "__main__":
  app = QApplication([])

  # This timer allows catching signals even if the app is inactive
  timer = QTimer()
  timer.start(5000)
  timer.timeout.connect(lambda: None)

  cb = app.clipboard()
  netmanager = InterceptNAM()
  cookiejar = CookieJar()
  netmanager.setCookieJar(cookiejar)

  app.setApplicationName("Eilat")
  app.setApplicationVersion("0.001")
  mainwin = MainWin(netmanager, cb)
  mainwin.show()
  for arg in argv[1:]:
    if arg not in ["-debug"]:
      mainwin.load(arg)
  app.exec_()
