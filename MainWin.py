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
    self.tabs = []
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

  #def stopJavascript(self, p, q):
  #  log("STOPPING JAVASCRIPT GLOBALLY")
  #  for t in self.tabs:
  #    t.stopScript()

  #def toggleStatusVisiblity(self):
  #  """ Muestra/oculta status bar. Afecta a todas las tabs """
  #  self.showStatusBar = not self.showStatusBar
  #  for t in self.tabs:
  #    t.setStatusVisibility(self.showStatusBar)

  def registerActions(self):
    self.actions["newtab"]    = [self.addTab,       "Ctrl+T", "Open new tab"]
    self.actions["paste"] = [lambda: self.addTab(unicode(self.cb.text(QClipboard.Selection)).strip()), "Y", "Access to clipboard"]
    self.actions["closetab"]  = [self.delTab,       "Ctrl+W", "Close current tab"]
    self.actions["tabprev"]   = [lambda: self.incTab(-1),       "N|Ctrl+PgUp", "Switch to previous tab"]
    self.actions["tabnext"]   = [self.incTab,       "M|Ctrl+PgDown", "Switch to next tab"]
    self.actions["go"]        = [self.focusAddress, "Ctrl+L", "Focus address bar"]
    self.actions["close"]     = [self.close,        "Ctrl+Q", "Close application"]
    self.actions["zoomin"]    = [lambda: self.zoom(1),   "Ctrl+Up", "Zoom into page"]
    self.actions["zoomout"]   = [lambda: self.zoom(-1),  "Ctrl+Down", "Zoom out of page"]

  # aux. action (en registerActions)
  def zoom(self, lvl):
    self.tabs[self.tabWidget.currentIndex()].zoom(lvl)

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

  # action (en registerActions)
  def focusAddress(self):
    self.tabs[self.tabWidget.currentIndex()].cmb.setFocus()

  # action y connect en llamada en constructor
  def delTab(self, idx = -1):
    if idx >= len(self.tabs):
      return
    if idx == -1:
      idx = self.tabWidget.currentIndex()
    t = self.tabs.pop(idx)
    t.webkit.stop()
    self.tabWidget.removeTab(idx)
    t.deleteLater()
    if len(self.tabs) == 0:
      self.close()
    else:
      self.focusWeb()

  # action (en registerActions)
  # externo en eilat.py, crea la primera tab
  def addTab(self, url = None):
    tab = WebTab(browser=self, actions=self.tabactions, netmanager=self.netmanager)
    self.tabWidget.addTab(tab, "New tab")
    self.tabs.append(tab)
    self.tabWidget.setCurrentWidget(tab)
    if url:
      tab.navigate(url)
      self.focusWeb()
    else:
      self.focusAddress()
    #return self.tabs[self.tabWidget.currentIndex()]

  def focusWeb(self):
    self.tabs[self.tabWidget.currentIndex()].webkit.setFocus()

  # Implemented, it's recognized and runs at close
  def closeEvent(self, e):
    print "MainWin.closeEvent"
    e.accept()
    self.close()
