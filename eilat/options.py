"""
Default values for NAM instances

"""

import tldextract

import yaml
from os.path import expanduser
from glob import glob

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


GLOBAL_CSS = b""" :focus > img, a:focus, input:focus {
outline-color: rgba(160, 160, 255, 0.6) ! important;
outline-width: 10px ! important;
/* outline-offset: 1px ! important; */
outline-style: ridge ! important;
}
* { box-shadow: none ! important; }
"""


def load_css():
    """ read and encode every stylesheet file on the CSS directory;
    store the encoding on a map, as a cache

    """

    css_dictionary = {}
    css_files = glob(expanduser("~/.eilat/css/")+"*.css")
    header = b"data:text/css;charset=utf-8;base64,"

    for css_file in css_files:
        with open(css_file) as file_handle:
            css_input = file_handle.read()

        encoded = encodestring(GLOBAL_CSS + css_input.encode())

        # filename without extension; also, host to apply css to
        key = css_file.split('/')[-1].split('.css')[0]
        css_dictionary[key] = (header + encoded).decode().strip()

    # default key; every host without .css file, load the global css only
    empty = (header + encodestring(GLOBAL_CSS)).decode().strip()
    css_dictionary[None] = empty

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
