""" Checks to be performed before the application starts """


def check_libraries():
    """ Are all required modules available? """

    try:
        import PyQt4
    except ImportError:
        print("""

        ----
        PyQt4 is not available

        It's not automatically installed through pip because I (the packager)
        can't get beyond 'No distributions at all found for PyQt4' after 'pip
        install PyQt4'

        Please install either from your package manager or by following the
        instructions on the wiki, https://github.com/jsoffer/eilat/wiki/set-up
        ----


        """)

        raise
