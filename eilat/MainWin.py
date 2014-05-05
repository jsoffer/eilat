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

from PyQt4.Qt import QClipboard
from PyQt4.QtGui import QMainWindow, QTabWidget, QApplication, QTabBar
from PyQt4.QtCore import Qt

from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel

from functools import partial

# local
from WebTab import WebTab
from libeilat import set_shortcuts

from os.path import expanduser

class MainWin(QMainWindow):
    """ Esta ventana guarda las tabs """
    def __init__(self, netmanager, clipboard, log=None, parent=None):
        super(MainWin, self).__init__(parent)
        if netmanager is not None:
            self.setWindowTitle("Eilat Browser " + netmanager.name)
        else:
            self.setWindowTitle("TESTING Eilat Browser")

        self.log = log

        self.last_closed = None
        self.css_path = expanduser("~/.css/")

        self.netmanager = netmanager
        self.clipboard = clipboard

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabBar(MidClickTabBar())
        self.tab_widget.tabBar().setMovable(True)
        self.setCentralWidget(self.tab_widget)
        self.tab_widget.setTabsClosable(True)

        database = QSqlDatabase("QPSQL")
        database.open("pguser", "pgpass")

        self.litedb = QSqlDatabase("QSQLITE")
        self.litedb.setDatabaseName("eilat.db")
        self.litedb.open()

        query = QSqlQuery(
                "select concat(regexp_replace(host,  '^www.', ''), " +
                "regexp_replace(path, '/$', '')) h, " +
                "count(*) c from navigation where query is null "
                "and not longpath(regexp_replace(path, '/$', '')) " +
                "group by h order by c desc", database)

        self.model = QSqlQueryModel()
        self.model.setQuery(query)

        self.tab_widget.tabCloseRequested.connect(self.del_tab)

        def new_tab_from_clipboard(scripting=False):
            """ One-use callback for QShortcut.
            Reads the content of the PRIMARY clipboard and navigates to it
            on a new tab.

            """
            if self.clipboard is not None:
                url = unicode(self.clipboard.text(
                    mode=QClipboard.Selection)).strip()
                self.add_tab(url, scripting)

        def restore_last_closed():
            """ One-use callback for QShortcut.
            Opens a fresh new tab with the url address of the last tab closed
            """
            if self.last_closed is not None:
                url = self.last_closed
                self.add_tab(url)
                self.last_closed = None

        set_shortcuts([
            ("Ctrl+T", self, self.add_tab),
            ("Ctrl+Shift+T", self, partial(self.add_tab, scripting=True)),
            ("Y", self, new_tab_from_clipboard),
            ("Shift+Y", self, partial(new_tab_from_clipboard, scripting=True)),
            ("U", self, restore_last_closed),
            ("Ctrl+W", self, self.del_tab),
            ("N", self, partial(self.inc_tab, -1)),
            ("Ctrl+PgUp", self, partial(self.inc_tab, -1)),
            ("M", self, self.inc_tab),
            ("Ctrl+PgDown", self, self.inc_tab),
            ("Ctrl+Q", self, QApplication.closeAllWindows)
            ])

    def register_nav(self, host, path):
        """ FIXME wrong place, testing """

        lite_q1 = (
                "insert or ignore into navigation (host, path) " +
                "values (\"" + host + "\", \"" + path + "\")")

        lite_q2 = (
                "update navigation set count = count + 1 where " +
                "host = \"" + host + "\" and path = \"" + path + "\"")

        self.litedb.exec_(lite_q1)
        self.litedb.exec_(lite_q2)


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

    # action y connect en llamada en constructor
    def del_tab(self, idx=None):
        """ Closes a tab. If 'idx' is set, it was called by a
        tabCloseRequested signal. If not, it was called by a keyboard
        action and closes the currently active tab.

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
            self.close()
        else:
            self.tab_widget.currentWidget().webkit.setFocus()

    # action (en register_actions)
    # only way to create a new tab on the browser
    # externo en eilat.py, crea la primera tab
    def add_tab(self, url=None, scripting=False):
        """ Creates a new tab, either empty or navegating to the url.
        Sets itself as the active tab.

        If navegating to an url it gives focus to the webkit area. Otherwise,
        the address bar is focused.

        """
        tab = WebTab(browser=self, parent=self.tab_widget)

        self.tab_widget.addTab(tab, "New tab")

        self.tab_widget.setCurrentWidget(tab)
        tab_idx = self.tab_widget.indexOf(tab)

        self.tab_widget.tabBar().tabButton(tab_idx, 1).hide() # 1: right align

        if scripting:
            tab.toggle_script()
        if url:
            tab.navigate(url)
        else:
            tab.address_bar.setFocus()

    # Implemented, it's recognized and runs at close
    #def closeEvent(self, e):
    #    print "MainWin.closeEvent"
    #    e.accept()
    #    self.close()

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
