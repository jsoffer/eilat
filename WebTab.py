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
from libeilat import log, fix_url

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

        def toggle_status():
            """ One-time callback for QShortcut """
            self.statusbar.setVisible(not self.statusbar.isVisible())

        def show_search():
            """ One-time callback for QShortcut """
            self.search_frame.search("")
            self.search_frame.setVisible(True)
            self.search_frame.search_line.setFocus()

        def hide_search():
            """ One-time callback for QShortcut """
            if self.search_frame.isVisible():
                self.search_frame.setVisible(False)
                self.webkit.setFocus()
            else:
                self.webkit.stop()

        def scroll(delta):
            """ One-time callback for QShortcut """
            def ret():
                """ return a lambda to pass argument to callback """
                self.webkit.page().mainFrame().scroll(0, delta)
            return ret

        def zoom(lvl):
            """ One-time callback for QShortcut """
            def ret():
                """ return a lambda to pass argument to callback """
                factor = self.webkit.zoomFactor() + (lvl * 0.25)
                self.webkit.setZoomFactor(factor)
            return ret

        for (shortcut, owner, callback) in [
                ("Ctrl+L", self, self.cmb.setFocus),
                ("Ctrl+J", self.cmb, self.navigate),
                ("F5", self, self.webkit.reload),
                ("R", self, self.webkit.reload),
                ("Alt+Left", self, self.webkit.history().back),
                ("Alt+Right", self, self.webkit.history().forward),
                ("Ctrl+Space", self, toggle_status),
                ("Q", self, self.toggle_script),
                ("J", self, scroll(40)),
                ("K", self, scroll(-40)),
                ("Ctrl+Up", self, zoom(1)),
                ("Ctrl+Down", self, zoom(-1)),
                ("G", self, show_search),
                ("Return", self.search_frame, self.do_search),
                ("Escape", self.search_frame, hide_search)
                ]:
            QtGui.QShortcut(shortcut, owner, callback)

        self.show_hide_message()

        # replace the Network Access Manager (log connections)
        page.setNetworkAccessManager(netmanager)

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

    def load_progress(self, val):
        """ Callback for connection """
        if self.pbar.isVisible():
            self.pbar.setValue(val)

    # connect (en constructor)
    def show_progress_bar(self):
        """ Callback for connection """
        self.pbar.setValue(0)
        self.pbar.setVisible(True)

    # connect (en constructor)
    def load_finished(self, success):
        """ Callback for connection """
        self.pbar.setVisible(False)
        if self.cmb.hasFocus():
            self.webkit.setFocus()
        if not success:
            print "loadFinished: failed"

    # connect (en constructor)
    def on_link_click(self, qurl):
        """ Callback for connection. Reads the 'paste' attribute from
        the extended QWebView to know if a middle click requested open
        on new tab.

        """
        if self.webkit.paste:
            self.browser.add_tab(qurl)
        else:
            self.navigate(qurl)

    # connect (en constructor)
    def on_link_hovered(self, link, title, content):
        """ The mouse is over an image or link. Does it have href?
        Does it have a title? Display on status bar.

        """
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
        """ Shown in status bar when nothing is happening """
        message = "(press %s to hide this)"
        self.statusbar.showMessage(message)

    # action (en register_actions)
    def navigate(self, url = None):
        """ Send this tab to the url. If 'url' is already a QUrl (for example
        if it comes from a href click), just send it. Otherwise, check if the
        "url" is actually one, partial or otherwise; if it's not, construct
        a web search.

        If 'url' is None, extract it directly from the address bar.

        """
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
        """ Go upwards to the web browser's tab widget and set this
        tab's title
        """
        if self.browser:
            self.browser.tab_widget.setTabText(
                    self.browser.tab_widget.indexOf(self), title[:40])

    # connection in constructor and action
    def do_search(self, search = None):
        """ Find text on the currently loaded web page. If no text
        is provided, it's extracted from the search widget.

        """
        if search is None:
            search = self.search_frame.search()
        self.webkit.findText(search, QWebPage.FindWrapsAroundDocument)

class SearchFrame(QtGui.QFrame):
    """ A frame with a label and a text entry. The text is provided to
    the application upwards to perform in-page search.

    """

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
        """ Sets or gets the content of the line edit, depending on
        if it was called with or without arguments.

        """
        if text:
            self.search_line.setText(text)
        else:
            return self.search_line.text()
