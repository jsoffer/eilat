"""
Default values for NAM instances

"""

import tldextract

import yaml
from os.path import expanduser

def proxy_options():
    """ Extracts the proxy information from YAML user settings. If any is
    empty, proxy will be disabled. If the fields do not exist (not checked)
    the app will fail hard.

    """
    with open(expanduser("~/.eilat/options.yaml")) as yaml_file:
        options = yaml.safe_load(yaml_file)['proxy']

    return (options['host'], options['port'])

def extract_options(url):
    """ Given a site, decide if cookies are allowed, if only some sites
    will not be blocked, etc.

    """

    host = None if url is None else tldextract.extract(url).domain

    with open(expanduser("~/.eilat/options.yaml")) as yaml_file:
        options_yaml = yaml.safe_load(yaml_file)
        options_sites = options_yaml['sites']

    options = options_sites['general']

    if not host in options_sites.keys():
        print("GENERAL")
    else:
        options = options_sites[host]
        print("INSTANCE: %s" % options['prefix'])

    return options
