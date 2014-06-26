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

from PyQt4.QtGui import (QWidget, QProgressBar, QStatusBar, QGridLayout,
                         QFrame, QLabel, QLineEdit, QCompleter, QKeyEvent)
from PyQt4.QtWebKit import QWebPage, QWebSettings
from PyQt4.QtCore import Qt, QEvent, QTimer

from functools import partial

from collections import deque

# local
from eilat.WebView import WebView
from eilat.DatabaseLog import DatabaseLogLite
from eilat.libeilat import set_shortcuts
from eilat.global_store import mainwin, clipboard

class WebTab(QWidget):
    """ Cada tab contiene una página web """
    def __init__(self, parent=None):
        super(WebTab, self).__init__(parent)

        self.current_title = "[EMPTY]"

        # address bar
        self.address_bar = AddressBar(parent=self)

        # notifier

        self.notifier = NotifyLabel(parent=self)

        prefix_label = QLabel(parent=self)
        prefix_label.hide()

        def update_prefix_label(string):
            """ if on a non-global web instance, show the instance's prefix
            next to the address bar

            """
            if string:
                prefix_label.setText(string)
                prefix_label.show()

        # webkit (the actual "web engine")
        self.webkit = WebView(parent=self)

        self.webkit.prefix_set.connect(partial(setattr, self, 'prefix'))
        self.webkit.prefix_set.connect(self.address_bar.set_model)
        self.webkit.prefix_set.connect(update_prefix_label)

        def update_address(qurl):
            """ Just because the 'connect' gives a QUrl and setText receives
            a string

            Required because a 3XX HTTP redirection will change the address,
            and without updating, the address bar will be left stale

            """
            self.address_bar.setText(qurl.toString())

        self.webkit.urlChanged.connect(update_address)
        self.webkit.loadStarted.connect(self.load_started)
        self.webkit.loadFinished.connect(self.load_finished)
        self.webkit.titleChanged.connect(self.save_title)
        self.webkit.loadProgress.connect(self.load_progress)

        def fill_notifier(message, request):
            """ sends a message to be displayed by the notifier, and starts a
            timer to hide it after eight seconds

            """
            self.notifier.push_text(message + " " + request.url().toString())

        self.webkit.page().downloadRequested.connect(
            partial(fill_notifier, "download"))
        self.webkit.page().unsupportedContent.connect(
            partial(fill_notifier, "unsupported"))

        # progress bar
        self.pbar = QProgressBar(self)

        self.pbar.setRange(0, 100)
        self.pbar.setTextVisible(False)
        self.pbar.setVisible(False)
        self.pbar.setMaximumHeight(7)

        # search in page
        self.search_frame = SearchFrame(parent=self)

        # status bar
        self.statusbar = QStatusBar(self)

        self.statusbar.setVisible(False)
        self.statusbar.setMaximumHeight(25)

        self.webkit.page().linkHovered.connect(self.on_link_hovered)

        self.search_frame.search_line.textChanged.connect(self.do_search)

        # layout
        grid = QGridLayout(self)
        grid.setSpacing(0)
        grid.setVerticalSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setRowStretch(1, 1)

        grid.addWidget(prefix_label, 0, 0, 1, 1)
        grid.addWidget(self.address_bar, 0, 1, 1, 1)
        grid.addWidget(self.notifier, 0, 2, 1, 1)

        grid.addWidget(self.webkit, 1, 0, 1, 3)
        grid.addWidget(self.search_frame, 2, 0, 1, 3)
        grid.addWidget(self.pbar, 3, 0, 1, 3)
        grid.addWidget(self.statusbar, 4, 0, 1, 3)

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

        def navigate_completion(key=Qt.Key_Down):
            """ Sends an "arrow press" to the completion popup to navigate
            results.

            Not the best way to do this. It would be better to find out what
            function is being called by that arrow press.

            """
            event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)

            self.address_bar.completer().popup().keyPressEvent(event)

        set_shortcuts([
            # search
            ("G", self.webkit, show_search),
            ("Escape", self.search_frame, hide_search),
            ("Return", self.search_frame, self.do_search),
            ("Ctrl+J", self.search_frame, self.do_search),
            # go to page
            ("Ctrl+J", self.address_bar, partial(
                self.webkit.navigate, self.address_bar.text)),
            ("Return", self.address_bar, partial(
                self.webkit.navigate, self.address_bar.text)),
            # address bar interaction
            ("Ctrl+L", self.webkit, self.address_bar.setFocus),
            ("Escape", self.address_bar, self.webkit.setFocus),
            ("Ctrl+I", self.address_bar, navigate_completion),
            ("Ctrl+P", self.address_bar, partial(
                navigate_completion, Qt.Key_Up)),
            # toggle
            ("Ctrl+Space", self.webkit, toggle_status),
            ("Q", self.webkit, self.toggle_script),
            # clipboard
            ("E", self, partial(clipboard, self.address_bar.text))
            ])

    def toggle_script(self):
        """ Activa o desactiva javascript, y notifica cambiando el color
        del address bar

        Callback for shortcut action
        """

        javascript_on = self.webkit.settings().testAttribute(
            QWebSettings.JavascriptEnabled)

        if javascript_on:
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
            self.set_title(str(val) + "% " + self.current_title)

    # connect (en constructor)
    def load_started(self):
        """ Callback for connection """

        self.address_bar.completer().popup().close()
        self.search_frame.setVisible(False)

        self.pbar.setValue(0)
        self.pbar.setVisible(True)

    # connect (en constructor)
    def load_finished(self, success):
        """ Callback for connection """

        self.webkit.navlist = []

        self.pbar.setVisible(False)
        self.set_title(self.current_title)

        if self.address_bar.hasFocus():
            self.webkit.setFocus()

        if not success:
            self.notifier.push_text("[F]")
            print("loadFinished: failed")


    # connect (en constructor)
    def on_link_hovered(self, link, unused_title, unused_content):
        """ The mouse is over an image or link.
        Display the href (if there's no href, it's '') on the status bar.

        """
        self.statusbar.showMessage(link)

    # connect (en constructor)

    def save_title(self, title):
        """ Store a recently changed title, and display it """
        self.current_title = title
        self.set_title(title)

    def set_title(self, title):
        """ Go upwards to the main window's tab widget and set this
        tab's title
        """

        if title is None:
            title = "[NO TITLE]"

        mainwin().tab_widget.setTabText(
            mainwin().tab_widget.indexOf(self),
            title[:40])

    # connection in constructor and action
    def do_search(self, search=None):
        """ Find text on the currently loaded web page. If no text
        is provided, it's extracted from the search widget.

        """
        if search is None:
            search = self.search_frame.search_line.text()
        self.webkit.findText(search, QWebPage.FindWrapsAroundDocument)

class SearchFrame(QFrame):
    """ A frame with a label and a text entry. The text is provided to
    the application upwards to perform in-page search.

    """

    def __init__(self, parent=None):
        super(SearchFrame, self).__init__(parent)

        self.search_grid = QGridLayout(self)
        self.search_grid.setSpacing(0)
        self.search_grid.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("Find in page:")
        self.search_line = QLineEdit()
        self.search_grid.addWidget(self.label, 0, 0)
        self.search_grid.addWidget(self.search_line, 0, 1)
        self.setVisible(False)

        set_shortcuts([
            ("Ctrl+H", self, self.search_line.backspace),
            ])

class AddressBar(QLineEdit):
    """ A command line of sorts; receives addresses, search terms or
    app-defined commands

    """

    def __init__(self, parent=None):
        super(AddressBar, self).__init__(parent)

        self.database = DatabaseLogLite()
        self.__completer = None
        self.set_model(None)

        self.set_color()

        set_shortcuts([
            ("Ctrl+H", self, self.backspace),
            # do not create a new tab when on the address bar;
            # popup related trouble
            ("Ctrl+T", self, lambda: None),
            ("Ctrl+Shift+T", self, lambda: None)
        ])

    def set_model(self, prefix):
        """ Update the completion model when the prefix is known. Has to
        be done through an instance variable because of a bug (will not
        complete the line edit otherwise)

        """
        self.__completer = QCompleter(self.database.model(prefix), self)
        self.setCompleter(self.__completer)

    def set_color(self, rgb=(255, 255, 255)):
        """ Sets the background color of the address bar """
        self.setStyleSheet(
            "QLineEdit { background-color: rgb(%s, %s, %s)}" % rgb)

class NotifyLabel(QLabel):
    """ A "poor man's" tooltip, that can stack notifications """

    def __init__(self, parent=None):
        super(NotifyLabel, self).__init__(parent)
        self.hide()
        self.content = deque(maxlen=4)

    def push_text(self, string):
        """ Add an entry to the notification. It will, by itself, be
        removed after eight seconds.

        """

        self.content.append(string)
        self.setText((" " + "|".join(self.content) + " ")[:80])
        self.show()
        QTimer.singleShot(8000, self.pop_text)

    def pop_text(self):
        """ Some entry's timeout has triggered; let's remove the oldest one.
        If there's no entry (because the queue spilled before having a chance
        to pop) do nothing. Afterwards, if the queue is empty, hide it.

        """

        if len(self.content) > 0:
            self.content.popleft()
            self.setText(" " + " | ".join(self.content) + " ")
        if len(self.content) == 0:
            self.hide()
