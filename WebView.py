# -*- coding: utf-8 -*-

"""

  Copyright (c) 2013, Jaime Soffer

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

from PyQt4.QtWebKit import QWebView
from PyQt4.QtCore import Qt, QEvent
import PyQt4.QtGui as QtGui

from libeilat import log

class WebView(QWebView):
    """ Una página web con contenedor, para poner en una tab

    """
    def __init__(self, netmanager, parent = None):
        super(WebView, self).__init__(parent)
        self.paste = False

        self.page().downloadRequested.connect(
                lambda k: log("D: " + k.url().toString()))
        self.page().unsupportedContent.connect(
                lambda k: log("U: " + k.url().toString()))

        self.page().setForwardUnsupportedContent(True)

        # replace the Network Access Manager (log connections)
        self.page().setNetworkAccessManager(netmanager)

        def handle_enter():
            """ Generate a fake Enter in the webkit, to send a form """
            enter_event = QtGui.QKeyEvent(
                    QEvent.KeyPress, Qt.Key_Enter, Qt.KeyboardModifiers())
            QtGui.QApplication.sendEvent(self, enter_event)

        for (shortcut, callback) in [
                ("Alt+Left", self.back),
                ("Alt+Right", self.forward),
                ("Ctrl+J", handle_enter),
                ("F5", self.reload),
                ("R", self.reload)
                ]:
            QtGui.QShortcut(
                    shortcut, self, callback
                    ).setContext(
                            Qt.WidgetWithChildrenShortcut)

    def mouse_press_event(self, event):
        """ Reimplementation from base class. Detects middle clicks
        and sets self.paste

        """
        self.paste = (event.buttons() & Qt.MiddleButton)
        return QWebView.mousePressEvent(self, event)

    # Clean reimplement for Qt
    # pylint: disable=C0103
    mousePressEvent = mouse_press_event
    # pylint: enable=C0103
