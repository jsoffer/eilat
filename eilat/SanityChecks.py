""" Checks to be performed before the application starts """

from os.path import isdir, isfile, expanduser

# do not warn about unused variables (nothing is going to be used,
# just looked at

def check_python_3():
    """ Using Python 3? """
    from sys import version_info
    if version_info < (3, 0):
        raise RuntimeError("Using python 2.x? 3.x required")

# pylint: disable=W0612
def check_libraries():
    """ Are all required modules available? """

    try:
        import PyQt4
    except ImportError:
        print("""

        ----
        PyQt4 is not available ('import PyQt4' failed with ImportError)

        It's not automatically installed through pip because I (the packager)
        can't get beyond 'No distributions at all found for PyQt4' after 'pip
        install PyQt4'

        Please install either from your package manager or by following the
        instructions on the wiki, https://github.com/jsoffer/eilat/wiki/set-up
        ----


        """)

        raise

    try:
        import colorama
    except:
        print("""

        ----
        Did pip fail at installing 'colorama'? It's a bug
        ----

        """)

        raise

    try:
        import tldextract
    except:
        print("""

        ----
        Did pip fail at installing 'tldextract'? It's a bug
        ----

        """)

        raise

# pylint: enable=W0612

def check_dotfile():
    """ Is the dotfile structure usable enough?

    Is the .db structure the right one? That's verified directly on the
    constructor of DatabaseLog

    """

    path = expanduser("~/.eilat")
    return(isdir(path) and
           isdir(path + '/cookies') and
           isdir(path + '/css') and
           isfile(path + '/options.yaml'))

def check_proxy(host, port):
    """ Is there even an appearance of something resembling a proxy on the set
    up port?

    """

    if host is None or port is None:
        return False

    try:
        import socket
        proxy = socket.socket()
        proxy.connect((host, port))
        return True
    except ConnectionRefusedError:
        print("No proxy on %s:%s?" % (host, str(port)))
        return False
    finally:
        proxy.close()
