Eilat
=====

Homebrew, Qt-Webkit based web browser

Features
--------

* Small and rather readable layer over WebKit
* Keyboard navigation, minimal UI widgets
* "Smartly" (queries DNS) chooses between "navigate URL" and "search for term"
* Reports every network request

Non-features
------------

* Has no cache. Will not have. Depends on a proxy.
* Does not have bookmarks management. May have as web service.
* Has downloads disabled. Options are being assessed.
* Does not report error when not able to do something. Check the console (to be fixed)

Requirements
------------

* Python (tested on 2.7)
* PyQt4, including Qt, QtGui, QtCore, QtWebKit, QtNetwork, as Python bindings
* node.js (tested on v0.10.21) for the search server

Usage
-----

Set up a proxy, such as squid, polipo, etc. This is required. It can be ignored
if the lines under **# Proxy** are commented, and then there won't be any kind of
content caching.

Chmod **eilat.py** as executable and run it. This starts an empty browser. On the
bottom is an address bar. Write a partial URL, as, for example, **xkcd.com**. Press
**Ctrl+j** (**Enter** also works). The domain will be identified, the address completed,
and the browser will navigate to **http://xkcd.com**.

Press **Ctrl+Space**. This enables the status bar. Hover the comic. The alt text
will appear on the status bar. Hovering over a link makes the href appear too.
Press Ctrl+Space to disable the status bar again.

Press **Ctrl+t**. A new tab will appear. Select this: http://sidigital.co/
from wherever you're reading. Go back to the browser, click inside the tab (to
ensure it's active - I have to improve that) and press **y**. This will navigate
to the address stored on the primary clipboard. The animation will not run yet:
javascript is disabled. Press **j** to scroll the page down, **k** to scroll up.

Press **q**. The address bar should have turned blue: javascript is enabled now,
for this tab only. Press **F5** to reload. It works now. You can even keep pressing
**q** to pause and resume the animation.

Press **Ctrl-t** to create another new tab. Press **m**, **n** (if the web view is 
active, instead of the address bar), **Ctrl+PgUp** or **Ctrl+PgDn** to navigate 
between the tabs. All the other tabs should have white background on the address bar,
meaning that javascript should be disabled there.

Go back to xkcd. Press **g**. A text entry should appear just over the address bar.
Write **p**, **e**, **r** letter by letter to find the string "Permanent".

Search Server
=============

Since Eilat by default sends web searches to localhost:8000 a server on this
port is required. searchserver.js is a node.js application that catches the ?q=
parameter, queries Google, and builds a minimal page based on the results. Any
similar web app on this port would work just as well.

Usage
-----

If entering something that's not a web address causes the progress bar to hang,
as if waiting for something, that "something" may be the search server (it's
either that, the proxy, or net access is down). Run **node searchserver.js**
on a command line on a directory containing the subdirectory **templates/**
and try again. An ugly page will appear containing the search results for
that non-url entry.
