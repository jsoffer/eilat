Eilat
=====

Homebrew, Qt-Webkit based web browser

Part of the purpose of this project is to familiarize the user with the workings
of a web browser and of the Internet in general. Setting up and tuning is not
expected to be trivial, requiring (rather minor) knowledge of Python and system
administration, hopefully in exchange for a more finely grained set of features.

Requirements
------------

* Python (tested on 2.7 and 3.4)
* PyQt4, including Qt, QtGui, QtCore, QtWebKit, QtSql, QtNetwork as Python
bindings, as well as sqlite3 support on the native QtSql
* tldextract (https://github.com/john-kurkowski/tldextract); install the latest
version (with pip install -e git://github...), pip has (as of now) a very obsolete one
* a proxy cache (like squid or polipo)

Installation
------------

A proxy cache is required. If it does not run in port 3128, or if the user chooses
not to run a proxy, it can be tuned up on the file **eilat.py**, function **main**,
under 'if options['use_proxy']:'. Failing to do so would result on pages not loading.
It's recommended to read first the function **extract_options** to find out why e.g.
opening twitter.com from the command line will ignore the proxy settings.

Very quick install: uncompress **dot_eilat.tar.bz2**, move it to ~/.eilat; the empty
history database and the cookies directory will be filled in runtime, and styles
will be searched on the css directory. Run 'python eilat.py [optional url]'
inside the 'eilat/eilat' directory.

Better instructions to be written later.

Features
--------

* Small and rather readable layer over WebKit
* Keyboard navigation, minimal UI widgets
* Reports every network request

Non-features
------------

* Has no cache. Will not have. Depends on a proxy.
* Does not have a fully featured bookmarks management.
* Has no means to make downloads. Copies the download URL to clipboard and
leaves the actual download to external means.

Usage
-----

(Unless browsing google, facebook, etc); Set up a proxy, such as squid, polipo, etc.
This is required. It can be ignored if the lines under **# Proxy** are commented,
and then there will be only limited memory content caching.

Chmod **eilat.py** as executable and run it. This starts an empty browser. On the
bottom is an address bar. Write a partial URL, as, for example, **xkcd.com**. Press
**Ctrl+j** (**Enter** also works). The domain will be identified, the address completed,
and the browser will navigate to **http://xkcd.com**.

Press **Ctrl+Space**. This enables the status bar.
Hovering over a link makes the href appear in the bar.
Press Ctrl+Space to disable the status bar again.

Press **Ctrl+t**. A new tab will appear. Select this: http://sidigital.co/
from wherever you're reading. Go back to the browser, click inside the tab (to
ensure it's active - I have to improve that) and press **y**. This will navigate
to the address stored on the primary clipboard. The animation will not run yet:
javascript is disabled. Press **j** to scroll the page down, **k** to scroll up.

Press **q**. The address bar should have turned blue: javascript is enabled now,
for this tab only. Press **F5** to reload. It works in the bar. You can even keep pressing
**q** to pause and resume the animation.

Press **Ctrl-t** to create another new tab. Press **m**, **n** (if the web view is 
active, instead of the address bar), **Ctrl+PgUp** or **Ctrl+PgDn** to navigate 
between the tabs. All the other tabs should have white background on the address bar,
meaning that javascript should be disabled there.

Go back to xkcd. Press **g**. A text entry should appear just over the address bar.
Write **p**, **e**, **r** letter by letter to find the string "Permanent".

----

If using vim, edit with https://github.com/hynek/vim-python-pep8-indent/
