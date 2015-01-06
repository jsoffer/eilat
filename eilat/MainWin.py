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

from PyQt5.Qt import (QMainWindow, QTabWidget, QTabBar, QLabel, QToolTip,
                      QFrame)
from PyQt5.QtGui import (QColor, QPalette, QFont)
from PyQt5.QtCore import Qt, QTimer

from functools import partial

# local
from eilat.WebTab import WebTab

from eilat.libeilat import fix_url, set_shortcuts, notify
from eilat.global_store import clipboard, close_managers
from eilat.options import load_options, load_css

import gc
import sys

from collections import deque


class MainWin(QMainWindow):
    """ It's a window, stores a TabWidget """

    def __init__(self, parent=None):
        super(MainWin, self).__init__(parent)
        self.setWindowTitle("Eilat Browser")
        # gc.set_debug(gc.DEBUG_LEAK)

        self.last_closed = None

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabBar(MidClickTabBar())
        self.tab_widget.tabBar().setMovable(True)
        self.tab_widget.setTabsClosable(True)

        # the right side of the tab already has the space for
        # a non-shown close button
        self.tab_widget.setStyleSheet(
            'QTabBar::tab {padding-top: 0px; padding-bottom: 0px; '
            'padding-left: 0.3em;} '
            'QTabBar::tab:selected {color: #00f;}')

        # tabCloseRequested carries int (index of a tab)
        self.tab_widget.tabCloseRequested.connect(self.del_tab)

        self.setCentralWidget(self.tab_widget)

        self.tooltip = NotifyLabel(parent=self)

        def restore_last_closed():
            """ One-use callback for QShortcut.
            Opens a fresh new tab with the url address of the last tab closed
            """
            if self.last_closed is not None:
                url = self.last_closed
                self.add_tab(url)
                self.last_closed = None

        def dump_gc():
            """ prints sizes for large memory collectable objects """
            objs = gc.get_objects()
            pairs = [(str(k)[:80], type(k).__name__, sys.getsizeof(k))
                     for k in objs if sys.getsizeof(k) > 1024*4*5]

            for pair in pairs:
                print(pair)

        def reload_disk_init():
            """ transfer options.yaml and the css directory to global maps """
            load_options()
            load_css()
            notify("reloaded disk config")

        set_shortcuts([
            ("F9", self, dump_gc),
            # reload configuration
            ("Ctrl+Shift+R", self, reload_disk_init),
            # new tabs
            ("Ctrl+T", self, self.add_tab),
            ("Ctrl+Shift+T", self, partial(self.add_tab, scripting=True)),
            ("Y", self, self.new_tab_from_clipboard),
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

    def new_tab_from_clipboard(self):
        """ One-use callback for QShortcut.
        Reads the content of the PRIMARY clipboard and navigates to it
        on a new tab.

        """

        url = clipboard()

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

        Makes a hard app close through os._exit to prevent garbage collection;
        cleanup has typically done more harm than good. Any state that we may
        want to preserve we should do ourselves (e.g. cookies through the NAMs)

        """

        idx = self.tab_widget.currentIndex()
        self.tab_widget.widget(idx).deleteLater()
        self.tab_widget.removeTab(idx)
        close_managers()  # also does an os._exit

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

        self.tab_widget.addTab(tab, tab.current['title'])

        self.tab_widget.setCurrentWidget(tab)
        tab_idx = self.tab_widget.indexOf(tab)

        self.tab_widget.tabBar().tabButton(tab_idx, 1).hide()  # 1: right align

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
        return super(MidClickTabBar, self).mouseReleaseEvent(event)

    # Clean reimplement for Qt
    # pylint: disable=C0103
    mouseReleaseEvent = mouse_release_event
    # pylint: enable=C0103


class NotifyLabel(QLabel):
    """ A tooltip that can stack notifications """

    def __init__(self, parent=None):
        super(NotifyLabel, self).__init__(parent)

        palette = QToolTip.palette()
        color = QColor(Qt.blue)
        color = color.lighter(170)
        color.setAlpha(128)
        palette.setColor(QPalette.Window, color)

        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)

        self.setFont(QFont(None, 20, QFont.Bold))

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
