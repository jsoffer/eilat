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

from PyQt5.QtWebKitWidgets import QWebPage, QWebView
from PyQt5.QtWebKit import QWebSettings, QWebElement

from PyQt5.Qt import QApplication, QLabel, QToolTip, QFrame, QLineEdit
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QPoint, QObject, QEvent, QThread

from PyQt5.QtGui import QColor, QPalette, QKeyEvent

from functools import partial

from eilat.InterceptNAM import InterceptNAM
from eilat.libeilat import (fix_url, set_shortcuts,
                            real_host,
                            fake_click,
                            notify, do_redirect)

from eilat.global_store import (mainwin, clipboard,
                                has_manager, register_manager, get_manager,
                                get_options, get_css)
from eilat.options import extract_instance

from os.path import expanduser
import datetime
from time import time

from colorama import Fore

import string
import itertools

from subprocess import call

# Poor man's symbols (enum would be better - Python 3.4 and up only)
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3


class VidThread(QThread):
    """ A thread that runs the 'mpv' player and emits its output as
    text message
    """

    mpv_output = pyqtSignal(str)

    def __init__(self, parent, qurl):
        super(VidThread, self).__init__(parent)
        self.target_url = qurl

    def run(self):
        """ Will be automatically run by thread_instance.start() """

        try:
            process_returncode = call(['mpv', self.target_url.toString()])
            if process_returncode != 0:
                self.mpv_output.emit("mpv can't play: status {}".format(
                    process_returncode))
        except FileNotFoundError:
            self.mpv_output.emit("'mpv' video player not available")


class VidPlay(QObject):
    """ An object that has as single purpose to run VidThreads; that
    can't be done directly on the WebViews because closing a tab while
    a player is running causes the thread to have nowhere to come back
    to, crashing the browser
    """

    def __init__(self, parent=None):
        super(VidPlay, self).__init__(parent)
        self.vid_thread = None

    def play(self, url):
        """ Creates and uses a thread. The thread will be safe even if
        the tab closes as long as this method is not garbage collected
        """

        self.vid_thread = VidThread(self, url)
        self.vid_thread.mpv_output.connect(notify)
        self.vid_thread.start()

GLOBAL_VID_PLAY = VidPlay()


def fake_key(web_view, key):
    """ Generate a fake key click in the widget """
    current_javascript = web_view.javascript()
    web_view.javascript(False)
    enter_event = QKeyEvent(
        QEvent.KeyPress, key,
        Qt.KeyboardModifiers())
    QApplication.sendEvent(web_view, enter_event)
    web_view.javascript(current_javascript)


def toggle_show_logs(prefix):
    """ Inverts a value, toggling between printing or not responses that were
    accepted by the webkit or (some of) those that were filtered at some point.

    TOG02

    """

    netmanager = get_manager(prefix)
    netmanager.show_detail ^= True
    if netmanager.show_detail:
        print("---- SHOWING DETAILS ----")
    else:
        print("---- HIDING DETAILS ----")


def toggle_load_fonts(prefix):
    """ Inverts a value, toggling between filtering or not the requests for
    web fonts on the net manager level

    TOG03

    """

    netmanager = get_manager(prefix)
    netmanager.load_webfonts ^= True
    if netmanager.load_webfonts:
        print("---- LOADING WEB FONTS NOW ----")
    else:
        print("---- DISABLING WEB FONTS ----")


class Attributes(QObject):
    """ Stores state for the webkit """

    webkit_info = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Attributes, self).__init__(parent)
        self.prefix = None
        self.css_path = None
        self.__attributes = {}

    def insert(self, key, value=None):
        """ add a key-value to the local set """

        self.__attributes[key] = value
        self.__label()

    def clear(self, key):
        """ remove a key-value from the local set """

        if key in self.__attributes:
            del self.__attributes[key]
        self.__label()

    def toggle(self, key, value):
        """ insert a key-value to the set unless the key already exists,
        clear in that case

        """

        if key in self.__attributes:
            self.clear(key)
        else:
            self.insert(key, value)

    # allows "'attrib' in attributes" syntax
    def __contains__(self, key):
        """ is an attribute active? """
        return key in self.__attributes

    def __label(self):
        """ generate an info label and send it to the web tab """
        info = "".join([self.__attributes[k]
                        for k in
                        self.__attributes
                        if self.__attributes[k]])
        if info:
            self.webkit_info.emit(self.prefix + " [" + info + "]")
        else:
            self.webkit_info.emit(self.prefix)

    def set_prefix(self, pfx):
        """ encapsulate the prefix storage (incomplete) """
        self.prefix = pfx


def node_neighborhood(rect, direction):
    """ Finds a rectangle next to the node, where close by
    nodes could be

    NAV12

    """

    if direction == UP:
        rect.moveTop(rect.top() - rect.height())
        rect.setTop(rect.top() - 100)
    elif direction == DOWN:
        rect.moveBottom(rect.bottom() + rect.height())
        rect.setBottom(rect.bottom() + 100)
    elif direction == LEFT:
        rect.moveLeft(rect.left() - rect.width())
        rect.setLeft(rect.left() - 100)
    elif direction == RIGHT:
        rect.moveRight(rect.right() + rect.width())
        rect.setRight(rect.right() + 100)

    return rect


def next_node(candidates, direction, boundary):
    """ Given the direction that was travelled to create the
    candidates, find the best close node

    NAV12

    """

    target = None

    if direction == UP:
        target = max(candidates, key=lambda node:
                     node.geometry().bottom())
    elif direction == LEFT:
        candidates = [node for node in candidates if
                      node.geometry().right() <= boundary.right()]
        if candidates:
            target = max(candidates, key=lambda node:
                         node.geometry().right())
    elif direction == DOWN:
        def surface(node):
            """ Give the node that has the largest surface inside the
            boundary. Negative to allow to use 'min' in tuple comparison.
            Kind of flaky (find better ways; workaround for hackernews
            title-to-comments instead of to username)

            """
            intersect = boundary & node.geometry()
            return -(intersect.height() * intersect.width())
        target = min(candidates, key=lambda node:
                     (node.geometry().top(), surface(node)))
    elif direction == RIGHT:
        candidates = [node for node in candidates if
                      node.geometry().left() >= boundary.left()]
        if candidates:
            target = min(candidates, key=lambda node:
                         node.geometry().left())

    return target

ALL_TAGS = [p + q for (p, q) in
            itertools.product(['', 'J', 'F', 'H'],
                              string.ascii_uppercase + string.digits)]

# make the prefix keys special, so it's possible to one-key most links
# on a low-population page; can be improved (as can the distribution too) by
# making ALL_TAGS a function depending on the number of links in the page

ALL_TAGS.remove('J')
ALL_TAGS.remove('F')
ALL_TAGS.remove('H')


class WebView(QWebView):
    """ Una página web con contenedor, para poner en una tab

    """

    # sent only once, to define the model to use for completion
    set_prefix = pyqtSignal(str)

    # a page load with destination 'str' started, but the url
    # has not changed yet
    load_requested = pyqtSignal(str)

    # sends a string to the yellow corner message area
    show_message = pyqtSignal(str)

    # emits in akey_nav to tell the akey input area to reset itself
    nonvalid_tag = pyqtSignal()

    # hides the message_label
    hide_overlay = pyqtSignal()

    # sent when the webkit acquires focus
    focus_webkit = pyqtSignal()

    javascript_state = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(WebView, self).__init__(parent)

        # hide the tooltips (they're still there, just with a height of zero)
        # see http://qt-project.org/doc/qt-4.8/stylesheet-reference.html
        self.setStyleSheet("QToolTip {max-height: 0px}")  # CFG11

        self.attr = Attributes(parent=self)
        self.attr.css_path = expanduser("~/.eilat/css/")  # CFG01

        self.started_at = None

        # a web element node
        self.__in_focus = None  # NAV11, NAV12

        # make_labels, clear_labels
        self.__labels = []

        # make_labels, clear_labels, akeynav
        self.map_tags = {}

        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)  # CB04

        # self.settings().setFontFamily(
        #     QWebSettings.StandardFont, "Georgia")

        self.settings().setAttribute(
            QWebSettings.PluginsEnabled, False)

        # take care; if set to True, the address bar, that is not yet
        # connected, will not be able to set its color to "javascript on"
        self.javascript(False)

        self.settings().setAttribute(
            QWebSettings.FrameFlatteningEnabled, True)

        self.settings().setAttribute(
            QWebSettings.DeveloperExtrasEnabled, True)

        self.page().setForwardUnsupportedContent(True)  # CB04

        # connect (en constructor)
        def on_link_click(qurl):
            """ Callback for connection. Reads the 'paste' attribute
            to know if a middle click requested to open on a new tab.

            BRW01 BRW12 VID01 CB03

            """

            # required for 'open in new tab if not in this instance'
            qurl = do_redirect(qurl)  # BRW12

            # 'play' and 'save' should only happen from inside the webkit and
            # if the user started the action; handle here, not in 'navigate'

            if 'play' in self.attr:
                print("PLAYING")

                GLOBAL_VID_PLAY.play(qurl)  # VID01

                self.attr.clear('play')

                return

            if 'save' in self.attr:
                clipboard(qurl)  # CB02
                self.attr.clear('save')
                return

            instance = extract_instance(qurl.toString())

            target_prefix = get_options()['sites'][instance]['prefix']

            # if the prefixes don't match, we're requesting a new instance
            # TAB04 TAB05
            if 'paste' in self.attr or self.attr.prefix != target_prefix:
                mainwin().add_tab(qurl,
                                  scripting=('open_scripted' in self.attr))
                self.attr.clear('paste')
            else:
                self.navigate(qurl)  # BRW01

            if 'open_scripted' in self.attr:
                self.attr.clear('open_scripted')

        # linkClicked carries QUrl
        self.linkClicked.connect(on_link_click)

        def url_changed(qurl):
            """ One time callback for 'connect'
            Sets the user style sheet

            CFG01

            """

            print("CHGD ({}s)".format(time() - self.started_at))
            self.started_at = time()

            host_id = real_host(qurl.host())

            css_map = get_css()

            css_pseudo_file = css_map[host_id]
            self.settings().setUserStyleSheetUrl(QUrl(css_pseudo_file))

        # urlChanged carries QUrl
        self.urlChanged.connect(url_changed)

        # statusBarMessage carries str
        self.statusBarMessage.connect(notify)

        # downloadRequested carries QNetworkRequest
        self.page().downloadRequested.connect(clipboard)  # CB04
        # unsupportedContent carries QNetworkReply
        self.page().unsupportedContent.connect(clipboard)  # CB04

        # loadStarted carries nothing
        self.page().loadStarted.connect(partial(self.attr.insert,
                                                'in_page_load'))

        self.profiler = None

        def load_started():
            """ Clear __in_focus; we don't even know if the focused
            node still exists.

            Set the "we're starting to load" attribute.

            """

            self.attr.insert('in_page_load')
            self.__in_focus = None

            self.started_at = time()

            # profiling()

        self.page().loadStarted.connect(load_started)

        # the star swallows all arguments
        def load_finished(*_):
            """ if we kept javascript on to allow the load of the page, we
            may want to turn it off when it has finished.

            Remove the "we're starting to load" attribute.

            """

            print("DONE ({}s)".format(time() - self.started_at))

            if (not self.hasFocus() and
                    'in_page_load' not in self.attr and
                    self.javascript()):
                self.attr.insert('stored_scripting_on')
                self.javascript(False)  # JS01
                print("EXITING LOAD WITH JS WITHOUT FOCUS")

            self.attr.clear('in_page_load')

            # profiling(begin=False)

        # loadFinished carries bool (ignored)
        self.page().loadFinished.connect(load_finished)

        def dump_dom():
            """ saves the content of the current web page

            DOM04

            """
            data = self.page().currentFrame().documentElement().toInnerXml()
            print("SAVING...")
            with open('test.html', 'w') as file_handle:
                file_handle.write(data)

        def scroll(delta_x=0, delta_y=0):
            """ One-time callback for QShortcut

            NAV01

            """
            self.page().mainFrame().scroll(delta_x, delta_y)

        def zoom(lvl):
            """ One-time callback for QShortcut

            NAV02

            """
            factor = self.zoomFactor() + (lvl * 0.25)
            self.setZoomFactor(factor)

        def emit_message_info(title=False):
            """
            If requesting for the document's title, emit it. Otherwise,
            if a link is focused, emit its target to the message label

            """

            if title:
                self.show_message.emit(self.title())
            elif self.__in_focus is not None:
                qurl = QUrl(self.__in_focus.attribute('href'))
                qurl = do_redirect(qurl)
                self.show_message.emit(qurl.toString())

        set_shortcuts([
            # notifications
            ("Shift+D", self, partial(emit_message_info, title=True)),
            ("D", self, emit_message_info),
            # DOM actions DOM04 DOM03 DOM02
            ("Ctrl+M", self, dump_dom),
            ("F", self, self.__unembed_frames),
            ("F2", self, self.__delete_fixed),
            ("Shift+F2", self, partial(self.__delete_fixed, delete=False)),
            ("Ctrl+F2", self, partial(self.__delete_fixed, force=True)),
            # webkit interaction
            ("Alt+Left", self, self.back),
            ("Alt+Right", self, self.forward),
            ("F5", self, self.reload),
            ("R", self, self.reload),
            # view interaction NAV01 NAV02
            ("J", self, partial(scroll, delta_y=40)),
            #("Z", self, partial(scroll, delta_y=40)),
            ("K", self, partial(scroll, delta_y=-40)),
            #("X", self, partial(scroll, delta_y=-40)),
            ("H", self, partial(scroll, delta_x=-40)),
            ("L", self, partial(scroll, delta_x=40)),
            ("Ctrl+Up", self, partial(zoom, 1)),
            ("Ctrl+Down", self, partial(zoom, -1)),
            ("Ctrl+J", self, partial(fake_key, self, Qt.Key_Enter)),
            ("Ctrl+H", self, partial(fake_key, self, Qt.Key_Backspace)),
            ("Backspace", self, self.back),
            #("C", self, partial(fake_click, self)),
            (",", self, partial(fake_click, self)),
            # spatial navigation NAV12
            ("Shift+H", self, partial(self.__spatialnav, LEFT)),
            ("Shift+J", self, partial(self.__spatialnav, DOWN)),
            ("Shift+K", self, partial(self.__spatialnav, UP)),
            ("Shift+L", self, partial(self.__spatialnav, RIGHT)),
            # toggles TOG02 TOG03
            # lambda required because self.attr.prefix is updated
            # when the web view navigates the first time
            ("F11", self, lambda: toggle_show_logs(self.attr.prefix)),
            ("Shift+F11", self, lambda: toggle_load_fonts(self.attr.prefix)),
            ("Escape", self, self.focus_webkit.emit),  # FIXME ???
            # clipboard related behavior
            ("I", self, partial(self.attr.toggle, 'paste', 'I')),  # TAB04
            ("O", self, partial(self.attr.toggle, 'open_scripted', 'O')),
            ("S", self, partial(self.attr.toggle, 'save', 'S')),  # CB03
            ("V", self, partial(self.attr.toggle, 'play', 'V')),  # VID01
            # profiler
            # ("9", self, profiling),  # DEB02
            # ("0", self, partial(profiling, begin=False))  # DEB02
            ])


    # action (en register_actions)
    def navigate(self, request=None):
        """ Open the url on this tab. If 'url' is already a QUrl
        (if it comes from a href click), just send it. Otherwise,
        it comes either from the address bar or the PRIMARY
        clipboard through a keyboard shortcut.
        Check if the "url" is actually one, partial or otherwise;
        if it's not, construct a web search.

        BRW01

        """

        if isinstance(request, QUrl):
            qurl = request

        # 'navigate' was connected to a QLineEdit to extract its text
        elif isinstance(request, QLineEdit):
            url = request.text()
            qurl = fix_url(url)  # BRW11
        else:
            raise RuntimeError("Navigating to non-navigable")

        # if the qurl does not trigger an URL in SHORTENERS or REDIRECTORS,
        # this will be a no-op
        qurl = do_redirect(qurl)  # BRW12

        if self.attr.prefix is None:
            # this is the first navigation on this tab/webkit; replace
            # the Network Access Manager CFG02

            instance = extract_instance(qurl.toString())
            self.attr.set_prefix(get_options()['sites'][instance]['prefix'])

            if self.attr.prefix is None:
                raise RuntimeError(
                    "prefix failed to be set... 'options' is broken")

            # strictly speaking, this should emit from Attributes.set_prefix
            self.set_prefix.emit(self.attr.prefix)
            if self.attr.prefix == "":
                print("GENERAL")
            else:
                print("INSTANCE: {}".format(self.attr.prefix))

            if not has_manager(self.attr.prefix):
                register_manager(self.attr.prefix,
                                 InterceptNAM(instance,
                                              parent=None))

            if not has_manager(self.attr.prefix):
                raise RuntimeError("prefix manager not registered...")

            self.page().setNetworkAccessManager(get_manager(self.attr.prefix))

        print("{}>>>\t\t{}\n>>> NAVIGATE {}{}".format(
            Fore.CYAN,
            datetime.datetime.now().isoformat(),
            qurl.toString(),
            Fore.RESET))

        self.setFocus()
        self.load_requested.emit(qurl.toString())
        self.load(qurl)

    def __unembed_frames(self):
        """ Replaces the content of iframes with a link to their source

        DOM03

        """

        frame = self.page().mainFrame()
        nodes = [node for node in frame.findAllElements("iframe[src]")]
        for node in nodes:
            url = node.attribute('src')
            node.setOuterXml("""<a href="{}">{}</a>""".format(url, url))

    def __delete_fixed(self, delete=True, force=False):
        """ Removes all '??? {position: fixed}' nodes

        DOM02

        """

        frame = self.page().mainFrame()
        fixables = "div, header, header > a, footer, nav, section, ul"

        if force:
            nodes = frame.findAllElements("*")
        else:
            nodes = frame.findAllElements(fixables)

        nodes = [node for node in nodes
                 if node.styleProperty("position",
                                       QWebElement.ComputedStyle) == 'fixed']

        for node in nodes:
            if delete:
                node.removeFromDocument()
            else:
                node.setStyleProperty('position', 'absolute')

    def __generate_navlist(self, elements="a[href], input"):
        """ find the current mainFrame's anchor links (or other elements)

        """

        frame = self.page().mainFrame()
        return [node for node
                in frame.findAllElements(elements).toList()
                if node.geometry() and
                node.styleProperty(
                    "visibility",
                    QWebElement.ComputedStyle) == 'visible']

    def __find_visible(self, navigables=True):
        """ Find the elements on the navigation list that are visible right now

        Can search either navigables (a href, input) or elements with a title


        NAV12 NAV11 DOM01

        """

        # TODO reduce code duplication; argument 'navigables' may be unclear

        # updating every time; not needed unless scroll or resize
        # but maybe tracking scroll/resize is more expensive...
        view_geom = self.page().mainFrame().geometry()
        view_geom.translate(self.page().mainFrame().scrollPosition())

        # which nodes from the entire page are, in any way, visible right now?
        if navigables:
            navlist = self.__generate_navlist()
            return [node for node in navlist
                    if view_geom.intersects(node.geometry())]

        else:
            navlist = self.__generate_navlist("*[title]")
            return [node for node in navlist
                    if view_geom.intersects(node.geometry())
                    and node.attribute("title")]

    def clear_labels(self):
        """ clear the access-key navigation labels

        Called externally from WebTab when nav_bar is hidden

        NAV11 DOM01

        """

        for label in self.__labels:
            label.hide()
            label.deleteLater()

        self.__labels = []
        self.map_tags = {}
        self.setFocus()

    def make_labels(self, target):
        """ Create labels for the web nodes in 'source'; if not defined,
        find all visible anchor nodes first

        TODO pass a color? for 'title' tags

        NAV11 DOM01

        """

        if target == "links":
            source = self.__find_visible(navigables=True)
            self.attr.clear('find_titles')
        elif target == "titles":
            source = self.__find_visible(navigables=False)
            self.attr.insert('find_titles')

        self.map_tags = dict(zip(ALL_TAGS, source))

        for tag, node in self.map_tags.items():
            label = QLabel(tag, parent=self)
            self.__labels.append(label)

            palette = QToolTip.palette()

            color = QColor(Qt.yellow)

            color = color.lighter(160)
            color.setAlpha(196)
            palette.setColor(QPalette.Window, color)

            label.setPalette(palette)
            label.setAutoFillBackground(True)
            label.setFrameStyle(QFrame.Box | QFrame.Plain)

            point = QPoint(
                node.geometry().left(),
                node.geometry().center().y())
            point -= self.page().mainFrame().scrollPosition()
            label.move(point)
            label.show()
            label.move(label.x(), label.y() + label.height() // 4)

    def akeynav(self, candidate):
        """ find and set focus on the node with the given label (if any)

        NAV11

        """

        candidate = candidate.upper()
        if candidate in self.map_tags:
            if 'find_titles' not in self.attr:
                found = self.map_tags[candidate]
                self.__in_focus = found
                found.setFocus()
            else:
                title = self.map_tags[candidate].attribute("title")
                self.show_message.emit(title)

            # this moves us back from the text entry to the webView
            self.setFocus()
        else:
            # deal with tags longer than a character
            # all the combinations are at most two letters
            if candidate not in [k[0] for k in self.map_tags]:
                # there's no possible tag for this entry
                # tell the webkit
                self.nonvalid_tag.emit()

    def __spatialnav(self, direction):
        """ find web link nodes, move through them;
        initial testing to replace webkit's spatial navigation

        NAV12

        """

        target = None

        localnav = self.__find_visible(navigables=True)  # generates a navlist

        if not localnav:
            print("No anchors in current view?")
            return

        if self.__in_focus not in localnav:
            if direction == UP or direction == LEFT:
                target = max(localnav, key=lambda node:
                             node.geometry().bottom())
            else:
                target = min(localnav, key=lambda node:
                             node.geometry().top())

        else:

            # if we're here, we have a visible, previously focused node;
            # search from it, in the required direction, within the width of
            # the node.

            target_rect = node_neighborhood(self.__in_focus.geometry(),
                                            direction)

            candidates = [node for node in localnav
                          if target_rect.intersects(node.geometry())]

            if candidates:
                target = next_node(candidates, direction, target_rect)

        if target is not None:
            self.__in_focus = target
            self.__in_focus.setFocus()

    def __mouse_press_event(self, event):
        """ Reimplementation from base class. Detects middle clicks
        and sets self.paste

        TAB03

        """
        if event.buttons() & Qt.MiddleButton:
            self.attr.toggle('paste', 'P')
        else:
            self.attr.clear('paste')
        return QWebView.mousePressEvent(self, event)

    def __focus_in_event(self, event):
        """ Turn on javascript when the WebView is focused if scripting
        was already turned on

        JS01

        """

        if 'stored_scripting_on' in self.attr:
            print("JS on")
            self.javascript(True)
            self.attr.clear('stored_scripting_on')

        self.focus_webkit.emit()

        return QWebView.focusInEvent(self, event)

    def __focus_out_event(self, event):
        """ Turn off javascript if the WebView is not focused

        JS01

        """

        if self.javascript() and 'in_page_load' not in self.attr:
            self.attr.insert('stored_scripting_on')
            self.javascript(False)
            print("JS off")

        return QWebView.focusOutEvent(self, event)

    def javascript(self, state=None):
        """ if called without parameters, return current state of javascript
        being enabled; otherwise, turn javascript on or off

        JS01 TOG01

        """
        if state is None:
            return self.settings().testAttribute(
                QWebSettings.JavascriptEnabled)
        else:
            self.settings().setAttribute(QWebSettings.JavascriptEnabled, state)
            self.javascript_state.emit(state)

    # Clean reimplement for Qt
    # pylint: disable=C0103
    mousePressEvent = __mouse_press_event
    focusInEvent = __focus_in_event
    focusOutEvent = __focus_out_event
    # pylint: enable=C0103
