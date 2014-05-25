# -*- coding: utf-8 -*-

"""

  Copyright (c) 2013, 2014 Jaime Soffer

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

from PyQt4.QtGui import QKeyEvent, QMouseEvent, QCursor, QApplication
from PyQt4.QtWebKit import QWebView, QWebElement
from PyQt4.QtCore import Qt, QEvent

from functools import partial

#from WebPage import WebPage
from libeilat import set_shortcuts

class WebView(QWebView):
    """ Una página web con contenedor, para poner en una tab

    """
    def __init__(self, netmanager, parent=None):
        super(WebView, self).__init__(parent)
        #self.setPage(WebPage()) # for custom user agents (disabled)
        self.paste = False
        self.save = False # here, just to get these two together

        #self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, False)
        #self.setRenderHint(QtWidgets.QPainter.HighQualityAntialiasing, True)

        # replace the Network Access Manager (log connections)
        if netmanager is not None:
            self.page().setNetworkAccessManager(netmanager)

        def handle_key(key):
            """ Generate a fake key click in the webkit """
            enter_event = QKeyEvent(
                    QEvent.KeyPress, key,
                    Qt.KeyboardModifiers())
            QApplication.sendEvent(self, enter_event)

        def handle_click():
            """ Generate a fake mouse click in the webkit """
            enter_event = QMouseEvent(
                    QEvent.MouseButtonPress,
                    self.mapFromGlobal(QCursor.pos()),
                    Qt.LeftButton,
                    Qt.MouseButtons(),
                    Qt.KeyboardModifiers())

            QApplication.sendEvent(self, enter_event)

            exit_event = QMouseEvent(
                    QEvent.MouseButtonRelease,
                    self.mapFromGlobal(QCursor.pos()),
                    Qt.LeftButton,
                    Qt.MouseButtons(),
                    Qt.KeyboardModifiers())

            QApplication.sendEvent(self, exit_event)

        def dump_dom():
            """ saves the content of the current web page """
            data = self.page().currentFrame().documentElement().toInnerXml()
            print("SAVING...")
            file_handle = open('test.html', 'w')
            file_handle.write(data)
            file_handle.close()

        set_shortcuts([
            ("Alt+Left", self, self.back),
            ("Alt+Right", self, self.forward),
            ("Ctrl+J", self, partial(handle_key, Qt.Key_Enter)),
            ("Ctrl+M", self, dump_dom),
            ("Ctrl+H", self, partial(handle_key, Qt.Key_Backspace)),
            ("Shift+H", self, partial(handle_key, Qt.Key_Left)),
            ("Shift+J", self, partial(handle_key, Qt.Key_Down)),
            ("Shift+K", self, partial(handle_key, Qt.Key_Up)),
            ("Shift+L", self, partial(handle_key, Qt.Key_Right)),
            ("C", self, handle_click),
            ("F5", self, self.reload),
            ("F2", self, self.del_fixed),
            ("R", self, self.reload)
            ])

    def del_fixed(self):
        """ Removes all 'div, header {position: fixed}' nodes """

        document = self.page().mainFrame().documentElement()
        nodes = document.findAll("div, header")
        #nodes = [node.removeFromDocument() for node in nodes if
        [node.setStyleProperty('position', 'absolute') for node in nodes if
                node.styleProperty(
                    "position",
                    QWebElement.ComputedStyle) == 'fixed']

    def set_paste(self):
        """ To use as callback in WebTab; can be improved """
        self.paste = True

    def set_save(self):
        """ To use as callback in WebTab; can be improved """
        self.save = True

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
