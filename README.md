Eilat
=====

Homebrew, Qt-Webkit based web browser, focused on keyboard navigation and privacy
and security while browsing.

Requirements
------------

* Python 3 (tested on 3.4)
* PyQt4, including Qt, QtGui, QtCore, QtWebKit, QtSql, QtNetwork as Python
bindings, as well as sqlite3 support on the native QtSql
* tldextract (https://pypi.python.org/pypi/tldextract)
* colorama (https://pypi.python.org/pypi/colorama)
* PyYAML (https://pypi.python.org/pypi/PyYAML)
* a proxy cache (like squid or polipo)

Installation
------------

`pip install eilat-web-browser` after installing PyQt4.

A proxy cache (e.g. squid) is strongly recommended. The default install creates
the file `options.yaml` inside the directory `~/.eilat` containing blank
entries for proxy's host and port after the first `eilat` startup; once a
proxy is ready and running, please set host and port to enable proxy,
then restart `eilat`.

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

## All Key Bindings

Anywhere except the address bar

The reason being, creating a new tab when a popup is active is a delicate
matter, and maybe a rare case, better to be avoided.

* `^t` add tab
    * `^T` with javascript on

### Anywhere

* `^q` close window

#### Tabs

* `^t` add tab
    * `^y` extracting the url from a redirector in the clipboard
    * `^T` with javascript on
* `^w` close current tab

#### Movement

* `^PgDown` move to next tab
    *  `^PgUp` move to previous tab

#### Input emulation

* `^j` sends Return
* `^h` sends Backspace

### On the web area

* `e` copy the contents of the address bar to clipboard
* `g` init a search in page text
* `^l` focus the address bar

#### Tabs

* `u` re-open last closed tab
* `y` add tab, navigating to an url in the clipboard

#### DOM manipulation
* `^m` dump DOM to file
* `f` unembed frames
* `F2` remove fixed elements
    * `Shift F2` un-fix fixed elements

#### Web actions

* `F5`, `r` reload page
* `Alt ←` go back in history (this tab only)
    * `Alt →` go forward in history

#### Movement

* `hjkl` move page
* `Shift hjkl`move between links
* `Shift i` forget currently focused link;et spatial navigation
* `Ctrl ↑` zoom in
    * `Ctrl ↓` zoom out
* `m` move to next tab
    * `n` move to previous tab

#### Input emulation

* `c` sends left mouse click

#### Modal state manipulation

* `i` next navigation will be on new tab
    * `io` on new tab, with javascript on
* `s` next navigation request will be saved to clipboard; no actual navigation will occur

#### Toggling

* `^<space>` toggle show/hide status bar
* `q` toggle enable/disable javascript
* `Z` toggle display of traffic
    * `z` toggle display of debug information

### On the address bar

* `^i` next completion
    * `^p` previous completion
* `<escape>` focus the webkit

### On the search frame

* `<escape>` hide the search frame

Usage
-----

Run `eilat`, that will be installed as a script and is probably on the path by
now.  This starts an empty browser. On the bottom is an address bar. Write a
partial URL, as, for example, `xkcd.com`. Press `Ctrl+j` (`Enter` also works).
The domain will be identified, the address completed, and the browser will
navigate to `http://xkcd.com`.

Press `Ctrl+Space`. This enables the status bar.
Hovering over a link makes the href appear in the bar.
Press `Ctrl+Space` to disable the status bar again.

Press `Ctrl+t`. A new tab will appear. Select this: http://sidigital.co/
from wherever you're reading. Go back to the browser, press `Escape` (to
ensure the web area is active) and press `y`. This will navigate
to the address stored on the primary clipboard. The animation will not run yet:
javascript is disabled. Press `j` to scroll the page down, `k` to scroll up.

Press `q`. The address bar should have turned blue: javascript is enabled now,
for this tab only. Press `r` or `F5` to reload. The animation starts since 
scripting is active. You can even keep pressing `q` to pause and resume
the animation.

Press `Ctrl+t` to create another new tab. Press `m`, `n` (with the web view
active, instead of the address bar or search frame - press `Escape` first otherwise),
or `Ctrl+PgUp`,  `Ctrl+PgDn` to navigate between the tabs. All newly created
tabs should have white background on the address bar, meaning that scripting is
disabled there.

Go back to xkcd. Press `g`. A text entry should appear just over the address bar.
Write `p`, `e`, `r` letter by letter to find the string "Permanent".

----

If using vim, edit source code with https://github.com/hynek/vim-python-pep8-indent/
Use pylint on all source `.py` files aiming for 100%; a reference `pylintrc` is provided.
