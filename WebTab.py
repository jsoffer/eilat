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

import PyQt4.QtGui as QtGui
from PyQt4.QtWebKit import QWebPage, QWebSettings
from PyQt4.QtCore import QUrl


# local
from WebView import WebView
from libeilat import log, register_shortcuts, fixUrl

class WebTab(QtGui.QWidget):
    """ Cada tab contiene una página web """
    def __init__(self, browser, netmanager, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.actions = dict()

        self.browser = browser

        # layout
        self.grid = QtGui.QGridLayout(self)
        self.grid.setSpacing(0)
        self.grid.setVerticalSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)

        # webkit: la parte que entra a internet
        # aquí se configura, cada tab tiene opciones independientes
        self.webkit = WebView(self)
        self.webkit.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.webkit.linkClicked.connect(self.onLinkClick)
        self.webkit.settings().setAttribute(
                QWebSettings.PluginsEnabled, False)
        self.webkit.settings().setAttribute(
                QWebSettings.JavascriptEnabled, False)
        #self.webkit.settings().setAttribute(
        #       QWebSettings.SpatialNavigationEnabled, True)
        #self.webkit.settings().setAttribute(
        #       QWebSettings.DeveloperExtrasEnabled, True)

        # address bar
        self.cmb = QtGui.QComboBox()
        self.cmb.setEditable(True)

        # progress bar
        self.pbar = QtGui.QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setTextVisible(False)
        self.pbar.setVisible(False)
        self.pbar.setMaximumHeight(7)

        self.search_frame = SearchFrame()

        self.statusbar = QtGui.QStatusBar()
        self.statusbar.setVisible(False)
        self.statusbar.setMaximumHeight(25)

        self.grid.addWidget(self.webkit, 1, 0)
        self.grid.setRowStretch(1, 1)
        self.grid.addWidget(self.search_frame, 2, 0)
        self.grid.addWidget(self.cmb, 0, 0)
        self.grid.addWidget(self.pbar, 3, 0)
        self.grid.addWidget(self.statusbar, 4, 0)

        self.webkit.loadStarted.connect(self.loadStarted)
        self.webkit.loadFinished.connect(self.loadFinished)
        self.webkit.titleChanged.connect(self.setTitle)
        self.webkit.loadProgress.connect(self.loadProgress)
        self.webkit.urlChanged.connect(self.setURL)
        self.webkit.page().linkHovered.connect(self.onLinkHovered)

        # el contenido de la tab (los datos, no el contenedor)
        page = self.webkit.page()

        page.downloadRequested.connect(
                lambda k: log("D: " + k.url().toString()))
        page.unsupportedContent.connect(
                lambda k: log("U: " + k.url().toString()))
        self.search_frame.search_line.textChanged.connect(self.doSearch)

        page.setForwardUnsupportedContent(True)

        self.registerActions()
        register_shortcuts(self.actions, self)
        self.showHideMessage()

        # replace the Network Access Manager (log connections)
        self.netmanager = netmanager
        page.setNetworkAccessManager(self.netmanager)

    # connect (en constructor)
    def loadProgress(self, val):
        if self.pbar.isVisible():
            self.pbar.setValue(val)

    # connect (en constructor)
    def setURL(self, url):
        self.cmb.setEditText(url.toString())

    # connect (en constructor)
    def loadStarted(self):
        self.showProgressBar()

    def showProgressBar(self):
        self.pbar.setValue(0)
        self.pbar.setVisible(True)

    # connect (en constructor)
    def loadFinished(self, success):
        self.hideProgressBar()
        if self.cmb.hasFocus():
            self.webkit.setFocus()

    def hideProgressBar(self, success = False):
        self.pbar.setVisible(False)

    # connect (en constructor)
    def onLinkClick(self, qurl):
        if self.webkit.paste:
            self.browser.add_tab(qurl)
        else:
            self.navigate(qurl)

    # connect (en constructor)
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

    # en constructor
    def showHideMessage(self):
        message = "(press %s to hide this)"
        self.statusbar.showMessage(message % (self.actions["togglestatus"][1]))

    def registerActions(self):
        self.actions["go"]        = [self.cmb.setFocus, "Ctrl+L", "Focus address bar"]
        self.actions["addressnav"]  = [self.navigate, "Enter|Ctrl+J", self.cmb, "Navigate to the url in the address bar"]
        self.actions["reload"]      = [self.webkit.reload, "F5|R", "Reload the current page"]
        self.actions["back"]        = [self.back, "Alt+Left", "Go back in history"]
        self.actions["fwd"]         = [self.fwd, "Alt+Right", "Go forward in history"]
        self.actions["togglestatus"] = [self.toggleStatus, "Ctrl+Space", "Toggle visibility of status bar"]
        self.actions["togglejs"] = [self.toggleScript, "Q", "Switches javascript on/off"]
        # el scroll debería ser el mismo de apretar flecha arriba / flecha abajo
        self.actions["scrolldown"] = [lambda: self.webkit.page().mainFrame().scroll(0, 40), "J", "Scrolls down"]
        self.actions["scrollup"] = [lambda: self.webkit.page().mainFrame().scroll(0, -40), "K", "Scrolls down"]
        self.actions["getfocus"] = [self.webkit.setFocus, "H", "Aquires focus for the webkit"]
        self.actions["zoomin"]    = [lambda: self.zoom(1),   "Ctrl+Up", "Zoom into page"]
        self.actions["zoomout"]   = [lambda: self.zoom(-1),  "Ctrl+Down", "Zoom out of page"]
        self.actions["search"] = [self.showSearch, "G", "Start a search"]
        self.actions["findnext"]    = [self.doSearch, "Return", self.search_frame, "Next match for current search"]
        self.actions["stopsearch"]  = [self.stopOrHideSearch, "Escape", self.search_frame, "Stop current load or searching"]

    # action (en registerActions)
    def toggleScript(self):
        """ Activa o desactiva javascript, y notifica cambiando el color
        del address bar

        """
        if self.webkit.settings().testAttribute(
                QWebSettings.JavascriptEnabled):
            self.webkit.settings().setAttribute(
                    QWebSettings.JavascriptEnabled, False)
            self.cmb.setStyleSheet("QComboBox { background-color: #fff; }")
        else:
            self.webkit.settings().setAttribute(
                    QWebSettings.JavascriptEnabled, True)
            self.cmb.setStyleSheet("QComboBox { background-color: #ddf; }")

    # action (en registerActions)
    def toggleStatus(self):
        self.statusbar.setVisible(not self.statusbar.isVisible())

    # auxiliar; action (en registerActions)
    def zoom(self, lvl):
        self.webkit.setZoomFactor(self.webkit.zoomFactor() + (lvl * 0.25))

    # action (en registerActions)
    def fwd(self):
        self.webkit.history().forward()

    # action (en registerActions)
    def back(self):
        self.webkit.history().back()

    # action (en registerActions)
    def navigate(self, url = None):
        if isinstance(url, QUrl):
            qurl = url
        else:
            if not url: url = unicode(self.cmb.currentText())
            qurl = fixUrl(url)
        self.setTitle("Loading...")
        self.webkit.load(qurl)
        self.webkit.setFocus()

    # connect (en constructor)
    def setTitle(self, title):
        if self.browser:
            self.browser.tabWidget.setTabText(self.browser.tabWidget.indexOf(self), title[:40])

    # connection in constructor and action
    def doSearch(self, search = None):
        if search is None: search = self.search_frame.search()
        self.webkit.findText(search, QWebPage.FindWrapsAroundDocument)

    # action (en registerActions)
    def showSearch(self):
        self.search_frame.search("")
        self.search_frame.setVisible(True)
        self.search_frame.focus_text()

    # action (en registerActions)
    def stopOrHideSearch(self):
        if self.search_frame.isVisible():
            self.search_frame.setVisible(False)
            self.webkit.setFocus()
        else:
            self.webkit.stop()

class SearchFrame(QtGui.QFrame):
    def __init__(self):
        super(SearchFrame, self).__init__()

        self.search_grid = QtGui.QGridLayout(self)
        self.search_grid.setSpacing(0)
        self.search_grid.setContentsMargins(0, 0, 0, 0)
        self.label = QtGui.QLabel("Find in page:")
        self.search_line = QtGui.QLineEdit()
        self.search_grid.addWidget(self.label, 0, 0)
        self.search_grid.addWidget(self.search_line, 0, 1)
        self.setVisible(False)

    def search(self, text = None):
        if text:
            self.search_line.setText(text)
        else:
            return self.search_line.text()

    def focus_text(self):
        self.search_line.setFocus()
