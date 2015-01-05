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

    all_whitelists = [options_yaml['sites'][k]['host_whitelist']
                      for k in options_yaml['sites']]
    all_whitelists = [k for k in all_whitelists if k is not None]  # filter
    all_whitelists = [x for y in all_whitelists for x in y]  # flatten
    all_whitelists = [k.split('/')[0] for k in all_whitelists]  # no paths

    options_yaml['all_whitelists'] = set(all_whitelists)  # no repetitions
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
    options = None

    if host in options_sites.keys():
        options = options_sites[host]
    else:
        options = options_sites['general']

    return options
