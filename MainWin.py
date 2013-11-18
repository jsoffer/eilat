# -*- coding: utf-8 -*-

"""

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

from PyQt4.Qt import QClipboard
from PyQt4.QtGui import QMainWindow, QTabWidget

# local
from WebTab import WebTab
from libeilat import registerShortcuts

#from signal import signal, SIGUSR1

class MainWin(QMainWindow):
  """ Esta ventana guarda las tabs """
  def __init__(self, netmanager, cb):
    QMainWindow.__init__(self, None)
    self.netmanager = netmanager
    self.cb = cb
    self.downloader = None
    self.actions = dict()
    self.tabactions = dict()
    self.tabactions = dict()
    self.registerActions()
    self.showStatusBar = False
    self.appname = "Eilat Browser"
    self.maxTitleLen = 40

    self.mkGui()
    registerShortcuts(self.actions, self)
    #signal(SIGUSR1, self.stopJavascript)

  # run (en constructor)
  def mkGui(self):
    self.setWindowTitle(self.appname)
    self.tabWidget = QTabWidget(self)
    self.tabWidget.tabBar().setMovable(True)
    self.setCentralWidget(self.tabWidget)
    self.tabWidget.setTabsClosable(True)

    self.tabWidget.tabCloseRequested.connect(self.delTab)

  def registerActions(self):
    self.actions["newtab"]    = [self.addTab,       "Ctrl+T", "Open new tab"]
    self.actions["paste"] = [lambda: self.addTab(unicode(self.cb.text(QClipboard.Selection)).strip()), "Y", "Access to clipboard"]
    self.actions["closetab"]  = [self.delTab,       "Ctrl+W", "Close current tab"]
    self.actions["tabprev"]   = [lambda: self.incTab(-1),       "N|Ctrl+PgUp", "Switch to previous tab"]
    self.actions["tabnext"]   = [self.incTab,       "M|Ctrl+PgDown", "Switch to next tab"]
    self.actions["close"]     = [self.close,        "Ctrl+Q", "Close application"]

  # aux. action (en registerActions)
  def incTab(self, incby = 1):
    """ Va a la tab siguiente """
    if self.tabWidget.count() < 2:
      return
    idx = self.tabWidget.currentIndex()
    idx += incby
    if idx < 0:
      idx = self.tabWidget.count()-1;
    elif idx >= self.tabWidget.count():
      idx = 0
    self.tabWidget.setCurrentIndex(idx)

  # action y connect en llamada en constructor
  def delTab(self, idx = None):
    if not idx:
      idx = self.tabWidget.currentIndex()
    self.tabWidget.widget(idx).webkit.stop()
    self.tabWidget.widget(idx).deleteLater()
    self.tabWidget.removeTab(idx)
    if len(self.tabWidget) == 0:
      self.close()

  # action (en registerActions)
  # externo en eilat.py, crea la primera tab
  def addTab(self, url = None):
    tab = WebTab(browser=self, actions=self.tabactions, netmanager=self.netmanager)
    self.tabWidget.addTab(tab, "New tab")
    self.tabWidget.setCurrentWidget(tab)
    if url:
      tab.navigate(url)

  # Implemented, it's recognized and runs at close
  def closeEvent(self, e):
    print "MainWin.closeEvent"
    e.accept()
    self.close()
