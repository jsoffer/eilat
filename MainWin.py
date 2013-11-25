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

from PyQt4.Qt import QClipboard
from PyQt4.QtGui import QMainWindow, QTabWidget, QShortcut

from functools import partial

# local
from WebTab import WebTab

class MainWin(QMainWindow):
    """ Esta ventana guarda las tabs """
    def __init__(self, netmanager, clipboard):
        QMainWindow.__init__(self, None)
        self.netmanager = netmanager
        self.clipboard = clipboard
        self.actions = dict()
        self.appname = "Eilat Browser"
        self.tab_widget = QTabWidget(self)

        self.setWindowTitle(self.appname)
        self.tab_widget.tabBar().setMovable(True)
        self.setCentralWidget(self.tab_widget)
        self.tab_widget.setTabsClosable(True)

        self.tab_widget.tabCloseRequested.connect(self.del_tab)

        def new_tab_clipboard():
            """ One-use callback for QShortcut.
            Reads the content of the PRIMARY clipboard and navigates to it
            on a new tab.

            """
            url = unicode(self.clipboard.text(QClipboard.Selection)).strip()
            self.add_tab(url)

        for (shortcut, callback) in [
                ("Ctrl+T", self.add_tab),
                ("Y", new_tab_clipboard),
                ("Ctrl+W", self.del_tab),
                ("N", partial(self.inc_tab, -1)),
                ("Ctrl+PgUp", partial(self.inc_tab, -1)),
                ("M", self.inc_tab),
                ("Ctrl+PgDown", self.inc_tab),
                ("Ctrl+Q", self.close)
                ]:
            QShortcut(shortcut, self, callback)

    # aux. action (en register_actions)
    def inc_tab(self, incby = 1):
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
    def del_tab(self, idx = None):
        """ Closes a tab. If 'idx' is set, it was called by a
        tabCloseRequested signal. If not, it was called by a keyboard
        action and closes the currently active tab.

        Afterwards the active tab has focus on its webkit area.

        It closes the window when deleting the last active tab.

        """
        if not idx:
            idx = self.tab_widget.currentIndex()
        self.tab_widget.widget(idx).webkit.stop()
        self.tab_widget.widget(idx).deleteLater()
        self.tab_widget.removeTab(idx)
        if len(self.tab_widget) == 0:
            self.close()
        else:
            self.tab_widget.currentWidget().webkit.setFocus()

    # action (en register_actions)
    # externo en eilat.py, crea la primera tab
    def add_tab(self, url = None):
        """ Creates a new tab, either empty or navegating to the url.
        Sets itself as the active tab.

        If navegating to an url it gives focus to the webkit area. Otherwise,
        the address bar is focused.

        """
        tab = WebTab(browser=self, netmanager=self.netmanager)
        self.tab_widget.addTab(tab, "New tab")
        self.tab_widget.setCurrentWidget(tab)
        if url:
            tab.navigate(url)
        else:
            tab.address_bar.setFocus()

    # Implemented, it's recognized and runs at close
    #def closeEvent(self, e):
    #    print "MainWin.closeEvent"
    #    e.accept()
    #    self.close()
