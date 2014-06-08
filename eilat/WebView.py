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

from pprint import PrettyPrinter

class WebView(QWebView):
    """ Una página web con contenedor, para poner en una tab

    """
    def __init__(self, netmanager, parent=None):
        super(WebView, self).__init__(parent)
        #self.setPage(WebPage()) # for custom user agents (disabled)
        self.paste = False
        self.save = False # here, just to get these two together

        self.testnav = []
        self.localnav = []
        self.in_focus = None

        self.printer = PrettyPrinter(indent=4).pprint

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

        def scroll(delta_x=0, delta_y=0):
            """ One-time callback for QShortcut """
            self.page().mainFrame().scroll(delta_x, delta_y)

        def zoom(lvl):
            """ One-time callback for QShortcut """
            factor = self.zoomFactor() + (lvl * 0.25)
            self.setZoomFactor(factor)

        def set_paste():
            """ To use as callback in WebTab; can be improved """
            self.paste = True

        def set_save():
            """ To use as callback in WebTab; can be improved """
            self.save = True

        def clear_focused():
            """ Clears known focused, forcing a rechoice;
            does not remove focus

            """
            self.in_focus = None

        set_shortcuts([
            # DOM actions
            ("Ctrl+M", self, dump_dom),
            ("F", self, self.unembed_frames),
            ("F2", self, self.delete_fixed),
            ("F7", self, self.test_nav_w),
            ("F8", self, partial(self.test_nav_w, reverse=True)),
            ("Shift+F2", self, partial(self.delete_fixed, delete=False)),
            # webkit interaction
            ("Alt+Left", self, self.back),
            ("Alt+Right", self, self.forward),
            ("F5", self, self.reload),
            ("R", self, self.reload),
            # view interaction
            ("J", self, partial(scroll, delta_y=40)),
            ("K", self, partial(scroll, delta_y=-40)),
            ("H", self, partial(scroll, delta_x=-40)),
            ("L", self, partial(scroll, delta_x=40)),
            ("Ctrl+Up", self, partial(zoom, 1)),
            ("Ctrl+Down", self, partial(zoom, -1)),
            ("Ctrl+J", self, partial(handle_key, Qt.Key_Enter)),
            ("Ctrl+H", self, partial(handle_key, Qt.Key_Backspace)),
            ("C", self, handle_click),
            # spatial navigation
            ("Ctrl+Shift+H", self, partial(handle_key, Qt.Key_Left)),
            ("Ctrl+Shift+J", self, partial(handle_key, Qt.Key_Down)),
            ("Ctrl+Shift+K", self, partial(handle_key, Qt.Key_Up)),
            ("Ctrl+Shift+L", self, partial(handle_key, Qt.Key_Right)),
            ("Shift+I", self, clear_focused),
            ("Shift+H", self, partial(self.test_nav_w, True, True)),
            ("Shift+J", self, partial(self.test_nav_w, False, False)),
            ("Shift+K", self, partial(self.test_nav_w, False, True)),
            ("Shift+L", self, partial(self.test_nav_w, True, False)),
            # clipboard related behavior
            ("I", self, set_paste),
            ("S", self, set_save)
            ])

    def unembed_frames(self):
        """ Replaces the content of iframes with a link to their source

        """

        document = self.page().mainFrame().documentElement()
        nodes = [node for node in document.findAll("iframe[src]")]
        for node in nodes:
            url = node.attribute('src')
            node.setOuterXml("""<a href="%s">%s</a>""" % (url, url))

    def delete_fixed(self, delete=True):
        """ Removes all '??? {position: fixed}' nodes """

        document = self.page().mainFrame().documentElement()
        nodes = [node for node in document.findAll("div, header, nav")
                 if node.styleProperty(
                     "position",
                     QWebElement.ComputedStyle) == 'fixed']

        for node in nodes:
            if delete:
                node.removeFromDocument()
            else:
                node.setStyleProperty('position', 'absolute')

    def test_nav_w(self, x_axis=True, reverse=False):
        """ find web link nodes, move through them;
        initial testing to replace webkit's spatial navigation

        """

        # updating every time; not needed unless scroll or resize
        # but maybe tracking scroll/resize is more expensive...
        geom = self.page().mainFrame().geometry()
        geom.translate(self.page().mainFrame().scrollPosition())

        if not self.testnav:
            print("INIT self.testnav for url")
            document = self.page().mainFrame().documentElement()
            self.testnav = [node for node
                            in document.findAll("a[href]").toList()
                            if node.geometry() and
                            node.styleProperty(
                                "visibility",
                                QWebElement.ComputedStyle) == 'visible' and
                            node.attribute("href") != "#" and
                            not node.attribute("href").startswith(
                                "javascript:")]

        if not self.testnav:
            print("No anchors - at all?")
            return

        # rebuilt it whole; there are less expensive methods, for
        # now it's enough if it works
        self.localnav = [node for node in self.testnav
                         if geom.intersect(node.geometry())]

        self.localnav.sort(
            key=(lambda node: (node.geometry().y(),
                               node.geometry().x())))

        if not self.localnav:
            print("No anchors in current view?")
            return

        # transform

        if self.in_focus in self.localnav:
            #top = self.in_focus.geometry().top()
            #bottom = self.in_focus.geometry().bottom()
            center = self.in_focus.geometry().center().y()
            if x_axis:
                row = [node for node in self.localnav
                       if center == node.geometry().center().y()]
                idx = row.index(self.in_focus)
                if reverse:
                    self.in_focus = row[idx - 1]
                else:
                    try:
                        self.in_focus = row[idx + 1]
                    except IndexError:
                        self.in_focus = row[0]
            else:
                if reverse:
                    region = [node for node in self.localnav
                              if node.geometry().center().y() < center]
                    if region:
                        region.sort(
                            key=(lambda node: node.geometry().center().y()))
                        self.in_focus = region[-1]
                else:
                    region = [node for node in self.localnav
                              if node.geometry().center().y() > center]
                    if region:
                        region.sort(
                            key=(lambda node: node.geometry().center().y()))
                        self.in_focus = region[0]

        else:
            if reverse:
                self.in_focus = self.localnav[-1]
            else:
                self.in_focus = self.localnav[0]

        self.parent().statusbar.showMessage(
            str(self.in_focus.geometry()) + " " +
            str(self.in_focus.geometry().center()) + " " +
            self.in_focus.attribute("href")
        )

        self.in_focus.setFocus()

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
