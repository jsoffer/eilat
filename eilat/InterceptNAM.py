# -*- coding: utf-8 -*-

"""

  Copyright (c) 2013, 2014 Jaime Soffer

   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

   Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   Neither the name of the involved organizations nor the names of its
   contributors may be used to endorse or promote products derived from this
   software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
   ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
   LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
   SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
   INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
   CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
   THE POSSIBILITY OF SUCH DAMAGE.

"""

from urllib.parse import parse_qsl

from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkRequest,
                             QNetworkDiskCache)
from PyQt5.QtCore import QUrl

from eilat.CookieJar import CookieJar
from eilat.libeilat import (is_local, non_whitelisted,
                            is_font, is_numerical,
                            encode_blocked)
from eilat.global_store import database, get_options

from pprint import PrettyPrinter
import tldextract

from colorama import Fore, Style

from os.path import expanduser

from re import sub

DO_NOT_STORE = [
    "duckduckgo.com", "t.co", "i.imgur.com", "imgur.com"
]


def compare_host(host1, host2):
    """ True if the domain.suffix part of both hosts is the same """

    (_, domain1, suffix1) = tldextract.extract(host1)
    (_, domain2, suffix2) = tldextract.extract(host2)

    return domain1 == domain2 and suffix1 == suffix2


def show_info(info_map):
    """ Construct and disply a colorized string to show
    information for a reply

    """

    result = "{}{}: {}[{}] {}".format(info_map['color_status'],
                                      info_map['status'],
                                      info_map['main_color'],
                                      highlight(info_map['source'],
                                                show_path=False,
                                                iframe=info_map['iframe']),
                                      highlight(info_map['resource']))
    result += Fore.RESET

    print(result)


def highlight(qurl, show_path=True, full=False, iframe=False):
    """ Colorizes the address stored in 'qurl'; if 'full' is false,
    it will print only the filename in the end of the path (if any)
    instead of the full path.

    """

    (subdomain, domain, suffix) = tldextract.extract(qurl.host())

    host = "{}.{}{}.{}".format(subdomain,
                               Style.BRIGHT, domain, suffix)
    host = host.strip('.')

    if show_path:
        path = qurl.path()
        if path and not full and qurl.scheme() != 'data':
            path = path.split('/')[-1]

        if path and qurl.scheme() == 'data':
            path = path.split(';')[0]
            return "[data] {}".format(path)

    port = ":{}".format(qurl.port()) if qurl.port() >= 0 else ''
    if port:
        host += port

    if show_path and qurl.scheme() != 'http':
        host = "[{}] {}".format(qurl.scheme(), host)

    if iframe:
        host = "* {}".format(host)

    result = "{}{}{}".format(Style.NORMAL, host, Style.NORMAL)
    if show_path:
        result += " {}".format(path)

    return result


def show_labeled(label, url, color=Fore.RESET, full=False, detail=None):
    """ Creates a colorized ' LABEL: [source] url path   '
        string to display as log output

    """

    result = "{}{}: {}{}".format(
        Fore.RESET,
        label,
        color,
        highlight(url, full=full))

    if detail:
        result += "\n\t> {}".format(detail)

    result += Fore.RESET

    print(result)

PRINTER = PrettyPrinter(indent=4).pprint


class InterceptNAM(QNetworkAccessManager):
    """ Reimplements the Network Access Manager to see what's being requested
    by web pages, besides of the page itself. Has primitive support to allow
    requests only from whitelisted sites.

    """

    def __init__(self, instance, parent=None):
        super(InterceptNAM, self).__init__(parent)
        print("INIT InterceptNAM")

        self.__instance = instance
        self.prefix = get_options()['sites'][instance]['prefix']

        self.show_detail = False
        self.load_webfonts = False

        # reference needed to save in shutdown
        self.cookie_jar = CookieJar(parent=self,
                                    options=get_options()['sites'][instance])
        self.setCookieJar(self.cookie_jar)

        self.setCache(DiskCacheDir(instance, parent=self))

        def reply_complete(reply):
            """ Prints when a request completes, handles the filter that
            chooses between successful and filtered requests

            Replies only - if the request doesn't have to go
            through the network, it will not be reported here

            """

            qurl = reply.url()
            s_url = qurl.toString()

            status = reply.attribute(
                QNetworkRequest.HttpStatusCodeAttribute)

            if is_local(qurl) or status is None:
                return

            # 'status' will never be None from here on

            # used only once
            color_status = Fore.GREEN if reply.attribute(
                QNetworkRequest.SourceIsFromCacheAttribute) else Fore.RED

            # was it a filtered reply?
            # used only once
            color = Fore.BLUE if 200 <= status < 400 else Fore.RED

            origin = reply.request().originatingObject()

            if origin:
                # used only once
                not_same = not compare_host(
                    origin.requestedUrl().host(), qurl.host())
            else:
                print("NO ORIGINATING OBJECT", s_url)
                return

            in_iframe = origin != origin.page().mainFrame()

            # this is the response to the original .load(), not a
            # resource loaded by the page itself
            if origin.requestedUrl() == qurl and not in_iframe:
                host = sub("^www.", "", qurl.host())
                path = qurl.path().rstrip("/ ")

                if (
                        (host not in DO_NOT_STORE) and
                        (not qurl.hasQuery()) and
                        len(path.split('/')) < 4 and
                        200 <= status < 400):
                    database().store_navigation(host, path, self.prefix)

            if not_same or in_iframe:
                info = {
                    'color_status': color_status,
                    'status': status,
                    'resource': qurl,
                    'source': origin.requestedUrl(),
                    'main_color': color,
                    'iframe': in_iframe}
                show_info(info)

        # finished carries QNetworkReply
        self.finished.connect(reply_complete)

        def handle_ssl_error(reply, errors):
            """ Callback to connect to when a SSL error happens

            This ignores the error before reporting it; that means all
            "issuer certificate could not be found" and similar will be
            accepted but reported. Until a better way to handle is
            implemented, keep an eye on the console when counting on SSL.
            This can and will create security issues.

            """

            reply.ignoreSslErrors()
            show_labeled("SSL",
                         reply.url(),
                         detail="/".join([k.errorString() for k in errors]),
                         color=Fore.RED)

        self.sslErrors.connect(handle_ssl_error)

    def __pass(self, operation, request, data, info=None):
        """ short for "ignore filter, just generate the request" """

        if info is not None and info['notify']:
            show_labeled(info['message'], info['qurl'], color=info['color'])

        return QNetworkAccessManager.createRequest(
            self, operation, request, data)

    def __block(self, message, info=None):
        """ short for "ignore request; generate default empty request" """

        if info is not None and info['notify']:
            show_labeled(info['message'], info['qurl'],
                         color=info['color'], detail=info['detail'])

        return QNetworkAccessManager.createRequest(
            self,
            QNetworkAccessManager.GetOperation,
            QNetworkRequest(QUrl(message)),
            None)

    def create_request(self, operation, request, data):
        """ Reimplemented to intercept requests. Stops blacklisted requests

        """

        request.setAttribute(
            QNetworkRequest.HttpPipeliningAllowedAttribute, True)

        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute,
                             QNetworkRequest.PreferCache)

        qurl = request.url()
        url = qurl.toString()

        info = {'notify': self.show_detail,
                'message': None,
                'detail': None,
                'qurl': qurl,
                'color': Fore.GREEN}

        # if keeping a log of the POST data, do it before anything else
        if operation == QNetworkAccessManager.PostOperation:
            notify_post(data, url)

        # stop here if the request is local enough as for not
        # requiring further scrutiny
        if is_local(qurl) and not is_font(qurl):
            info['message'] = "LOCAL"
            return self.__pass(operation, request, data, info=info)

        # make optional the loading of webfonts
        if is_font(qurl):
            if self.load_webfonts:
                return self.__pass(operation, request, data)
            else:
                info['message'] = "TRIMMED WEBFONT"
                return self.__block("about:blank", info=info)

        # If the request is going to be intercepted a custom request is
        # built and returned after optionally reporting the reason

        whitelist = get_options()['sites'][self.__instance]['host_whitelist']

        info['color'] = Fore.RED

        for (stop_case, description, show) in [
                # it may be an un-dns'ed request; careful here
                (is_numerical(qurl.host()), "NUMERICAL", True),
                # whitelist exists, and the requested URL is not in it
                (non_whitelisted(whitelist, qurl),
                 "NON WHITELISTED", self.show_detail)
        ]:
            if stop_case:
                info['notify'] = show
                info['message'] = description
                return self.__block("about:blank", info=info)

        # It's not a local request; it should have a proper URL structure
        # then. 'domain' and 'suffix' must be non-None (and non-empty).

        (subdomain, domain, suffix) = tldextract.extract(url)
        subdomain = subdomain if subdomain != '' else None

        for (stop_case, description, detail, show) in [
                # if 'domain' or 'suffix' are not valid, stop;
                # should never happen (even though it does - some providers
                # don't have a proper 'domain' according to tldextract
                (domain == '' or suffix == '',
                 "SHOULD NOT HAPPEN", " {}|{}|{} ".format(subdomain,
                                                          domain,
                                                          suffix), True),

                # site is on a whitelist, but this instance does not use
                # whitelists; this means it belong to another instance,
                # assuming exclusivity
                # TODO 'domain + suffix' is a maybe bad generalization
                (whitelist is None and
                 domain + '.' + suffix in get_options()['all_whitelists'],
                 "NEG-WL FILTER", "{} || {} || {} ".format(
                     subdomain,
                     domain,
                     suffix), self.show_detail)
        ]:
            if stop_case:
                info['message'] = description
                info['detail'] = detail
                return self.__block(encode_blocked(description, url),
                                    info=info)

        return self.__pass(operation, request, data)

    # Clean reimplement for Qt
    # pylint: disable=C0103
    createRequest = create_request
    # pylint: enable=C0103


def notify_post(data, url):
    """ 'data' being from a POST request, watch (but don't consume) its
    contents, and report them in a notification

    """

    try:
        post_str = data.peek(4096).data().decode()
        print("_-_-_-_")
        print(url)
        PRINTER(parse_qsl(post_str, keep_blank_values=True))
        print("-_-_-_-")
    except UnicodeDecodeError:
        print("Binary POST upload")


class DiskCacheDir(QNetworkDiskCache):
    """ near-empty reimplementation of QNetworkDiskCache, only to avoid
    setting the directory and cache size after construction

    """

    def __init__(self, instance, parent=None):
        super(DiskCacheDir, self).__init__(parent)

        self.setCacheDirectory(
            expanduser("~/.eilat/caches/cache{prefix}".format_map(
                get_options()['sites'][instance])))
        self.setMaximumCacheSize(1024 * 1024 * 128)
