"""
Default values for NAM instances

"""

from PyQt5.QtNetwork import QSslConfiguration, QSslCertificate

import tldextract

import yaml
from os.path import expanduser
import re
from glob import glob
from collections import defaultdict

from eilat.global_store import set_options, get_options, set_css
from base64 import encodestring


def load_options():
    """ to be called at startup and maybe with a keybinding after
    modifying the options file

    """

    with open(expanduser("~/.eilat/options.yaml")) as yaml_file:
        options_yaml = yaml.safe_load(yaml_file)

    all_whitelists = [options_yaml['sites'][k]['host_whitelist']
                      for k in options_yaml['sites']]
    all_whitelists = [k for k in all_whitelists if k is not None]  # filter
    all_whitelists = [x for y in all_whitelists for x in y]  # flatten
    all_whitelists = [k.split('/')[0] for k in all_whitelists]  # no paths

    options_yaml['all_whitelists'] = set(all_whitelists)  # no repetitions
    set_options(options_yaml)

# note: modifying GLOBAL_CSS in disk doesn't make load_css update it,
# because it uses the in-memory stored at first file load

GLOBAL_CSS = b""" :focus > img, a:focus, input:focus {
outline-color: rgba(160, 160, 255, 0.6) ! important;
outline-width: 10px ! important;
/* outline-offset: 1px ! important; */
outline-style: ridge ! important;
}
* { box-shadow: none ! important; opacity: 1 ! important; }
* { -webkit-user-select: text ! important; } /* override 'forbid selection' */
::-webkit-scrollbar {width: 8px !important; height: 4px ! important; }
::-webkit-scrollbar-thumb{background-color: #999 !important;}
"""


def load_css():
    """ read and encode every stylesheet file on the CSS directory;
    store the encoding on a map, as a cache

    """

    header = b"data:text/css;charset=utf-8;base64,"
    empty = (header + encodestring(GLOBAL_CSS)).decode().strip()

    # the defaultdict will return the content of 'empty' for missing keys
    css_dictionary = defaultdict(lambda: empty)

    css_files = glob(expanduser("~/.eilat/css/")+"*.css")

    for css_file in css_files:
        with open(css_file) as file_handle:
            css_input = file_handle.read()

        encoded = encodestring(GLOBAL_CSS + css_input.encode())

        # filename without extension; also, host to apply css to
        key = css_file.split('/')[-1].split('.css')[0]
        css_dictionary[key] = (header + encoded).decode().strip()

    set_css(css_dictionary)


def proxy_options():
    """ Extracts the proxy information from YAML user settings. If any is
    empty, proxy will be disabled. If the fields do not exist (not checked)
    the app will fail hard.

    """

    options = get_options()['proxy']
    return (options['host'], options['port'])


def extract_instance(url):
    """ Given a site, give the key to a map that decides if cookies are
    allowed, if only some sites will not be blocked, etc.

    """

    host = None if url is None else tldextract.extract(url).domain

    options_sites = get_options()['sites']

    if host in options_sites.keys():
        return host
    else:
        return 'general'


def split_certificates(cert_file):
    """ input: a file containing X.509 PEM certificates; output: a list of
    strings, each containing a single certificate

    """

    try:
        with open(cert_file) as pem_file:
            certificates = pem_file.read()

        expression = re.compile("-----BEGIN CERTIFICATE-----"
                                ".*?"  # *? is non greedy
                                "-----END CERTIFICATE-----",
                                re.S)  # re.S matches newline with *
    except FileNotFoundError:
        return None

    return expression.findall(certificates)


def load_certificates():
    """ load (if existing and not empty) the local PEM file; split it into
    individual certificates, add each to the default configuration

    """

    local_cert_path = expanduser("~/.eilat/local.pem")
    local_certificates = split_certificates(local_cert_path)

    if local_certificates:
        print(r"""
        /----------------------------\
        SETTING LOCAL SSL CERTIFICATES
        \----------------------------/


        """)
        current_configuration = QSslConfiguration.defaultConfiguration()
        current_certs = current_configuration.caCertificates()
        for certificate in local_certificates:
            current_certs.append(QSslCertificate(certificate))

            current_configuration.setCaCertificates(current_certs)
            QSslConfiguration.setDefaultConfiguration(current_configuration)
