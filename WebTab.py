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
import PyQt4.QtGui as QtGui
from PyQt4.QtWebKit import QWebPage, QWebSettings
from PyQt4.QtCore import QUrl


from WebView import WebView

from libeilat import log, registerShortcuts

class WebTab(QtGui.QWidget):
  """ Cada tab contiene una página web """
  def __init__(self, browser, netmanager, clipboard, actions=None, parent=None, showStatusBar=False):
    QtGui.QWidget.__init__(self, parent)
    self.actions = dict()

    self.browser = browser
    self.cb = clipboard

    # layout
    self.grid = QtGui.QGridLayout(self)
    self.grid.setSpacing(0)
    self.grid.setVerticalSpacing(0)
    self.grid.setContentsMargins(0,0,0,0)

    # webkit: la parte que entra a internet
    # aquí se configura, cada tab tiene opciones independientes
    self.webkit = WebView(self)
    self.webkit.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
    self.webkit.linkClicked.connect(self.onLinkClick)
    self.webkit.settings().setAttribute(QWebSettings.PluginsEnabled,False)
    self.webkit.settings().setAttribute(QWebSettings.JavascriptEnabled,False)
    #self.webkit.settings().setAttribute(QWebSettings.SpatialNavigationEnabled,True)
    #self.webkit.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled,True)
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

    self.grid.addWidget(self.webkit, 1, 0)
    self.grid.setRowStretch(1, 1)
    self.grid.addWidget(self.fraSearch, 2, 0)
    self.grid.addWidget(self.cmb, 0, 0)
    self.grid.addWidget(self.pbar, 3, 0)
    self.grid.addWidget(self.statusbar, 4, 0)

    # cuando se selecciona una opción del combobox dropdown
    # Incorrecto; entra cada vez que se mueve el combobox
    #self.cmb.currentIndexChanged.connect(self.navigate)

    self.webkit.loadStarted.connect(self.loadStarted)
    self.webkit.loadFinished.connect(self.loadFinished)
    self.webkit.titleChanged.connect(self.setTitle)
    self.webkit.loadProgress.connect(self.loadProgress)
    self.webkit.urlChanged.connect(self.setURL)
    self.webkit.page().linkHovered.connect(self.onLinkHovered)

    # el contenido de la tab (los datos, no el contenedor)
    page = self.webkit.page()
    page.downloadRequested.connect(self.onDownloadRequested)
    page.setForwardUnsupportedContent(True)
    page.unsupportedContent.connect(self.onUnsupportedContent)
    self.txtSearch.textChanged.connect(self.doSearch)

    self.registerActions()
    registerShortcuts(self.actions, self)
    self.showHideMessage()

    # reemplazar el Network Access Manager para saber qué contenido está pidiendo
    self.netmanager = netmanager
    page.setNetworkAccessManager(self.netmanager)

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
    self.actions["paste"] = [lambda: self.browser.addTab(unicode(self.cb.text(QClipboard.Selection)).strip()), "Y", "Access to clipboard"]
    self.actions["togglejs"] = [self.toggleScript, "Q", "Switches javascript on/off"]
    self.actions["getfocus"] = [lambda: self.webkit.setFocus(), "H", "Aquires focus for the webkit"]

  def toggleScript(self):
    """ Activa o desactiva javascript, y notifica cambiando el color del address bar """
    if self.webkit.settings().testAttribute(QWebSettings.JavascriptEnabled):
        self.webkit.settings().setAttribute(QWebSettings.JavascriptEnabled,False)
        self.cmb.setStyleSheet("QComboBox { background-color: #fff; }")
    else:
        self.webkit.settings().setAttribute(QWebSettings.JavascriptEnabled,True)
        self.cmb.setStyleSheet("QComboBox { background-color: #ddf; }")

  def stopScript(self):
        self.webkit.settings().setAttribute(QWebSettings.JavascriptEnabled,False)
        self.cmb.setStyleSheet("QComboBox { background-color: #fff; }")

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
    self.webkit.findText(s, QWebPage.FindWrapsAroundDocument)

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
        if not url or type(url) == int: url = unicode(self.cmb.currentText()) # ??? TODO
        url = QUrl(self.browser.fixUrl(url))
        self.cmb.addItem(url.host() + url.path())
        self.setTitle("Loading...")
        self.webkit.load(url)
        self.webkit.setFocus()

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
