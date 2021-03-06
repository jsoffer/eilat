# -*- coding: utf-8 -*-

"""

  Copyright (c) 2012, Davyd McColl; 2013, 2014, 2015 Jaime Soffer

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

from PyQt5.QtGui import (QKeyEvent, QPalette, QColor)
from PyQt5.QtWebKitWidgets import QWebPage
from PyQt5.QtCore import Qt, QEvent

from PyQt5.Qt import (QApplication, QWidget, QProgressBar, QGridLayout, QFrame,
                      QLabel, QLineEdit, QCompleter, QToolTip)

from functools import partial

# local
from eilat.WebView import WebView
from eilat.libeilat import set_shortcuts, notify
from eilat.global_store import mainwin, clipboard, database


class WebTab(QWidget):
    """ The tab contains chrome plus a web view; is hosted on a tab bar """

    def __init__(self, parent=None):
        super(WebTab, self).__init__(parent)

        self.current = {
            'title': "[EMPTY]",
            'address': ""
        }

        # address bar
        self.address_bar = AddressBar(parent=self)

        # webkit (the actual "web engine")
        self.webkit = WebView(parent=self)

        # set_prefix: app defined, carries str
        self.webkit.set_prefix.connect(self.address_bar.set_model)  # CFG02
        # javascript_state: app defined, carries bool
        self.webkit.javascript_state.connect(self.address_bar.set_bgcolor)

        # small label displaying instance ID and pending tab operations

        info_label = QLabel(parent=self)
        info_label.setText('?')  # CFG02

        # webkit_info: app defined, carries str
        self.webkit.attr.webkit_info.connect(info_label.setText)

        def update_address(qurl):
            """ The 'connect' gives a QUrl and setText receives a string;
            can't just connect setText

            Required because a 3XX HTTP redirection will change the address,
            and without updating, the address bar will be left stale

            AB02 AB03

            """
            self.current['address'] = qurl.toString()
            self.address_bar.setText(self.current['address'])

        # urlChanged carries QUrl; loadStarted carries nothing;
        # loadFinished carries bool; titleChanged carries str;
        # loadProgress carries int
        self.webkit.urlChanged.connect(update_address)
        self.webkit.loadStarted.connect(self.load_started)
        self.webkit.loadFinished.connect(self.load_finished)
        self.webkit.titleChanged.connect(self.save_title)
        self.webkit.loadProgress.connect(self.load_progress)

        def fill_notifier(message, request):
            """ sends a message to be displayed by the notifier

            """
            notify(message + " " + request.url().toString())

        # downloadRequested carries QNetworkRequest
        self.webkit.page().downloadRequested.connect(
            partial(fill_notifier, "download"))
        # unsupportedContent carries QNetworkReply
        self.webkit.page().unsupportedContent.connect(
            partial(fill_notifier, "unsupported"))

        # input area for access-key navigation

        self.nav_bar = NavigateInput(parent=self)
        # editingFinished carries nothing
        self.nav_bar.editingFinished.connect(self.webkit.clear_labels)

        # textEdited carries str
        self.nav_bar.textEdited.connect(self.webkit.akeynav)
        # nonvalid_tag (app defined) carries nothing
        self.webkit.nonvalid_tag.connect(self.nav_bar.clear)

        # 'corner' message and notification label, not on timer, smaller

        self.message_label = MessageLabel(self.webkit)

        def handle_hovered(link, title, content):
            """ When hovered, if ALT is pressed, show message label;
            hide otherwise

            """

            if ((QApplication.keyboardModifiers() & Qt.AltModifier) and
                    (link or title or content)):
                # ugly hack to ensure proper resizing; find a better way?
                self.message_label.hide()
                self.message_label.setText(
                    link + " " + title + " " + content)
                self.message_label.show()
            else:
                self.message_label.hide()

        # linkHovered carries str, str, str
        self.webkit.page().linkHovered.connect(handle_hovered)

        def handle_signaled(title):
            """ We received a string through a signal; display it on
            the message label

            """

            # if title:
            self.message_label.hide()
            self.message_label.setText(title)
            self.message_label.show()

        # show_message (app defined) carries str
        self.webkit.show_message.connect(handle_signaled)
        # loadStarted carries nothing
        self.webkit.loadStarted.connect(self.message_label.hide)

        # At the time navigation is requested load_requested is sent, and the
        # requested url is set as text in grey at the address bar. Once the
        # urlChanged signal is received, the actual url is set in black.

        # load_requested (app defined) carries str
        self.webkit.load_requested.connect(
            partial(self.address_bar.set_txt_color,
                    color=QColor(128, 128, 128)))

        def hide_message_label(*_):
            """ WARNING scrollRequested carries int, int, QRect;
            star swallows all

            """
            self.message_label.hide()

        self.webkit.page().scrollRequested.connect(hide_message_label)

        # focus_webkit (app defined) carries nothing
        self.webkit.hide_overlay.connect(self.message_label.hide)
        self.webkit.focus_webkit.connect(self.address_bar.restore)

        # progress bar
        self.pbar = QProgressBar(self)

        self.pbar.setRange(0, 100)
        self.pbar.setTextVisible(False)
        self.pbar.setVisible(False)
        self.pbar.setMaximumHeight(7)

        # search in page
        self.search_frame = SearchFrame(parent=self)  # NAV20
        # textChanged carries str
        self.search_frame.search_line.textChanged.connect(self.do_search)

        # layout
        grid = QGridLayout(self)
        grid.setSpacing(0)
        grid.setVerticalSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setRowStretch(1, 1)

        grid.addWidget(info_label, 0, 0, 1, 1)
        grid.addWidget(self.address_bar, 0, 1, 1, 1)
        grid.addWidget(self.nav_bar, 0, 2, 1, 1)

        grid.addWidget(self.webkit, 1, 0, 1, 3)

        grid.addWidget(self.search_frame, 2, 0, 1, 3)
        grid.addWidget(self.pbar, 3, 0, 1, 3)

        def show_search():
            """ One-time callback for QShortcut NAV20 """
            self.search_frame.setVisible(True)
            self.search_frame.search_line.setFocus()

        def hide_search():
            """ One-time callback for QShortcut NAV20 """
            self.search_frame.setVisible(False)
            self.webkit.findText("")
            self.webkit.setFocus()

        def navigate_completion(key=Qt.Key_Down):
            """ Sends an "arrow press" to the completion popup to navigate
            results.

            Not the best way to do this. It would be better to find out what
            function is being called by that arrow press.

            AB01

            """
            event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)

            self.address_bar.completer().popup().keyPressEvent(event)

        # the star swallows all arguments that aren't named 'store'
        def reset_addressbar(*, store=False):
            """ Restore the address bar to its original address and color (it
            could have changed because of a hover event).

            Optionally, store the original address in the clipboard.

            AB03

            """

            if self.current['address']:
                self.address_bar.set_txt_color(self.current['address'],
                                               color=QColor(0, 0, 0))

            if store:
                clipboard(self.current['address'])

        # urlChanged carries QUrl (ignored)
        self.webkit.urlChanged.connect(reset_addressbar)

        def enter_address_bar(clear=True):
            """ do not try entering the address bar if a load is in
            progress; do an 'stop' first

            AB00

            """

            if 'in_page_load' not in self.webkit.attr:
                if clear:
                    self.address_bar.clear_and_focus()
                else:
                    self.address_bar.setFocus()

        def cancel():
            """ if we're in the middle of loading the document, stop loading.
            Otherwise, hide the message label. The general concept is to reach
            a basic state.

            """

            if 'in_page_load' not in self.webkit.attr:
                self.message_label.hide()
                self.webkit.update()
            else:
                self.webkit.stop()

        set_shortcuts([
            # search NAV20
            ("G", self.webkit, show_search),
            ("Escape", self.search_frame, hide_search),
            ("Return", self.search_frame, self.do_search),
            ("Ctrl+J", self.search_frame, self.do_search),
            # go to page AB00
            ("Ctrl+J", self.address_bar, partial(
                self.webkit.navigate, self.address_bar)),
            ("Return", self.address_bar, partial(
                self.webkit.navigate, self.address_bar)),
            # address bar interaction
            ("A", self.webkit, cancel),
            ("Ctrl+L", self.webkit, enter_address_bar),  # AB00
            ("Ctrl+Shift+L", self.webkit, partial(
                enter_address_bar, clear=False)),
            ("Escape", self.address_bar, self.webkit.setFocus),  # AB00
            ("Ctrl+I", self.address_bar, navigate_completion),  # AB01
            ("Ctrl+P", self.address_bar, partial(
                navigate_completion, Qt.Key_Up)),
            # in-page element navigation
            ("Ñ", self, self.enter_nav),  # NAV11
            (";", self, self.enter_nav),
            # DOM01
            ("Ctrl+Ñ", self, partial(self.enter_nav, target="titles")),
            # toggle
            ("Q", self.webkit, self.toggle_script),  # TOG01
            # clipboard
            ("E", self, partial(reset_addressbar, store=True))  # CB05
            ])

    def enter_nav(self, target="links"):
        """ A request for access-key navigation was received; display
        link labels and go to the input area

        NAV11

        """

        self.webkit.make_labels(target)
        if self.webkit.map_tags:
            self.nav_bar.show()
            self.nav_bar.setFocus()

    def toggle_script(self):
        """ Retrieves the current javascript state for the tab and sets
        the opposite

        Callback for shortcut action

        TOG01

        """

        self.webkit.javascript(not self.webkit.javascript())

    def load_progress(self, val):
        """ Callback for connection """

        self.pbar.setValue(val)
        self.set_title("{}% {}".format(val, self.current['title']))

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
        self.set_title(self.current['title'])

        if self.address_bar.hasFocus():
            self.webkit.setFocus()

        if not success:
            notify("[F]")
            print("loadFinished: failed",
                  self.webkit.page().mainFrame().requestedUrl())

    # connect (en constructor)
    def save_title(self, title):
        """ Store a recently changed title, and display it """
        if title:
            self.current['title'] = title
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

        NAV20

        """
        if search is None:
            search = self.search_frame.search_line.text()
        self.webkit.findText(search, QWebPage.FindWrapsAroundDocument)


class SearchFrame(QFrame):
    """ A frame with a label and a text entry. The text is provided to
    the application upwards to perform in-page search.

    NAV20

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

        self.__completer = None
        self.__model = None

        self.__stored_text = ''
        self.__stored_color = QColor(0, 0, 0)

        # This first assignation is to allow a blank tab, who hasn't chosen yet
        # an instance, to display completions for all sites
        self.set_model(None)

        set_shortcuts([
            ("Ctrl+H", self, self.backspace),
            # do not create a new tab when on the address bar;
            # popup related trouble BF001
            ("Ctrl+T", self, lambda: None),
            ("Ctrl+Shift+T", self, lambda: None)
        ])

    def clear_and_focus(self):
        """ called by keybinding when edition of the address bar is requested

        AB00

        """

        self.clear()
        self.setFocus()

    def set_model(self, prefix):
        """ Update the completion model when the prefix is known. Has to
        be done through an instance variable because of a bug (will not
        complete the line edit otherwise)

        CFG02

        """

        # storage in __model is required because, apparently, the value
        # returned from DatabaseLogLite.model() is deleted somehow (not stored
        # anywhere) if used directly to set the QCompleter, disabling
        # completion silently
        self.__model = database().model(prefix)
        self.__completer = QCompleter(self.__model, self)
        self.setCompleter(self.__completer)

    def set_bgcolor(self, active):
        """ Sets the background color of the address bar; when 'active', that
        is, javascript is active, set to blue; set to white otherwise

        """

        palette = self.palette()
        (red, green, blue) = (230, 230, 255) if active else (255, 255, 255)
        palette.setColor(QPalette.Base, QColor(red, green, blue))
        self.setPalette(palette)

    def set_txt_color(self, text, color=QColor(127, 127, 255)):
        """ Write text on the address bar in the given color """

        self.__stored_color = color
        self.__stored_text = text

        # change the address bar's color to point out that we're in a
        # special state (waiting for load start, etc)
        palette = self.palette()
        palette.setColor(QPalette.Text, color)
        self.setPalette(palette)

        self.setText(text)

    def restore(self):
        """ After clearing out (or modifying) the address bar for text input,
        if cancelled, go back to the previous state

        AB03

        """

        self.set_txt_color(self.__stored_text, self.__stored_color)


class NavigateInput(QLineEdit):
    """ When access-key navigation starts, jump to a line edit, where it's
    easier to input the label name than intercepting keystrokes inside
    the web view

    NAV11 DOM01

    """

    def __init__(self, parent=None):
        super(NavigateInput, self).__init__(parent)

        set_shortcuts([
            ("Ctrl+H", self, self.backspace),
            ("Escape", self, self.exit)
        ])

        self.hide()

    def exit(self):
        """ We are (no matter how) done with the input area; clear and hide """

        self.clear()
        self.hide()

    def focus_out_event(self, _):
        """ If the line edit loses focus (either by regular means, or because
        it has been hidden by the app through the 'exit' method), notify
        the webkit

        """

        # it's ok to call twice if the event was result of calling 'exit', the
        # line edit is hidden now and will not send another event
        self.exit()
        self.editingFinished.emit()

    # Clean reimplement for Qt
    # pylint: disable=C0103
    focusOutEvent = focus_out_event
    # pylint: enable=C0103


class MessageLabel(QLabel):
    """ A label to be displayed on the top left corner of the webview;
    it performs most of the functions of a status bar

    Yellow, opaque, regular fonts, rectangle shaped due to setWordWrap

    """

    def __init__(self, parent=None):
        super(MessageLabel, self).__init__(parent)

        palette = QToolTip.palette()
        color = QColor(Qt.yellow)
        palette.setColor(QPalette.Window, color)

        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)

        self.setWordWrap(True)

        self.hide()
