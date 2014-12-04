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

from PyQt4.QtGui import (QWidget, QProgressBar, QGridLayout,
                         QFrame, QLabel, QLineEdit, QCompleter, QKeyEvent,
                         QPalette, QColor, QToolTip)
from PyQt4.QtWebKit import QWebPage
from PyQt4.QtCore import Qt, QEvent

from PyQt4.Qt import QApplication

from functools import partial

# local
from eilat.WebView import WebView
from eilat.DatabaseLog import DatabaseLogLite
from eilat.libeilat import set_shortcuts, notify
from eilat.global_store import mainwin, clipboard

class WebTab(QWidget):
    """ Cada tab contiene una página web """
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

        self.webkit.set_prefix.connect(self.address_bar.set_model)
        self.webkit.javascript_state.connect(self.address_bar.set_color)

        # small label displaying instance ID and pending tab operations

        info_label = QLabel(parent=self)
        info_label.setText('?')

        self.webkit.webkit_info.connect(info_label.setText)

        def update_address(qurl):
            """ The 'connect' gives a QUrl and setText receives a string;
            can't just connect setText

            Required because a 3XX HTTP redirection will change the address,
            and without updating, the address bar will be left stale

            """
            self.current['address'] = qurl.toString()
            self.address_bar.setText(self.current['address'])

        self.webkit.urlChanged.connect(update_address)
        self.webkit.loadStarted.connect(self.load_started)
        self.webkit.loadFinished.connect(self.load_finished)
        self.webkit.titleChanged.connect(self.save_title)
        self.webkit.loadProgress.connect(self.load_progress)

        def fill_notifier(message, request):
            """ sends a message to be displayed by the notifier, and starts a
            timer to hide it after eight seconds

            """
            notify(message + " " + request.url().toString())

        self.webkit.page().downloadRequested.connect(
            partial(fill_notifier, "download"))
        self.webkit.page().unsupportedContent.connect(
            partial(fill_notifier, "unsupported"))

        # input area for access-key navigation

        self.nav_bar = NavigateInput(parent=self)
        self.nav_bar.editingFinished.connect(self.webkit.clear_labels)

        self.nav_bar.textEdited.connect(self.webkit.akeynav)
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

        self.webkit.page().linkHovered.connect(handle_hovered)

        def handle_signaled(title):
            """ We received a string through a signal; display it on
            the message label

            """

            #if title:
            self.message_label.hide()
            self.message_label.setText(title)
            self.message_label.show()

        self.webkit.display_title.connect(handle_signaled)

        self.webkit.loadStarted.connect(self.message_label.hide)
        self.webkit.page().scrollRequested.connect(self.message_label.hide)
        self.webkit.hide_overlay.connect(self.message_label.hide)

        # progress bar
        self.pbar = QProgressBar(self)

        self.pbar.setRange(0, 100)
        self.pbar.setTextVisible(False)
        self.pbar.setVisible(False)
        self.pbar.setMaximumHeight(7)

        # search in page
        self.search_frame = SearchFrame(parent=self)

        self.webkit.link_selected.connect(self.on_link_hovered)

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

        def reset_addressbar(store=False):
            """ Restore the address bar to its original address and color (it
            could have changed because of a hover event).

            Optionally, store the original address in the clipboard.

            """

            palette = self.address_bar.palette()
            palette.setColor(QPalette.Text, QColor(0, 0, 0))
            self.address_bar.setPalette(palette)

            if self.current['address']:
                self.address_bar.setText(self.current['address'])

            if store:
                clipboard(self.current['address'])

        self.webkit.loadStarted.connect(reset_addressbar)

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
            # in-page element navigation
            ("Ñ", self, self.enter_nav),
            (";", self, self.enter_nav),
            ("Ctrl+Ñ", self, partial(self.enter_nav, target="titles")),
            # toggle
            ("Q", self.webkit, self.toggle_script),
            # clipboard
            ("E", self, partial(reset_addressbar, store=True))
            ])

    def enter_nav(self, target="links"):
        """ A request for access-key navigation was received; display
        link labels and go to the input area

        """

        self.webkit.make_labels(target)
        if self.webkit.map_tags:
            self.nav_bar.show()
            self.nav_bar.setFocus()

    def toggle_script(self):
        """ Activa o desactiva javascript, y notifica cambiando el color
        del address bar

        Callback for shortcut action
        """

        # FIXME needed here? Only place where .javascript() needs
        # to be public. Mainly for address_bar's color (using signals now)
        javascript_on = self.webkit.javascript()
        self.webkit.javascript(not javascript_on)

    def load_progress(self, val):
        """ Callback for connection """
        if self.pbar.isVisible():
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
            print("loadFinished: failed", self.webkit.url())


    # connect (en constructor)
    def on_link_hovered(self, link):
        """ A link has been selected (no relation with legacy 'link hovered').
        Display the href (if there's no href, it's '') on the (pseudo) status
        bar.

        """


        # change the address bar's color to point out that we're in a
        # pseudo status bar, not the regular address bar
        palette = self.address_bar.palette()
        palette.setColor(QPalette.Text, QColor(127, 127, 255))
        self.address_bar.setPalette(palette)

        self.address_bar.setText(link)

        # if used, overwrites the clipboard every time navigation is performed,
        # either access-key or spatial
        # clipboard(link)

    # connect (en constructor)

    def save_title(self, title):
        """ Store a recently changed title, and display it """
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

        # This first assignation is to allow a blank tab, who hasn't chosen yet
        # an instance, to display completions for all sites
        self.set_model(None)

        set_shortcuts([
            ("Ctrl+H", self, self.backspace),
            # do not create a new tab when on the address bar;
            # popup related trouble
            ("Ctrl+T", self, lambda: None),
            ("Ctrl+Shift+T", self, lambda: None)
        ])

    def focus_in_event(self, event):
        """ Reset the address bar's color if entering; because the
        pseudo-status-bar color is not valid anymore

        """

        palette = self.palette()
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        self.setPalette(palette)
        QLineEdit.focusInEvent(self, event)


    def set_model(self, prefix):
        """ Update the completion model when the prefix is known. Has to
        be done through an instance variable because of a bug (will not
        complete the line edit otherwise)

        """
        self.__completer = QCompleter(self.database.model(prefix), self)
        self.setCompleter(self.__completer)

    def set_color(self, active):
        """ Sets the background color of the address bar; when 'active', that
        is, javascript is active, set to blue; set to white otherwise

        """

        palette = self.palette()
        (red, green, blue) = (230, 230, 255) if active else (255, 255, 255)
        palette.setColor(QPalette.Base, QColor(red, green, blue))
        self.setPalette(palette)

    # Clean reimplement for Qt
    # pylint: disable=C0103
    focusInEvent = focus_in_event
    # pylint: enable=C0103

class NavigateInput(QLineEdit):
    """ When access-key navigation starts, jump to a line edit, where it's
    easier to input the label name than intercepting keystrokes inside
    the web view

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
        it has been hidden by 'exit'), notify the webkit

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

