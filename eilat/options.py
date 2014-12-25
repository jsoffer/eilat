"""
Default values for NAM instances

"""

import tldextract

import yaml
from os.path import expanduser

from eilat.global_store import set_options, get_options


def load_options():
    """ to be called at startup and maybe with a keybinding after
    modifying the options file

    """

    with open(expanduser("~/.eilat/options.yaml")) as yaml_file:
        options_yaml = yaml.safe_load(yaml_file)
        set_options(options_yaml)


def proxy_options():
    """ Extracts the proxy information from YAML user settings. If any is
    empty, proxy will be disabled. If the fields do not exist (not checked)
    the app will fail hard.

    """

    options = get_options()['proxy']
    return (options['host'], options['port'])


def extract_options(url):
    """ Given a site, decide if cookies are allowed, if only some sites
    will not be blocked, etc.

    """

    host = None if url is None else tldextract.extract(url).domain

    options_sites = get_options()['sites']
    options = options_sites['general']

    if host not in options_sites.keys():
        print("GENERAL")
    else:
        options = options_sites[host]
        print("INSTANCE: {prefix}".format_map(options))

    return options
