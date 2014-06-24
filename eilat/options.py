"""
Default values for NAM instances

"""

import tldextract

import yaml
from os.path import expanduser


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
