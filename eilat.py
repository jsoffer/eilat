#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
minimalistic browser levering off of Python, PyQt and Webkit

Original: https://code.google.com/p/foobrowser/
davydm@gmail.com

+ tabs
+ descargar con click derecho + menú: requiere auxiliar

+ proxy
+ actualizar dirección al cambiar de página
+ ctrl-l: address bar
+ ctrl-q: salir
+ dirección destino, [title], ¿status bar?
+ ^J como Enter en address bar
+ zoom
+ buscar en página
+ detecta si es búsqueda o completa el http://
+ movimiento con jk (falta hl)
+ paste (y visita sitio) con 'y'
+ verifica no tráfico no solicitado

Pendiente:

* navegación con teclado
* historia en address bar
* ^H en address bar es backspace

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

from PyQt4 import Qt, QtGui, QtCore, QtWebKit, QtNetwork
import os
import sys
import socket

# clipboard; global, feo pero parece apropiado (es global a todo el sistema)
cb = None

# trivial; FIXME
def log(s):
    print(s)

def registerShortcuts(actions, defaultOwner):
  for action in actions:
    """ Las acciones son ??? """ # FIXME
    shortcut = actions[action][1]
    if shortcut.lower() == "none":
      continue
# allow multiple shortcuts with keys delimited by |
    shortcuts = shortcut.split("|")
    for shortcut in shortcuts:
      shortcut = shortcut.strip()
      if shortcut == "":
        continue
      callback = actions[action][0]
      if len(actions[action]) == 2:
        owner = defaultOwner
      else:
        if type(actions[action][2]) != str:
          owner = actions[action][2]
        elif len(actions[action]) == 4:
          owner = actions[action][3]
        else:
          owner = defaultOwner
      QtGui.QShortcut(shortcut, owner, callback)

class WebView(QtWebKit.QWebView):
  """ Una página web con contenedor, para poner en una tab """
  def __init__(self, parent = None):
    self.parent = parent
    self.paste = False
    QtWebKit.QWebView.__init__(self, parent)
  def mousePressEvent(self, event):
      self.paste = (event.buttons() & QtCore.Qt.MiddleButton)
      return QtWebKit.QWebView.mousePressEvent(self,event)
  def createWindow(self, type):
    return self.parent.browser.addTab().webkit

class WebTab(QtGui.QWidget):
  """ Cada tab contiene una página web """
  def __init__(self, browser, actions=None, parent=None, showStatusBar=False):
    QtGui.QWidget.__init__(self, parent)
    self.actions = dict()

    self.browser = browser

    # layout
    self.grid = QtGui.QGridLayout(self)
    self.grid.setSpacing(0)
    self.grid.setVerticalSpacing(0)
    self.grid.setContentsMargins(0,0,0,0)

    # webkit: la parte que entra a internet
    # aquí se configura, cada tab tiene opciones independientes
    self.webkit = WebView(self)
    self.webkit.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
    self.webkit.linkClicked.connect(self.onLinkClick)
    self.webkit.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled,False)
    self.webkit.settings().setAttribute(QtWebKit.QWebSettings.JavascriptEnabled,False)
    #self.webkit.settings().setAttribute(QtWebKit.QWebSettings.SpatialNavigationEnabled,True)
    #self.webkit.settings().setAttribute(QtWebKit.QWebSettings.DeveloperExtrasEnabled,True)
    #self.webkit.setSizePolicy()

    # address bar
    self.cmb = QtGui.QComboBox()
    self.cmb.setEditable(True)

    # progress bar
    self.pbar = QtGui.QProgressBar()
    self.pbar.setRange(0, 100)
    self.pbar.setTextVisible(False)
    self.pbar.setVisible(False)
    self.pbar.setMaximumHeight(7)

    # buscar en página (frame+layout)
    self.fraSearch = QtGui.QFrame()
    self.searchGrid = QtGui.QGridLayout(self.fraSearch)
    self.searchGrid.setSpacing(0)
    self.searchGrid.setContentsMargins(0,0,0,0)
    self.lblSearch = QtGui.QLabel("Find in page:")
    self.txtSearch = QtGui.QLineEdit()
    self.searchGrid.addWidget(self.lblSearch, 0,0)
    self.searchGrid.addWidget(self.txtSearch, 0,1)
    self.fraSearch.setVisible(False)

    self.statusbar = QtGui.QStatusBar()
    self.statusbar.setVisible(showStatusBar)
    self.statusbar.setMaximumHeight(25)

    self.grid.addWidget(self.webkit, 0, 0)
    self.grid.setRowStretch(0, 1)
    self.grid.addWidget(self.fraSearch, 1, 0)
    self.grid.addWidget(self.cmb, 2, 0)
    self.grid.addWidget(self.pbar, 3, 0)
    self.grid.addWidget(self.statusbar, 4, 0)

    # cuando se selecciona una opción del combobox dropdown
    self.connect(self.cmb, QtCore.SIGNAL("currentIndexChanged(int)"), self.navigate)

    self.connect(self.webkit, QtCore.SIGNAL("loadStarted()"), self.loadStarted)
    self.connect(self.webkit, QtCore.SIGNAL("loadFinished(bool)"), self.loadFinished)
    self.connect(self.webkit, QtCore.SIGNAL("titleChanged(QString)"), self.setTitle)
    self.connect(self.webkit, QtCore.SIGNAL("loadProgress(int)"), self.loadProgress)
    self.connect(self.webkit, QtCore.SIGNAL("urlChanged(QUrl)"), self.setURL)
    self.connect(self.webkit.page(), QtCore.SIGNAL("linkHovered(QString, QString, QString)"), self.onLinkHovered)

    # el contenido de la tab (los datos, no el contenedor)
    page = self.webkit.page()
    page.downloadRequested.connect(self.onDownloadRequested)
    page.setForwardUnsupportedContent(True)
    page.unsupportedContent.connect(self.onUnsupportedContent)
    self.connect(self.txtSearch, QtCore.SIGNAL("textChanged(QString)"), self.doSearch)

    self.registerActions()
    registerShortcuts(self.actions, self)
    self.cmb.setFocus()
    self.showHideMessage()

    # reemplazar el Network Access Manager para saber qué contenido está pidiendo
    self.netmanager = InterceptNAM(app)
    page.setNetworkAccessManager(self.netmanager);

  def onLinkClick(self, qurl):
    self.navigate(qurl.toString(), self.webkit.paste)

  def registerActions(self):
    self.actions["addressnav"]  = [self.navigate, "Ctrl+J|Enter", self.cmb, "Navigate to the url in the address bar"]
    self.actions["reload"]      = [self.reload, "F5|R", "Reload the current page"]
    self.actions["back"]        = [self.back, "Alt+Left", "Go back in history"]
    self.actions["fwd"]         = [self.fwd, "Alt+Right", "Go forward in history"]
    self.actions["smartsearch"] = [self.smartSearch, "G", "Smart search (find next or start search)"]
    self.actions["stopsearch"]  = [self.stopOrHideSearch, "Escape", self.fraSearch, "Stop current load or searching"]
    self.actions["findnext"]    = [self.doSearch, "Return", self.txtSearch, "Next match for current search"]
    self.actions["togglestatus"]= [self.toggleStatus, "Ctrl+Space", "Toggle visibility of status bar"]
    # el scroll debería ser el mismo de apretar flecha arriba / flecha abajo
    self.actions["scrolldown"] = [lambda: self.webkit.page().mainFrame().scroll(0,40), "J", "Scrolls down"]
    self.actions["scrollup"] = [lambda: self.webkit.page().mainFrame().scroll(0,-40), "K", "Scrolls down"]
    self.actions["paste"] = [lambda: self.navigate(str(cb.text(Qt.QClipboard.Selection)).strip()), "Y", "Access to clipboard"]
    self.actions["togglejs"] = [self.toggleScript, "Q", "Switches javascript on/off"]

  def toggleScript(self):
    """ Activa o desactiva javascript, y notifica cambiando el color del address bar """
    if self.webkit.settings().testAttribute(QtWebKit.QWebSettings.JavascriptEnabled):
        self.webkit.settings().setAttribute(QtWebKit.QWebSettings.JavascriptEnabled,False)
        self.cmb.setStyleSheet("QComboBox { background-color: #fff; }")
    else:
        self.webkit.settings().setAttribute(QtWebKit.QWebSettings.JavascriptEnabled,True)
        self.cmb.setStyleSheet("QComboBox { background-color: #ddf; }")

  def toggleStatus(self):
    if self.browser:
      self.browser.toggleStatusVisiblity()
    else:
      self.statusbar.setVisible(not self.statusBar.isVisible())

  # toggleStatusVisibility
  def setStatusVisibility(self, visible):
    self.statusbar.setVisible(visible)

  # conexión
  def onUnsupportedContent(self, reply):
    log("Unsupported content %s" % (reply.url().toString()))

  # conexión
  def onDownloadRequested(self, request):
    log("Download Request: " + str(request.url()))

  # múltiples llamadas - reestructurar
  def doSearch(self, s = None):
    if s is None: s = self.txtSearch.text()
    self.webkit.findText(s, QtWebKit.QWebPage.FindWrapsAroundDocument)

  def stopOrHideSearch(self):
    if self.fraSearch.isVisible():
      self.fraSearch.setVisible(False)
      self.webkit.setFocus()
    else:
      self.webkit.stop()

  def showSearch(self):
    self.txtSearch.setText("")
    self.fraSearch.setVisible(True)
    self.txtSearch.setFocus()

  # usado en zoom in, zoom out
  def zoom(self, lvl):
    self.webkit.setZoomFactor(self.webkit.zoomFactor() + (lvl * 0.25))

  def stop(self):
    self.webkit.stop()

  # usado en load, refresh
  def URL(self):
    return self.cmb.currentText()

  # conexión
  def loadProgress(self, val):
    if self.pbar.isVisible():
      self.pbar.setValue(val)

  def setTitle(self, title):
    if self.browser:
      self.browser.setTabTitle(self, title)

  def setURL(self, url):
    self.cmb.setEditText(url.toString())

  def refresh(self):
    self.navigate(self.URL())
    self.webkit.reload()

  def loadStarted(self):
    self.showProgressBar()

  def loadFinished(self, success):
    self.hideProgressBar()
    if self.cmb.hasFocus():
      self.webkit.setFocus()

  def showProgressBar(self):
    self.pbar.setValue(0)
    self.pbar.setVisible(True)

  def hideProgressBar(self, success = False):
    self.pbar.setVisible(False)

  def reload(self):
    self.webkit.reload()

  def smartSearch(self):
    if self.fraSearch.isVisible():
      self.doSearch()
    else:
      self.showSearch()

  def fwd(self):
    self.webkit.history().forward()

  def back(self):
    self.webkit.history().back()

  def navigate(self, url = None, newtab = False):
    if newtab:
        self.browser.addTab(url)
    else:
        # 'not url' para keybinding; 'int' para sin http:// ???
        if not url or type(url) == int: url = str(self.cmb.currentText()) # ??? TODO
        url = QtCore.QUrl(self.browser.fixUrl(url))
        self.setTitle("Loading...")
        self.webkit.load(url)

  def onStatusBarMessage(self, s):
    if s:
      self.statusbar.showMessage(s)
    else:
      self.showHideMessage()

  def showHideMessage(self):
    self.statusbar.showMessage("(press %s to hide this)" % (self.actions["togglestatus"][1]))

  def onLinkHovered(self, link, title, content):
    if link or title:
      if title and not link:
        self.statusbar.showMessage(title)
      elif link and not title:
        self.statusbar.showMessage(link)
      elif link and title:
        self.statusbar.showMessage("%s (%s)" % (title, link))
    else:
      self.showHideMessage()

class MainWin(QtGui.QMainWindow):
  """ Esta ventana guarda las tabs """
  def __init__(self):
    QtGui.QMainWindow.__init__(self, None)
    self.downloader = None
    self.actions = dict()
    self.tabactions = dict()
    self.tabactions = dict()
    tmp = WebTab(None, None)
    self.tabactions = tmp.actions
    self.registerActions()
    self.showStatusBar = False
    self.appname = "Eilat Browser"
    self.tabs = []
    self.maxTitleLen = 40

    tmp.deleteLater()
    self.mkGui()
    registerShortcuts(self.actions, self)

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
    self.actions["go"]        = [self.currentTabGo, "Ctrl+L", "Focus address bar"]
    self.actions["close"]     = [self.close,        "Ctrl+Q", "Close application"]
    self.actions["zoomin"]    = [self.zoomIn,       "Ctrl+Up", "Zoom into page"]
    self.actions["zoomout"]   = [self.zoomOut,      "Ctrl+Down", "Zoom out of page"]

  def currentTabGo(self):
    self.tabs[self.tabWidget.currentIndex()].cmb.setFocus()

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
    self.tabWidget = QtGui.QTabWidget(self)
    self.tabWidget.tabBar().setMovable(True)
    self.setCentralWidget(self.tabWidget)
    self.tabWidget.setTabsClosable(True)

    self.connect(self.tabWidget, QtCore.SIGNAL("tabCloseRequested(int)"), self.delTab)
    self.connect(self, QtCore.SIGNAL("refreshAll()"), self.refreshAll)
    self.addTab()

  def addTab(self, url = None):
    tab = WebTab(browser=self, actions=self.tabactions, showStatusBar = self.showStatusBar)
    self.tabWidget.addTab(tab, "New tab")
    self.tabs.append(tab)
    self.tabWidget.setCurrentWidget(tab)
    if url:
      tab.navigate(url)
    else:
      self.currentTabGo()
    return self.tabs[self.tabWidget.currentIndex()]

  def fixUrl(self, url): # FIXME
    # look for "smart" search
    search = False
    if url[:4] == 'http':
      return url
    else:
      try:
        socket.gethostbyname(url.split('/')[0]) # ingenioso pero feo; con 'bind' local es barato
      except Exception as e:
        #print e
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

  def load(self, url):
    if self.tabs[-1].URL() == "":
      self.tabs[-1].navigate(url)
    else:
      self.addTab(url)

  def refreshAll(self):
    for t in self.tabs:
      t.refresh()

class InterceptNAM(QtNetwork.QNetworkAccessManager):
    def createRequest(self, operation, request, data):
        try:
            url = request.url().toString()
            if url[:4] == "data":
                print "<-- " + url[:72]
            else:
                print "<<< " + url
        except:
            print "[unicode on address... browser bug, FIXME]"
        return QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, data)

if __name__ == "__main__":
  # Proxy
  proxy = QtNetwork.QNetworkProxy()
  proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
  proxy.setHostName('localhost');
  proxy.setPort(3128)
  QtNetwork.QNetworkProxy.setApplicationProxy(proxy);

  app = QtGui.QApplication([])
  cb = app.clipboard()

  app.setApplicationName("Eilat")
  app.setApplicationVersion("0.001")
  mainwin = MainWin()
  mainwin.show()
  for arg in sys.argv[1:]:
    if arg not in ["-debug"]:
      mainwin.load(arg)
  app.exec_()
