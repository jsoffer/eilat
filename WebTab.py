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
from libeilat import log, register_shortcuts, fix_url

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
        self.webkit.linkClicked.connect(self.on_link_click)
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

        self.webkit.loadStarted.connect(self.show_progress_bar)
        self.webkit.loadFinished.connect(self.load_finished)
        self.webkit.titleChanged.connect(self.set_title)
        self.webkit.loadProgress.connect(self.load_progress)
        self.webkit.urlChanged.connect(
                lambda url: self.cmb.setEditText(url.toString()))
        self.webkit.page().linkHovered.connect(self.on_link_hovered)

        # el contenido de la tab (los datos, no el contenedor)
        page = self.webkit.page()

        page.downloadRequested.connect(
                lambda k: log("D: " + k.url().toString()))
        page.unsupportedContent.connect(
                lambda k: log("U: " + k.url().toString()))
        self.search_frame.search_line.textChanged.connect(self.do_search)

        page.setForwardUnsupportedContent(True)

        self.register_actions()
        register_shortcuts(self.actions, self)
        self.show_hide_message()

        # replace the Network Access Manager (log connections)
        page.setNetworkAccessManager(netmanager)

    # connect (en constructor)
    def load_progress(self, val):
        if self.pbar.isVisible():
            self.pbar.setValue(val)

    # connect (en constructor)
    def show_progress_bar(self):
        self.pbar.setValue(0)
        self.pbar.setVisible(True)

    # connect (en constructor)
    def load_finished(self, success):
        self.pbar.setVisible(False)
        if self.cmb.hasFocus():
            self.webkit.setFocus()
        if not success:
            print "loadFinished: failed"

    # connect (en constructor)
    def on_link_click(self, qurl):
        if self.webkit.paste:
            self.browser.add_tab(qurl)
        else:
            self.navigate(qurl)

    # connect (en constructor)
    def on_link_hovered(self, link, title, content):
        if link or title:
            if title and not link:
                self.statusbar.showMessage(title)
            elif link and not title:
                self.statusbar.showMessage(link)
            elif link and title:
                self.statusbar.showMessage("%s (%s)" % (title, link))
        else:
            self.show_hide_message()

    # en constructor
    def show_hide_message(self):
        message = "(press %s to hide this)"
        self.statusbar.showMessage(message % (self.actions["togglestatus"][1]))

    def register_actions(self):
        self.actions["go"]        = [self.cmb.setFocus, "Ctrl+L", "Focus address bar"]
        self.actions["addressnav"]  = [self.navigate, "Enter|Ctrl+J", self.cmb, "Navigate to the url in the address bar"]
        self.actions["reload"]      = [self.webkit.reload, "F5|R", "Reload the current page"]
        self.actions["back"]        = [self.back, "Alt+Left", "Go back in history"]
        self.actions["fwd"]         = [self.fwd, "Alt+Right", "Go forward in history"]
        self.actions["togglestatus"] = [self.toggle_status, "Ctrl+Space", "Toggle visibility of status bar"]
        self.actions["togglejs"] = [self.toggle_script, "Q", "Switches javascript on/off"]
        # el scroll debería ser el mismo de apretar flecha arriba / flecha abajo
        self.actions["scrolldown"] = [lambda: self.webkit.page().mainFrame().scroll(0, 40), "J", "Scrolls down"]
        self.actions["scrollup"] = [lambda: self.webkit.page().mainFrame().scroll(0, -40), "K", "Scrolls down"]
        self.actions["getfocus"] = [self.webkit.setFocus, "H", "Aquires focus for the webkit"]
        self.actions["zoomin"]    = [lambda: self.zoom(1),   "Ctrl+Up", "Zoom into page"]
        self.actions["zoomout"]   = [lambda: self.zoom(-1),  "Ctrl+Down", "Zoom out of page"]
        self.actions["search"] = [self.show_search, "G", "Start a search"]
        self.actions["findnext"]    = [self.do_search, "Return", self.search_frame, "Next match for current search"]
        self.actions["stopsearch"]  = [self.hide_search, "Escape", self.search_frame, "Stop current load or searching"]

    # action (en register_actions)
    def toggle_script(self):
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

    # action (en register_actions)
    def toggle_status(self):
        self.statusbar.setVisible(not self.statusbar.isVisible())

    # auxiliar; action (en register_actions)
    def zoom(self, lvl):
        self.webkit.setZoomFactor(self.webkit.zoomFactor() + (lvl * 0.25))

    # action (en register_actions)
    def fwd(self):
        self.webkit.history().forward()

    # action (en register_actions)
    def back(self):
        self.webkit.history().back()

    # action (en register_actions)
    def navigate(self, url = None):
        if isinstance(url, QUrl):
            qurl = url
        else:
            if not url:
                url = unicode(self.cmb.currentText())
            qurl = fix_url(url)
        self.set_title("Loading...")
        self.webkit.load(qurl)
        self.webkit.setFocus()

    # connect (en constructor)
    def set_title(self, title):
        if self.browser:
            self.browser.tab_widget.setTabText(
                    self.browser.tab_widget.indexOf(self), title[:40])

    # connection in constructor and action
    def do_search(self, search = None):
        if search is None:
            search = self.search_frame.search()
        self.webkit.findText(search, QWebPage.FindWrapsAroundDocument)

    # action (en register_actions)
    def show_search(self):
        self.search_frame.search("")
        self.search_frame.setVisible(True)
        self.search_frame.focus_text()

    # action (en register_actions)
    def hide_search(self):
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
