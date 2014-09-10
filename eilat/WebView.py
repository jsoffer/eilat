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

from PyQt4.QtWebKit import QWebPage, QWebSettings, QWebView, QWebElement
from PyQt4.QtCore import Qt, QUrl, pyqtSignal, QPoint

from PyQt4.QtGui import QLabel, QColor, QToolTip, QPalette, QFrame

from functools import partial

#from WebPage import WebPage
from eilat.InterceptNAM import InterceptNAM
from eilat.libeilat import (fix_url, set_shortcuts, node_neighborhood,
                            UP, DOWN, LEFT, RIGHT,
                            encode_css, real_host, toggle_show_logs,
                            fake_key, fake_click)
from eilat.global_store import (mainwin, clipboard, database,
                                has_manager, register_manager, get_manager)
from eilat.options import extract_options

from os.path import expanduser
from re import sub
import datetime

from threading import Thread
from subprocess import Popen

from colorama import Fore

import string
import itertools

ALL_TAGS = [p + q for (p, q) in
            itertools.product(['', 'G', 'H', 'F', 'J'],
                              [k for k in
                               string.ascii_uppercase + string.digits])]

# make the prefix keys special, so it's possible to one-key most links
# on a low-population page; can be improved (as can the distribution too) by
# making ALL_TAGS a function depending on the number of links in the page

ALL_TAGS.remove('G')
ALL_TAGS.remove('H')
ALL_TAGS.remove('F')
ALL_TAGS.remove('J')

def play_mpv(qurl):
    """ Will try to open an 'mpv' instance running the video pointed at
    in 'qurl'. Warns if 'mpv' is not installed or available.

    To be executed in a separate thread. That way, 'wait' will not block.

    """

    try:
        process = Popen(['mpv', qurl.toString()])
        process.wait() # wait, or mpv will be <defunct> after exiting!
    except FileNotFoundError:
        print("'mpv' video player not available")

class WebView(QWebView):
    """ Una página web con contenedor, para poner en una tab

    """

    prefix_set = pyqtSignal(str)

    def __init__(self, parent=None):
        super(WebView, self).__init__(parent)

        self.prefix = None

        self.css_path = expanduser("~/.eilat/css/")

        self.attributes = set()

        self.navlist = []
        self.in_focus = None

        self.labels = []
        self.map_tags = {}

        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

        self.settings().setAttribute(
            QWebSettings.PluginsEnabled, False)
        self.settings().setAttribute(
            QWebSettings.JavascriptEnabled, False)
        #self.settings().setAttribute(
        #    QWebSettings.SpatialNavigationEnabled, True)
        self.settings().setAttribute(
            QWebSettings.FrameFlatteningEnabled, True)

        self.page().setForwardUnsupportedContent(True)

        # connect (en constructor)
        def on_link_click(qurl):
            """ Callback for connection. Reads the 'paste' attribute
            to know if a middle click requested to open on a new tab.

            """
            if 'paste' in self.attributes:
                mainwin().add_tab(qurl,
                                  scripting=(
                                      'open_scripted' in self.attributes))
                self.attributes.discard('paste')
            else:
                self.navigate(qurl)
            self.attributes.discard('open_scripted')

        self.linkClicked.connect(on_link_click)

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

        self.urlChanged.connect(url_changed)

        self.page().downloadRequested.connect(partial(clipboard))
        self.page().unsupportedContent.connect(partial(clipboard))

        def clear_labels():
            """ clear the access-key navigation labels """

            if self.labels:
                for label in self.labels:
                    label.hide()
                    label.deleteLater()
                self.labels = []
                self.update()

        self.page().scrollRequested.connect(clear_labels)
        self.page().loadStarted.connect(clear_labels)

        #self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, False)
        #self.setRenderHint(QtWidgets.QPainter.HighQualityAntialiasing, True)

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

        set_shortcuts([
            # DOM actions
            ("Ctrl+M", self, dump_dom),
            ("F", self, self.__unembed_frames),
            ("F2", self, self.__delete_fixed),
            ("Shift+F2", self, partial(self.__delete_fixed, delete=False)),
            # webkit interaction
            ("Alt+Left", self, self.back),
            ("Alt+Right", self, self.forward),
            ("F5", self, self.reload),
            ("R", self, self.reload),
            # view interaction
            ("J", self, partial(scroll, delta_y=40)),
            ("Z", self, partial(scroll, delta_y=40)),
            ("K", self, partial(scroll, delta_y=-40)),
            ("X", self, partial(scroll, delta_y=-40)),
            ("H", self, partial(scroll, delta_x=-40)),
            ("L", self, partial(scroll, delta_x=40)),
            ("Ctrl+Up", self, partial(zoom, 1)),
            ("Ctrl+Down", self, partial(zoom, -1)),
            ("Ctrl+J", self, partial(fake_key, self, Qt.Key_Enter)),
            ("Ctrl+H", self, partial(fake_key, self, Qt.Key_Backspace)),
            ("C", self, partial(fake_click, self)),
            # spatial navigation
            ("Shift+I", self, partial(setattr, self, 'in_focus', None)),
            ("Shift+H", self, partial(self.__spatialnav, LEFT)),
            ("Shift+J", self, partial(self.__spatialnav, DOWN)),
            ("Shift+K", self, partial(self.__spatialnav, UP)),
            ("Shift+L", self, partial(self.__spatialnav, RIGHT)),
            # toggles
            # right now self.prefix is None; lambda allows to retrieve the
            # value it will have when toggle_show_logs is called
            ("F11", self, partial(
                toggle_show_logs, lambda: self.prefix, detail=True)),
            ("Shift+F11", self, partial(
                toggle_show_logs, lambda: self.prefix)),
            # clipboard related behavior
            ("I", self, partial(self.attributes.add, 'paste')),
            ("O", self, partial(self.attributes.add, 'open_scripted')),
            ("S", self, partial(self.attributes.add, 'save')),
            ("V", self, partial(self.attributes.add, 'play'))
            ])

    # action (en register_actions)
    def navigate(self, request=None):
        """ Open the url on this tab. If 'url' is already a QUrl
        (if it comes from a href click), just send it. Otherwise,
        it comes either from the address bar or the PRIMARY
        clipboard through a keyboard shortcut.
        Check if the "url" is actually one, partial or otherwise;
        if it's not, construct a web search.

        """

        #self.search_frame.setVisible(False)
        #self.address_bar.completer().popup().close()

        if isinstance(request, QUrl):
            qurl = request

            if 'play' in self.attributes:
                print("PLAYING")

                Thread(target=partial(play_mpv, qurl)).start()

                self.attributes.discard('play')

                return

            if 'save' in self.attributes:
                clipboard(qurl)
                self.attributes.discard('save')
                return

        elif callable(request):
            url = request()
            qurl = fix_url(url)
        else:
            raise RuntimeError("Navigating to non-navigable")

        if self.prefix is None:
            options = extract_options(qurl.toString())
            self.prefix = options['prefix']
            self.prefix_set.emit(self.prefix)
            print("SET PREFIX: ", self.prefix)
            # this is the first navigation on this tab/webkit; replace
            # the Network Access Manager
            if self.prefix is None:
                raise RuntimeError(
                    "prefix failed to be set... 'options' is broken")

            if not has_manager(self.prefix):
                register_manager(self.prefix, InterceptNAM(options, None))

        if self.prefix is None:
            raise RuntimeError(
                "prefix failed to be set... 'options' is broken")
        if not has_manager(self.prefix):
            raise RuntimeError("prefix manager not registered...")

        self.page().setNetworkAccessManager(get_manager(self.prefix))

        ### LOG NAVIGATION
        host = sub("^www.", "", qurl.host())
        path = qurl.path().rstrip("/ ")

        do_not_store = [
            "duckduckgo.com", "t.co", "i.imgur.com", "imgur.com"
        ]

        if (
                (host not in do_not_store) and
                (not qurl.hasQuery()) and
                len(path.split('/')) < 4):
            database().store_navigation(host, path, self.prefix)

        print("%s>>>\t\t%s\n>>> NAVIGATE %s%s" % (
            Fore.CYAN,
            datetime.datetime.now().isoformat(),
            qurl.toString(),
            Fore.RESET))

        self.navlist = []

        self.setFocus()
        self.load(qurl)

    def __unembed_frames(self):
        """ Replaces the content of iframes with a link to their source

        """

        frame = self.page().mainFrame()
        nodes = [node for node in frame.findAllElements("iframe[src]")]
        for node in nodes:
            url = node.attribute('src')
            node.setOuterXml("""<a href="%s">%s</a>""" % (url, url))

        # We've added a[href] nodes to the page... rebuild the navigation list
        self.navlist = []

    def __delete_fixed(self, delete=True):
        """ Removes all '??? {position: fixed}' nodes """

        frame = self.page().mainFrame()
        fixables = "div, header, header > a, footer, nav, section, ul"
        nodes = [node for node in frame.findAllElements(fixables)
                 if node.styleProperty("position",
                                       QWebElement.ComputedStyle) == 'fixed']

        for node in nodes:
            if delete:
                node.removeFromDocument()
            else:
                node.setStyleProperty('position', 'absolute')

    def __populate_navlist(self):
        """ Fill the spatial navigation list with the current mainFrame
        anchor links

        If it already exists and has content, do nothing; the list has to
        be cleared when navigating or reloading a page

        Ideally it could be populated once per page load. It is not, partially
        because javascript creating/deleting anchors would require a refresh.

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

    def __find_visible_navigables(self):
        """ Find the elements on the navigation list that are visible right now

        """

        # updating every time; not needed unless scroll or resize
        # but maybe tracking scroll/resize is more expensive...
        view_geom = self.page().mainFrame().geometry()
        view_geom.translate(self.page().mainFrame().scrollPosition())

        # pending: do it only if needed
        self.__populate_navlist()

        # just for this time; which nodes from the entire page are, in
        # any way, visible right now?
        return [node for node in self.navlist
                if view_geom.intersects(node.geometry())]

    def clear_labels(self):
        """ clear the access-key navigation labels """

        print("hiding labels...")
        for label in self.labels:
            label.hide()
            label.deleteLater()

        self.labels = []
        self.map_tags = {}
        self.setFocus()

    def make_labels(self, source=None):
        """ Create labels for the web nodes in 'source'; if not defined,
        find all visible anchor nodes first

        """

        if source is None:
            source = self.__find_visible_navigables()

        self.map_tags = dict(zip(ALL_TAGS, source))

        for tag, node in self.map_tags.items():
            label = QLabel(tag, parent=self)
            self.labels.append(label)

            palette = QToolTip.palette()
            color = QColor(Qt.yellow)
            color = color.lighter(150)
            color.setAlpha(112)
            palette.setColor(QPalette.Window, color)

            label.setPalette(palette)
            label.setAutoFillBackground(True)
            label.setFrameStyle(QFrame.Box | QFrame.Plain)

            point = QPoint(node.geometry().left(), node.geometry().center().y())
            point -= self.page().mainFrame().scrollPosition()
            label.move(point)
            label.show()
            label.move(label.x(), label.y() + label.height() // 4)

    def akeynav(self, candidate):
        """ find and set focus on the node with the given label (if any) """

        candidate = candidate.upper()
        if candidate in self.map_tags.keys():
            found = self.map_tags[candidate]
            found.setFocus()
            self.page().linkHovered.emit(found.attribute("href"),
                                         None, None)
            self.setFocus()
            print("FOUND")
        else:
            print("not found yet...")

    def __spatialnav(self, direction):
        """ find web link nodes, move through them;
        initial testing to replace webkit's spatial navigation

        """

        localnav = self.__find_visible_navigables()

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
            self.__next_node(localnav, mininav, direction)
        else:
            if direction == UP or direction == LEFT:
                self.in_focus = max(localnav, key=lambda node:
                                    node.geometry().bottom())
            else:
                self.in_focus = min(localnav, key=lambda node:
                                    node.geometry().top())

        # We're done, we have a node to focus; focus it,
        # send a signal that will be bound to the status bar
        self.page().linkHovered.emit(self.in_focus.attribute("href"),
                                     None, None)

        self.in_focus.setFocus()

    def __next_node(self, localnav, mininav, direction):
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
                    min(region, key=partial(self.__node_manhattan,
                                            xfactor=manhattan_x,
                                            yfactor=manhattan_y)))

        elif direction == LEFT:
            if mininav:
                self.in_focus = min(
                    mininav, key=lambda node: node.geometry().right())
            else:
                region = [node for node in localnav
                          if node.geometry().right() < geom.left()]

                self.in_focus = self.in_focus if not region else (
                    min(region, key=partial(self.__node_manhattan,
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
                region.sort(key=partial(self.__node_manhattan,
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
                region.sort(key=partial(self.__node_manhattan,
                                        xfactor=manhattan_x,
                                        yfactor=manhattan_y))
                self.in_focus = self.in_focus if not region else region[0]

    def __node_manhattan(self, node, xfactor=1, yfactor=1):
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

    def __mouse_press_event(self, event):
        """ Reimplementation from base class. Detects middle clicks
        and sets self.paste

        """
        if event.buttons() & Qt.MiddleButton:
            self.attributes.add('paste')
        else:
            self.attributes.discard('paste')
        return QWebView.mousePressEvent(self, event)

    # Clean reimplement for Qt
    # pylint: disable=C0103
    mousePressEvent = __mouse_press_event
    # pylint: enable=C0103
