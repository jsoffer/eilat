from setuptools import setup

from sys import version_info
if version_info < (3, 0):
    raise RuntimeError("""
        Using python 2.x? 3.x required (modify setup.py to disable the
        exception if the code has been ported)

        """)

try:
    import PyQt4
except ImportError:
    print("""

    PyQt4 is not available and setuptools is unable to install it from Pypi.
    Please install PyQt4 from distribution package or from source and try again.

    """)
    raise

setup(
    name='eilat-web-browser',
    version='1.5.5',
    platforms='Qt', # Pure python? Portability issues: path, clipboard
    description='QTWebkit based web browser',
    long_description="""

    Keyboard driven, security and privacy focused web browser build in PyQt4's
    webkit engine.

    Features:

    * simple source code, focused on promoting auditing
    * Isolation of instances for facebook, google, twitter; configurable
      for more sites
    * Console logging of resources actually retrieved and cookies set or
      attempted
    * hjkl, ^j, ^h, etc. keyboard navigation

    New in 1.5.5:

    * hooks for playing videos on 'mpv'
    * redone the log system for message clarity
    * access-key navigation ('ñ' or ';', then one or two-letters link tag)

    Install:

    First install PyQt4 for Python 3 by whatever means result more appropiate;
    using a pyvenv is recommended. Then do `pip install eilat-web-browser`. Pip
    will not install PyQt, but will install all the other dependences.

    Quick usage notes:

    * facebook, twitter, google will be blacklisted unless they are the first
      URL visited on a tab (and then the tab will hold to that site only)
    * `^t` creates a new tab
    * `Ctrl+Space` toggles the status bar
    * `g` starts an in-page search; `escape` in the search frame closes it
    * javascript is off by default; to enable one-tab-only, press `q` and reload
      with F5 or `r`

    Read `README.md` and the wiki (https://github.com/jsoffer/eilat/wiki) for
    lots of details - there's a lot of non obvious functionality that requires
    a bit of reading, e.g. modal keys or navigating through isolated tabs

    """,
    url='http://github.com/jsoffer/eilat',
    download_url='https://github.com/jsoffer/eilat/releases/',
    author='Jaime Soffer',
    author_email='Jaime.Soffer@gmail.com',
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Browsers'
    ],
    keywords='web browser qt webkit qtwebkit',
    packages=['eilat'],
    scripts=['bin/eilat'],
    install_requires=['tldextract', 'colorama', 'PyYAML']
)
