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
    version='1.5.2',
    description='QTWebkit based web browser',
    long_description="""


                TODO: write long description (¿importar DESCRIPTION.rst?)


    """,
    url='http://github.com/jsoffer/eilat',
    author='Jaime Soffer',
    author_email='Jaime.Soffer@gmail.com',
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Browsers'
    ],
    keywords='TODO keywords',
    packages=['eilat'],
    scripts=['bin/eilat'],
    #install_requires=['PyQt4', 'tldextract', 'colorama'],
    install_requires=['tldextract', 'colorama', 'PyYAML'],
    include_package_data=True
)
