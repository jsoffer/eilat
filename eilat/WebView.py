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
from PyQt4.QtWebKit import QWebPage, QWebSettings, QWebView, QWebElement
from PyQt4.QtCore import Qt, QEvent, QUrl

from functools import partial

#from WebPage import WebPage
from libeilat import (set_shortcuts, node_neighborhood,
                      UP, DOWN, LEFT, RIGHT,
                      encode_css, real_host, copy_to_clipboard, osd)

from os.path import expanduser
from pprint import PrettyPrinter

class WebView(QWebView):
    """ Una página web con contenedor, para poner en una tab

    """
    def __init__(self, netmanager, parent=None):
        super(WebView, self).__init__(parent)
        #self.setPage(WebPage()) # for custom user agents (disabled)

        self.css_path = expanduser("~/.eilat/css/")

        self.paste = False
        self.save = False # here, just to get these two together

        self.navlist = []
        self.in_focus = None

        self.printer = PrettyPrinter(indent=4).pprint

        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

        self.settings().setAttribute(
            QWebSettings.PluginsEnabled, False)
        self.settings().setAttribute(
            QWebSettings.JavascriptEnabled, False)
        self.settings().setAttribute(
            QWebSettings.SpatialNavigationEnabled, True)
        self.settings().setAttribute(
            QWebSettings.FrameFlatteningEnabled, True)

        self.page().setForwardUnsupportedContent(True)

        def url_changed(qurl):
            """ One time callback for 'connect'
            Sets the user style sheet, sets the address bar text

            """
            host_id = real_host(qurl.host())
            css_file = self.css_path + host_id + ".css"

            try:
                with open(css_file, 'r') as css_fh:
                    css_encoded = encode_css(css_fh.read()).strip()
            except IOError:
                css_encoded = encode_css('')

            self.settings().setUserStyleSheetUrl(
                QUrl(css_encoded))
            self.parent().address_bar.setText(qurl.toString())

        self.urlChanged.connect(url_changed)

        def process_clipboard(notify, request):
            """ notify and save to clipboard """
            message = request.url().toString() + "\n" + notify
            osd(message)
            copy_to_clipboard(request)

        self.page().downloadRequested.connect(partial(
            process_clipboard, "Download Requested"))
        self.page().unsupportedContent.connect(partial(
            process_clipboard, "Unsupported Content"))

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
            ("Shift+H", self, partial(self.spatialnav, LEFT)),
            ("Shift+J", self, partial(self.spatialnav, DOWN)),
            ("Shift+K", self, partial(self.spatialnav, UP)),
            ("Shift+L", self, partial(self.spatialnav, RIGHT)),
            # clipboard related behavior
            ("I", self, set_paste),
            ("S", self, set_save)
            ])

    def unembed_frames(self):
        """ Replaces the content of iframes with a link to their source

        """

        frame = self.page().mainFrame()
        nodes = [node for node in frame.findAllElements("iframe[src]")]
        for node in nodes:
            url = node.attribute('src')
            node.setOuterXml("""<a href="%s">%s</a>""" % (url, url))

        # We've added a[href] nodes to the page... rebuild the navigation list
        self.navlist = []

    def delete_fixed(self, delete=True):
        """ Removes all '??? {position: fixed}' nodes """

        frame = self.page().mainFrame()
        fixables = "div, header, footer, nav"
        nodes = [node for node in frame.findAllElements(fixables)
                 if node.styleProperty("position",
                                       QWebElement.ComputedStyle) == 'fixed']

        for node in nodes:
            if delete:
                node.removeFromDocument()
            else:
                node.setStyleProperty('position', 'absolute')

    def populate_navlist(self):
        """ Fill the spatial navigation list with the current mainFrame
        anchor links

        If it already exists and has content, do nothing; the list has to
        be cleared when navigating or reloading a page
        """

        if not self.navlist:
            print("INIT self.navlist for url")
            frame = self.page().mainFrame()
            self.navlist = [node for node
                            in frame.findAllElements("a[href]").toList()
                            if node.geometry() and
                            node.styleProperty(
                                "visibility",
                                QWebElement.ComputedStyle) == 'visible' and
                            node.attribute("href") != "#" and
                            not node.attribute("href").startswith(
                                "javascript:")]

        if not self.navlist:
            print("No anchors in this page, at all?")

    def spatialnav(self, direction):
        """ find web link nodes, move through them;
        initial testing to replace webkit's spatial navigation

        """

        # updating every time; not needed unless scroll or resize
        # but maybe tracking scroll/resize is more expensive...
        view_geom = self.page().mainFrame().geometry()
        view_geom.translate(self.page().mainFrame().scrollPosition())

        self.populate_navlist()

        # just for this time; which nodes from the entire page are, in any way,
        # visible right now?
        localnav = [node for node in self.navlist
                    if view_geom.intersects(node.geometry())]

        if not self.navlist or not localnav:
            print("No anchors in current view?")
            return

        # find the best node to move to
        if self.in_focus in localnav:

            geom = self.in_focus.geometry()

            neighborhood = node_neighborhood(geom, direction)

            # 'mininav' is a list of the nodes close to the focused one,
            # on the relevant direction
            mininav = [node for node in localnav
                       if node != self.in_focus and
                       not node.geometry().contains(geom) and
                       neighborhood.intersects(node.geometry())]

            #print("mininav: ", str([node.toPlainText() for node in mininav]),
            #      str(self.in_focus.geometry()), str(neighborhood))

        if self.in_focus in localnav:
            self.next_node(localnav, mininav, direction)
        else:
            if direction == UP or direction == LEFT:
                self.in_focus = max(localnav, key=lambda node:
                                    node.geometry().bottom())
            else:
                self.in_focus = min(localnav, key=lambda node:
                                    node.geometry().top())

        # We're done, we have a node to focus; focus it, bind to status bar
        self.parent().statusbar.showMessage(
            str(self.in_focus.geometry()) + " " +
            self.in_focus.attribute("href")
        )

        self.in_focus.setFocus()

    def next_node(self, localnav, mininav, direction):
        """ Finds and sets a next node appropiate to the chosen direction,
        first on a neighborhood and then using modified manhattan distance

        """

        manhattan_x = 95
        manhattan_y = 15

        geom = self.in_focus.geometry()

        if direction == RIGHT:
            if mininav:
                self.in_focus = min(
                    mininav, key=lambda node: node.geometry().left())
            else:
                region = [node for node in localnav
                          if node.geometry().left() > geom.right()]

                self.in_focus = self.in_focus if not region else (
                    min(region, key=partial(self.node_manhattan,
                                            xfactor=manhattan_x,
                                            yfactor=manhattan_y)))

        elif direction == LEFT:
            if mininav:
                self.in_focus = min(
                    mininav, key=lambda node: node.geometry().right())
                self.in_focus = mininav[-1]
            else:
                region = [node for node in localnav
                          if node.geometry().right() < geom.left()]

                self.in_focus = self.in_focus if not region else (
                    min(region, key=partial(self.node_manhattan,
                                            xfactor=manhattan_x,
                                            yfactor=manhattan_y)))

        elif direction == DOWN:
            if mininav:
                self.in_focus = min(
                    mininav, key=lambda node: node.geometry().top())
            else:
                region = [node for node in localnav
                          if node.geometry().top() > geom.top() and
                          not node.geometry().contains(geom) and
                          abs(geom.bottom() - node.geometry().bottom()) > 8]
                region.sort(key=partial(self.node_manhattan,
                                        xfactor=manhattan_x,
                                        yfactor=manhattan_y))
                self.in_focus = self.in_focus if not region else region[0]

        # up
        else:
            if mininav:
                mininav.sort(key=lambda node: node.geometry().bottom())
                self.in_focus = max(
                    mininav, key=lambda node: node.geometry().bottom())
            else:
                region = [node for node in localnav
                          if node.geometry().bottom() < geom.bottom() and
                          not node.geometry().contains(geom) and
                          abs(geom.bottom() - node.geometry().bottom()) > 8]
                region.sort(key=partial(self.node_manhattan,
                                        xfactor=manhattan_x,
                                        yfactor=manhattan_y))
                self.in_focus = self.in_focus if not region else region[0]

    def node_manhattan(self, node, xfactor=1, yfactor=1):
        """ Calculates the least possible L1 distance between the focused node
        and another one

        """

        geom = node.geometry()
        f_geom = self.in_focus.geometry()

        top = geom.top()
        f_top = f_geom.top()
        bottom = geom.bottom()
        f_bottom = f_geom.bottom()
        left = geom.left()
        f_left = f_geom.left()
        right = geom.right()
        f_right = f_geom.right()

        return (
            min(abs(top - f_top),
                abs(bottom - f_bottom),
                abs(top - f_bottom),
                abs(bottom - f_top)) * xfactor +
            min(abs(left - f_left),
                abs(right - f_right),
                abs(left - f_right),
                abs(right - f_left)) * yfactor)

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
