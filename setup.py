from setuptools import setup, find_packages

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
    install_requires=['tldextract', 'colorama'],
    include_package_data=True
)