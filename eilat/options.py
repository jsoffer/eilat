"""
Default values for NAM instances

"""

import tldextract


def extract_options(url):
    """ Given a site, decide if cookies are allowed, if only some sites
    will not be blocked, etc.

    """

    options = OPTIONS['general']

    host = None if url is None else tldextract.extract(url).domain

    if not host in OPTIONS.keys():
        print("GENERAL")
    else:
        options = OPTIONS[host]
        print("INSTANCE: %s" % options['prefix'])

    return options

OPTIONS = {
    'general': {
        'host_whitelist': None,
        'cookie_allow': [
            "github.com"],
        'cookie_file': None,
        'prefix': ""},

    'reddit': {
        'host_whitelist': [
            "reddit.com/r/programming",
            "reddit.com/r/Python",
            "reddit.com/r/haskell"
        ],
        'cookie_allow': None,
        'cookie_file': None,
        'prefix': "RD"
    },

    'linkedin': {
        'host_whitelist': [
            "linkedin.com",
            "licdn.com"
        ],
        'cookie_allow': ["linkedin.com"],
        'cookie_file': "licookies.cj",
        'prefix': "LI"
    },

    'youtube': {
        'host_whitelist': [
            "youtube.com",
            "ytimg.com"
        ],
        'cookie_allow': None,
        'cookie_file': None,
        'prefix': "YT"
    },

    'facebook': {
        'host_whitelist': [
            "facebook.com",
            "akamaihd.net",
            "fbcdn.net"],
        'cookie_allow': ["facebook.com"],
        'cookie_file': "fbcookies.cj",
        'prefix': "FB"
    },

    'twitter': {
        'host_whitelist': ["twitter.com", "twimg.com"],
        'cookie_allow': ["twitter.com"],
        'cookie_file': "twcookies.cj",
        'prefix': "TW"
    },

    'google': {
        'host_whitelist': [
            "google.com",
            "google.com.mx",
            "googleusercontent.com",
            "gstatic.com",
            "googleapis.com"],
        'cookie_allow': ["google.com"],
        'cookie_file': "gcookies.cj",
        'prefix': "G"
    }
}
