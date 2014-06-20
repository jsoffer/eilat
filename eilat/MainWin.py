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

from PyQt4.QtGui import QMainWindow, QTabWidget, QTabBar
from PyQt4.QtCore import Qt

from functools import partial

# local
from eilat.WebTab import WebTab

from eilat.libeilat import fix_url, set_shortcuts, extract_url
from eilat.global_store import clipboard, close_managers

class MainWin(QMainWindow):
    """ It's a window, stores a TabWidget """

    def __init__(self, parent=None):
        super(MainWin, self).__init__(parent)
        self.setWindowTitle("Eilat Browser")

        self.last_closed = None

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabBar(MidClickTabBar())
        self.tab_widget.tabBar().setMovable(True)
        self.tab_widget.setTabsClosable(True)

        self.tab_widget.tabCloseRequested.connect(self.del_tab)

        self.setCentralWidget(self.tab_widget)

        def restore_last_closed():
            """ One-use callback for QShortcut.
            Opens a fresh new tab with the url address of the last tab closed
            """
            if self.last_closed is not None:
                url = self.last_closed
                self.add_tab(url)
                self.last_closed = None

        set_shortcuts([
            # new tabs
            ("Ctrl+T", self, self.add_tab),
            ("Ctrl+Shift+T", self, partial(self.add_tab, scripting=True)),
            ("Y", self, self.new_tab_from_clipboard),
            ("Ctrl+Y", self, partial(
                self.new_tab_from_clipboard, extract=True)),
            # movement
            ("M", self, self.inc_tab),
            ("N", self, partial(self.inc_tab, -1)),
            ("Ctrl+PgUp", self, partial(self.inc_tab, -1)),
            ("Ctrl+PgDown", self, self.inc_tab),
            # destroy/undestroy
            ("U", self, restore_last_closed),
            ("Ctrl+W", self, self.del_tab),
            ("Ctrl+Q", self, self.finalize)
            ])

    #def new_tab_from_clipboard(self, scripting=False, extract=False):
    def new_tab_from_clipboard(self, extract=False):
        """ One-use callback for QShortcut.
        Reads the content of the PRIMARY clipboard and navigates to it
        on a new tab.

        """

        url = clipboard()

        if extract:
            url = extract_url(url)

        if url is not None:
            self.add_tab(url)

    # aux. action (en register_actions)
    def inc_tab(self, incby=1):
        """ Takes the current tab index, modifies wrapping around,
        and sets as current.

        Afterwards the active tab has focus on its webkit area.

        """
        if self.tab_widget.count() < 2:
            return
        idx = self.tab_widget.currentIndex()
        idx += incby
        if idx < 0:
            idx = self.tab_widget.count()-1
        elif idx >= self.tab_widget.count():
            idx = 0
        self.tab_widget.setCurrentIndex(idx)
        self.tab_widget.currentWidget().webkit.setFocus()

    def finalize(self):
        """ Just doing self.close() doesn't clean up; for example, closing
        when the address bar popup is visible doesn't close the popup, and
        leaves the window hidden and unclosable (except e.g. for KILL 15)

        """

        idx = self.tab_widget.currentIndex()
        self.tab_widget.widget(idx).deleteLater()
        self.tab_widget.removeTab(idx)
        close_managers()
        self.close()

    # action y connect en llamada en constructor
    def del_tab(self, idx=None):
        """ Closes a tab. If 'idx' is set, it was called by a
        tabCloseRequested signal (maybe mid click). If not,
        it was called by a keyboard action and closes the
        currently active tab.

        Afterwards the active tab has focus on its webkit area.

        It closes the window when deleting the last active tab.

        """

        if idx is None:
            idx = self.tab_widget.currentIndex()
        self.tab_widget.widget(idx).webkit.stop()

        self.last_closed = self.tab_widget.widget(idx).webkit.url()

        self.tab_widget.widget(idx).deleteLater()
        self.tab_widget.removeTab(idx)
        if len(self.tab_widget) == 0:
            close_managers()
            self.close()
        else:
            self.tab_widget.currentWidget().webkit.setFocus()

    # action (en register_actions)
    # only way to create a new tab
    # called externally in eilat.py to create the first tab
    def add_tab(self, url=None, scripting=False):
        """ Creates a new tab, either empty or navegating to the url.
        Sets itself as the active tab.

        If navegating to an url it gives focus to the webkit area. Otherwise,
        the address bar is focused.

        """
        tab = WebTab(parent=self.tab_widget)

        self.tab_widget.addTab(tab, tab.current_title)

        self.tab_widget.setCurrentWidget(tab)
        tab_idx = self.tab_widget.indexOf(tab)

        self.tab_widget.tabBar().tabButton(tab_idx, 1).hide() # 1: right align

        if scripting:
            tab.toggle_script()

        if url is not None:
            qurl = fix_url(url)
            tab.webkit.navigate(qurl)
        else:
            tab.address_bar.setFocus()

class MidClickTabBar(QTabBar):
    """ Overloads middle click to close the clicked tab """
    def mouse_release_event(self, event):
        """ Emits the "close tab" signal if a middle click happened """
        if event.button() == Qt.MidButton:
            self.tabCloseRequested.emit(self.tabAt(event.pos()))
        super(MidClickTabBar, self).mouseReleaseEvent(event)

    # Clean reimplement for Qt
    # pylint: disable=C0103
    mouseReleaseEvent = mouse_release_event
    # pylint: enable=C0103
