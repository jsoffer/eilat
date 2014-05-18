# -*- coding: utf-8 -*-

"""

  Copyright (c) 2013, Jaime Soffer

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

# to keep some support of python2
try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt4.Qt import QUrl

from libeilat import es_url_local, usando_whitelist, es_font, es_num_ip

from pprint import PrettyPrinter

class InterceptNAM(QNetworkAccessManager):
    """ Reimplements the Network Access Manager to see what's being requested
    by web pages, besides of the page itself. Has primitive support to allow
    requests only from whitelisted sites.

    """

    def __init__(self, prefix, log=None, parent=None, whitelist=None):
        super(InterceptNAM, self).__init__(parent)
        print("INIT InterceptNAM")

        self.whitelist = whitelist
        self.prefix = prefix
        self.log = log
        self.cheatgc = []

        self.showing_accepted = True

        self.printer = PrettyPrinter(indent=4).pprint

    def show_pending(self):
        """ List of requests that haven't sent 'finished' signal """

        print("PENDING")
        self.printer([reply.url().toString() for reply in self.cheatgc])

    def create_request(self, operation, request, data):
        """ Reimplemented to intercept requests. Stops blacklisted requests,
        matches requests with replies. Stores on a PostgreSQL database.

        """

        qurl = request.url()

        if es_url_local(qurl) and not es_font(qurl):
            print("LOCAL")
            return QNetworkAccessManager.createRequest(
                    self, operation, request, data)

        if (usando_whitelist(self.whitelist, qurl) or
                es_font(qurl) or es_num_ip(request.url().host())):
            # different 'flows' for shown, filtered
            #print("FILTERING %s" % qurl.toString()[:255])
            return QNetworkAccessManager.createRequest(
                self,
                QNetworkAccessManager.GetOperation,
                QNetworkRequest(QUrl("about:blank")),
                None)

        if operation == QNetworkAccessManager.PostOperation:
            post_str = data.peek(4096).data().decode()
            print("_-_-_-_")
            print(qurl.toString())
            self.printer(parse_qsl(post_str, keep_blank_values=True))
            print("-_-_-_-")

        request.setAttribute(
                QNetworkRequest.HttpPipeliningAllowedAttribute, True)

        response = QNetworkAccessManager.createRequest(
                self, operation, request, data)

        self.cheatgc.append(response)

        def tell_response():
            """ Callback; closes around 'response' """

            status = response.attribute(
                        QNetworkRequest.HttpStatusCodeAttribute)

            if ((self.showing_accepted and
                status is not None and status < 400) or
                (not self.showing_accepted and
                    (status is None or status >= 400))):
                print(str(status) + " " + response.url().toString())

            self.cheatgc.remove(response)
            #print(self.cheatgc)

        response.finished.connect(tell_response)

        #self.printer([reply.url().toString() for reply in self.cheatgc])
        return response

    # Clean reimplement for Qt
    # pylint: disable=C0103
    createRequest = create_request
    # pylint: enable=C0103
