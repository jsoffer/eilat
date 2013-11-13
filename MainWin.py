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

from PyQt4.QtGui import QMainWindow, QTabWidget

# local
from WebTab import WebTab
from libeilat import registerShortcuts

from signal import signal, alarm, SIGUSR1
from socket import gethostbyname

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
    signal(SIGUSR1, self.stopJavascript)

  def stopJavascript(self, p, q):
    log("STOPPING JAVASCRIPT GLOBALLY")
    for t in self.tabs:
      t.stopScript()

  def toggleStatusVisiblity(self):
    """ Muestra/oculta status bar. Afecta a todas las tabs """
    self.showStatusBar = not self.showStatusBar
    for t in self.tabs:
      t.setStatusVisibility(self.showStatusBar)

  def registerActions(self):
    self.actions["newtab"]    = [self.addTab,       "Ctrl+T", "Open new tab"]
    self.actions["closetab"]  = [self.delTab,       "Ctrl+W", "Close current tab"]
    self.actions["tabprev"]   = [self.decTab,       "N|Ctrl+PgUp", "Switch to previous tab"]
    self.actions["tabnext"]   = [self.incTab,       "M|Ctrl+PgDown", "Switch to next tab"]
    self.actions["go"]        = [self.focusAddress, "Ctrl+L", "Focus address bar"]
    self.actions["close"]     = [self.close,        "Ctrl+Q", "Close application"]
    self.actions["zoomin"]    = [self.zoomIn,       "Ctrl+Up", "Zoom into page"]
    self.actions["zoomout"]   = [self.zoomOut,      "Ctrl+Down", "Zoom out of page"]

  def focusAddress(self):
    self.tabs[self.tabWidget.currentIndex()].cmb.setFocus()

  def focusWeb(self):
    self.tabs[self.tabWidget.currentIndex()].webkit.setFocus()

  def zoomIn(self):
    self.zoom(1)
  def zoomOut(self):
    self.zoom(-1)

  def zoom(self, lvl):
    self.tabs[self.tabWidget.currentIndex()].zoom(lvl)

  def decTab(self):
    """ Va a la tab anterior """
    self.incTab(-1)

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

  def setTabTitle(self, tab, title):
    idx = self.getTabIndex(tab)
    if idx > -1:
      if len(title) > self.maxTitleLen:
        title = title[:self.maxTitleLen-3] + "..."
      self.tabWidget.setTabText(idx, title)

  def getTabIndex(self, tab):
    for i in range(len(self.tabs)):
      if tab == self.tabs[i]:
        return i
    return -1

  def closeEvent(self, e):
    e.accept()
    self.close()

  def mkGui(self):
    self.setWindowTitle(self.appname)
    self.tabWidget = QTabWidget(self)
    self.tabWidget.tabBar().setMovable(True)
    self.setCentralWidget(self.tabWidget)
    self.tabWidget.setTabsClosable(True)

    self.tabWidget.tabCloseRequested.connect(self.delTab)
    self.addTab()

  def addTab(self, url = None):
    tab = WebTab(browser=self, actions=self.tabactions, netmanager=self.netmanager, clipboard=self.cb, showStatusBar = self.showStatusBar)
    self.tabWidget.addTab(tab, "New tab")
    self.tabs.append(tab)
    self.tabWidget.setCurrentWidget(tab)
    if url:
      tab.navigate(url)
      self.focusWeb()
    else:
      self.focusAddress()
    return self.tabs[self.tabWidget.currentIndex()]

  def fixUrl(self, url): # FIXME
    # look for "smart" search
    if url.split(':')[0] == "about":
        return url
    search = False
    if url[:4] == 'http':
      return url
    else:
      try:
        gethostbyname(url.split('/')[0]) # ingenioso pero feo; con 'bind' local es barato
      except Exception as e:
        search = True
    if search:
      return "http://localhost:8000/?q=%s" % (url.replace(" ", "+"))
    else:
      return "http://" + url

  def delTab(self, idx = -1):
    if idx >= len(self.tabs):
      return
    if idx == -1:
      idx = self.tabWidget.currentIndex()
    t = self.tabs.pop(idx)
    t.stop()
    self.tabWidget.removeTab(idx)
    t.deleteLater()
    if len(self.tabs) == 0:
      self.close()
    else:
      self.focusWeb()

  def load(self, url):
    if self.tabs[-1].URL() == "":
      self.tabs[-1].navigate(url)
    else:
      self.addTab(url)

