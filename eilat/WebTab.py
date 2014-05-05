# -*- coding: utf-8 -*-

"""

  Copyright (c) 2012, Davyd McColl; 2013, 2014 Jaime Soffer

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

from __future__ import unicode_literals, print_function

import PyQt4.QtGui as QtGui
from PyQt4.QtWebKit import QWebPage, QWebSettings
from PyQt4.QtCore import QUrl, Qt, QEvent

from functools import partial
from re import sub

# local
from WebView import WebView
from libeilat import set_shortcuts, fix_url, real_host, encode_css
from libeilat import filtra, notnull, copy_to_clipboard, osd

class WebTab(QtGui.QWidget):
    """ Cada tab contiene una página web """
    def __init__(self, browser, parent=None):
        super(WebTab, self).__init__(parent)

        self.browser = browser

        # webkit: la parte que entra a internet
        # aquí se configura, cada tab tiene opciones independientes
        self.webkit = WebView(browser.netmanager, parent=self)
        self.webkit.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.webkit.linkClicked.connect(self.on_link_click)
        self.webkit.settings().setAttribute(
                QWebSettings.PluginsEnabled, False)
        self.webkit.settings().setAttribute(
                QWebSettings.JavascriptEnabled, False)
        self.webkit.settings().setAttribute(
               QWebSettings.SpatialNavigationEnabled, True)
        #self.webkit.settings().setAttribute(
        #       QWebSettings.DeveloperExtrasEnabled, True)

        main_frame = self.webkit.page().mainFrame()
        ##### NUEVO
        test_javascript = """ window.onload=function(){
        var txt = document.createTextNode("new text");
        document.getElementsByTagName('body')[0].appendChild(txt);
        }
        """

        #main_frame.evaluateJavaScript(javascript)

        main_frame.initialLayoutCompleted.connect(
                partial(main_frame.evaluateJavaScript, test_javascript))

        def process_clipboard(notify, request):
            """ notify and save to clipboard """
            #osd(request.url().toString())
            message = unicode(request.url().toString()) + "\n" + notify
            print(message)
            osd(message)
            copy_to_clipboard(self.browser.clipboard, request)

        self.webkit.page().downloadRequested.connect(partial(
            process_clipboard, "Download Requested"))
            #copy_to_clipboard, self.browser.clipboard))
        self.webkit.page().unsupportedContent.connect(partial(
            process_clipboard, "Unsupported Content"))
            #copy_to_clipboard, self.browser.clipboard))

        self.webkit.page().setForwardUnsupportedContent(True)

        # address bar
        self.address_bar = AddressBar(model=browser.model, parent=self)

        # progress bar
        self.pbar = QtGui.QProgressBar(self)
        self.pbar.setRange(0, 100)
        self.pbar.setTextVisible(False)
        self.pbar.setVisible(False)
        self.pbar.setMaximumHeight(7)

        self.search_frame = SearchFrame(parent=self)

        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setVisible(False)
        self.statusbar.setMaximumHeight(25)

        self.webkit.loadStarted.connect(self.show_progress_bar)
        self.webkit.loadFinished.connect(self.load_finished)
        self.webkit.titleChanged.connect(self.set_title)
        self.webkit.loadProgress.connect(self.load_progress)

        def url_changed(qurl):
            """ One time callback for 'connect'
            Sets the user style sheet, sets the address bar text

            """
            host_id = real_host(qurl.host())
            css_file = self.browser.css_path + host_id + ".css"
            try:
                with open(css_file, 'r') as css_fh:
                    css_encoded = encode_css(css_fh.read()).strip()
            except IOError:
                css_encoded = encode_css('')
            self.webkit.settings().setUserStyleSheetUrl(
                    QUrl(css_encoded))
            self.address_bar.setText(qurl.toString())

        self.webkit.urlChanged.connect(url_changed)
        self.webkit.page().linkHovered.connect(self.on_link_hovered)

        self.search_frame.search_line.textChanged.connect(self.do_search)

        # layout
        grid = QtGui.QGridLayout(self)
        grid.setSpacing(0)
        grid.setVerticalSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)

        grid.addWidget(self.webkit, 1, 0)
        grid.setRowStretch(1, 1)
        grid.addWidget(self.search_frame, 2, 0)
        grid.addWidget(self.address_bar, 0, 0)
        grid.addWidget(self.pbar, 3, 0)
        grid.addWidget(self.statusbar, 4, 0)


        def toggle_status():
            """ One-time callback for QShortcut """
            self.statusbar.setVisible(not self.statusbar.isVisible())

        def show_search():
            """ One-time callback for QShortcut """
            self.search_frame.setVisible(True)
            self.search_frame.search_line.setFocus()

        def hide_search():
            """ One-time callback for QShortcut """
            self.search_frame.setVisible(False)
            self.webkit.findText("")
            self.webkit.setFocus()

        def scroll(delta_x=0, delta_y=0):
            """ One-time callback for QShortcut """
            self.webkit.page().mainFrame().scroll(delta_x, delta_y)

        def zoom(lvl):
            """ One-time callback for QShortcut """
            factor = self.webkit.zoomFactor() + (lvl * 0.25)
            self.webkit.setZoomFactor(factor)

        def navigate_completion(key=Qt.Key_Down):
            """ Sends an "arrow press" to the completion popup to navigate
            results.

            Not the best way to do this. It would be better to find out what
            function is being called by that arrow press.

            """

            event = QtGui.QKeyEvent(
                        QEvent.KeyPress, key, Qt.KeyboardModifiers())

            QtGui.QApplication.sendEvent(
                    self.address_bar.completer().popup(), event)

        set_shortcuts([
            ("Ctrl+L", self.webkit, self.address_bar.setFocus),
            ("Ctrl+J", self.address_bar, self.navigate),
            ("Ctrl+I", self.address_bar, navigate_completion),
            ("Ctrl+O", self.address_bar, partial(
                navigate_completion, Qt.Key_Up)),
            ("Return", self.address_bar, self.navigate),
            ("Ctrl+Space", self.webkit, toggle_status),
            ("Q", self.webkit, self.toggle_script),
            ("J", self.webkit, partial(scroll, delta_y=40)),
            ("K", self.webkit, partial(scroll, delta_y=-40)),
            ("H", self.webkit, partial(scroll, delta_x=-40)),
            ("L", self.webkit, partial(scroll, delta_x=40)),
            ("E", self, partial(copy_to_clipboard,
                self.browser.clipboard,
                self.address_bar.text)),
            ("Ctrl+Up", self, partial(zoom, 1)),
            ("Ctrl+Down", self, partial(zoom, -1)),
            ("G", self.webkit, show_search),
            ("I", self.webkit, self.webkit.set_paste),
            ("S", self.webkit, self.webkit.set_save),
            ("Return", self.search_frame, self.do_search),
            ("Ctrl+J", self.search_frame, self.do_search),
            ("Escape", self.search_frame, hide_search),
            ("Escape", self.address_bar, self.webkit.setFocus)
            ])

        #self.browser.tab_widget.tabBar().tabButton(0,1).hide()

    def toggle_script(self):
        """ Activa o desactiva javascript, y notifica cambiando el color
        del address bar

        Callback for shortcut action
        """
        if self.webkit.settings().testAttribute(
                QWebSettings.JavascriptEnabled):
            self.webkit.settings().setAttribute(
                    QWebSettings.JavascriptEnabled, False)
            self.address_bar.set_color()
        else:
            self.webkit.settings().setAttribute(
                    QWebSettings.JavascriptEnabled, True)
            self.address_bar.set_color((230, 230, 255))

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
        if self.address_bar.hasFocus():
            self.webkit.setFocus()
        if not success:
            #osd("loadFinished: failed")
            print("loadFinished: failed")

    # connect (en constructor)
    def on_link_click(self, qurl):
        """ Callback for connection. Reads the 'paste' attribute from
        the extended QWebView to know if a middle click requested to open
        on a new tab.

        """
        if self.webkit.paste:
            self.browser.add_tab(qurl)
            self.webkit.paste = False
        else:
            self.navigate(qurl)

    # connect (en constructor)
    def on_link_hovered(self, link, title, _):
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
            self.statusbar.showMessage("")

    # action (en register_actions)
    def navigate(self, url=None):
        """ Open the url on this tab. If 'url' is already a QUrl
        (if it comes from a href click), just send it. Otherwise,
        it comes either from the address bar or the PRIMARY
        clipboard through a keyboard shortcut.
        Check if the "url" is actually one, partial or otherwise;
        if it's not, construct a web search.

        If 'url' is None, extract it directly from the address bar.

        """

        #index_self = self.browser.tab_widget.indexOf(self)
        #print("I", index_self)
        #print("B", self.browser.tab_widget.tabBar().tabButton(index_self,1))
        #self.browser.tab_widget.tabBar().tabButton(index_self,1).hide()

        self.search_frame.setVisible(False)
        self.address_bar.completer().popup().close()

        if self.webkit.save:
            copy_to_clipboard(self.browser.clipboard, url)
            self.webkit.save = False
            return

        if isinstance(url, QUrl):
            qurl = url
        else:
            if not url:
                url = unicode(self.address_bar.text())
            qurl = fix_url(url)
        self.set_title("Loading...")

        if self.browser.log:
            self.browser.log.store_navigation({
                "id": self.browser.log.instance_id,
                "scheme": unicode(qurl.scheme()),
                "host": unicode(qurl.host()),
                "path": unicode(qurl.path()),
                "query": filtra(qurl.encodedQueryItems()),
                "fragment": notnull(
                    unicode(qurl.fragment())),
                })


        host = sub("^www.", "", unicode(qurl.host()))
        path = unicode(qurl.path()).rstrip("/ ")

        if(
                (host not in ["duckduckgo.com"]) and
                (not qurl.encodedQuery()) and
                len(path.split('/')) < 3):
            self.browser.register_nav(host, path)

        self.webkit.load(qurl)
        self.webkit.setFocus()

    # connect (en constructor)
    def set_title(self, title):
        """ Go upwards to the web browser's tab widget and set this
        tab's title
        """
        self.browser.tab_widget.setTabText(
                self.browser.tab_widget.indexOf(self), title[:40])

    # connection in constructor and action
    def do_search(self, search=None):
        """ Find text on the currently loaded web page. If no text
        is provided, it's extracted from the search widget.

        """
        if search is None:
            search = self.search_frame.search_line.text()
        self.webkit.findText(search, QWebPage.FindWrapsAroundDocument)

class SearchFrame(QtGui.QFrame):
    """ A frame with a label and a text entry. The text is provided to
    the application upwards to perform in-page search.

    """

    def __init__(self, parent=None):
        super(SearchFrame, self).__init__(parent)

        self.search_grid = QtGui.QGridLayout(self)
        self.search_grid.setSpacing(0)
        self.search_grid.setContentsMargins(0, 0, 0, 0)
        self.label = QtGui.QLabel("Find in page:")
        self.search_line = QtGui.QLineEdit()
        self.search_grid.addWidget(self.label, 0, 0)
        self.search_grid.addWidget(self.search_line, 0, 1)
        self.setVisible(False)

        set_shortcuts([
            ("Ctrl+H", self, self.search_line.backspace),
            ])

class AddressBar(QtGui.QLineEdit):
    """ A command line of sorts; receives addresses, search terms or
    app-defined commands

    """

    def __init__(self, model, parent=None):
        super(AddressBar, self).__init__(parent)

        set_shortcuts([
            ("Ctrl+H", self, self.backspace),
            ("Ctrl+Y", self, self.crop_right),
            ("Ctrl+U", self, partial(self.crop_right, root=True))
            ])

        self.set_color()
        self.setCompleter(QtGui.QCompleter(model, self))

    def crop_right(self, root=False):
        """
        Removes the final '/something' on an url
        If 'root' is requested, it removes everything right of the host

        """
        url = self.text().split('/')

        if root:
            if ':' in url[0]:
                # [:3] accounts for 'http://' and then the host
                new_url = url[:3].join('/')
            else:
                new_url = url[0]
        else:
            new_url = url[:-1].join('/')

        self.setText(new_url)


    def set_color(self, rgb=(255, 255, 255)):
        """ Sets the background color of the address bar """
        self.setStyleSheet(
                "QLineEdit { background-color: rgb(%s, %s, %s)}" % rgb)

    def focus_out_event(self, event):
        """ Close completion if it's open while the tab is changed """
        self.completer().popup().close()
        super(AddressBar, self).focusOutEvent(event)

    # Clean reimplement for Qt
    # pylint: disable=C0103
    focusOutEvent = focus_out_event
    # pylint: enable=C0103
