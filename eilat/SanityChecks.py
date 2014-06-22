""" Checks to be performed before the application starts """

# do not warn about unused variables (nothing is going to be used,
# just looked at
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

def check_dotfile():
    """ Is the dotfile structure usable enough? """
    pass

def check_proxy():
    """ Is there even an appearance of something resembling a proxy on the set
    up port?

    """
    pass

# pylint: enable=W0612
