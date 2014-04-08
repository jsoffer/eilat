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

from __future__ import unicode_literals, print_function

from urlparse import parse_qsl

from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt4.Qt import QUrl

from PyQt4.QtCore import QString

from libeilat import filtra, notnull, es_url_local, usando_whitelist, es_font

OPERATIONS = {
        1: "HEAD",
        2: "GET",
        3: "PUT",
        4: "POST",
        5: "DELETE",
        6: "CUSTOM"
        }

class InterceptNAM(QNetworkAccessManager):
    """ Reimplements the Network Access Manager to see what's being requested
    by web pages, besides of the page itself. Has primitive support to allow
    requests only from whitelisted sites.

    """

    def __init__(self, name, log=None, parent=None, whitelist=None):
        super(InterceptNAM, self).__init__(parent)
        print("INIT InterceptNAM")
        self.count = -1
        self.cheatgc = []

        self.whitelist = whitelist
        self.name = name
        self.log = log

    def create_request(self, operation, request, data):
        """ Reimplemented to intercept requests. Stops blacklisted requests,
        matches requests with replies. Stores on a PostgreSQL database.

        """
        self.count += 1
        qurl = request.url()

        if es_url_local(qurl) and not es_font(qurl):
            return QNetworkAccessManager.createRequest(
                    self, operation, request, data)

        if (usando_whitelist(self.whitelist, qurl) or
                es_font(qurl)):
            print("FILTERING %s" % qurl.toString()[:255])
            return QNetworkAccessManager.createRequest(
                self,
                operation,
                QNetworkRequest(QUrl("about:blank")),
                data)

        #request.setAttribute(
        #        QNetworkRequest.HttpPipeliningAllowedAttribute, True)

        response = QNetworkAccessManager.createRequest(
                self, operation, request, data)

        if operation == QNetworkAccessManager.PostOperation:
            post_str = unicode(QString.fromLocal8Bit(data.peek(4096)))
            data_json = filtra(parse_qsl(post_str, keep_blank_values=True))
        else:
            data_json = None

        def indice(reply, idx):
            """ This function returns a closure enclosing the current index
            and its associated reply. This is required since there's no
            knowing when (if at all) a request will be replied to; once it
            happens, the index will surely have changed.

            The 'cheatgc' list is required because of a bug where the reference
            for the 'reply' and 'idx' objects is lost sometimes after 'ret'
            completes, despite having created a closure referencing them. By
            appending to the list, garbage collection is prevented.

            """

            # please don't do garbage collection...
            self.cheatgc.append(reply)
            self.cheatgc.append(idx)

            def ret():
                """ Closure; freezes 'reply' and 'idx' so they will be
                accessible at the time the request finalizes and this closure
                is called.

                """
                encabezados = filtra(reply.rawHeaderPairs())
                (statuscode, _) = reply.attribute(
                        QNetworkRequest.HttpStatusCodeAttribute).toInt()

                if self.log:
                    self.log.store_reply({
                        "id": self.log.instance_id,
                        "idx": idx,
                        "scheme": unicode(reply.url().scheme()),
                        "host": unicode(reply.url().host()),
                        "path": unicode(reply.url().path()),
                        "query": filtra(reply.url().encodedQueryItems()),
                        "fragment": notnull(
                            unicode(reply.url().fragment())),
                        "status": statuscode,
                        "headers": encabezados
                        })

                # ...until we're done with the request
                # (pyqt/sip related trouble)
                self.cheatgc.remove(reply)
                self.cheatgc.remove(idx)
                #print "[%s]" % (len(self.cheatgc))

            return ret

        response.finished.connect(indice(response, self.count))

        if self.log:
            headers = []
            for header in request.rawHeaderList():
                headers.append((header, request.rawHeader(header)))

            self.log.store_request({
                "id": self.log.instance_id,
                "idx": self.count,
                "op": OPERATIONS[operation],
                "scheme": unicode(request.url().scheme()),
                "host": unicode(request.url().host()),
                "path": unicode(request.url().path()),
                "query": filtra(request.url().encodedQueryItems()),
                "fragment": notnull(
                    unicode(request.url().fragment())),
                "data": data_json,
                "source": unicode(
                    request.originatingObject().requestedUrl().host()),
                "headers": filtra(headers)
                })

        return response

    # Clean reimplement for Qt
    # pylint: disable=C0103
    createRequest = create_request
    # pylint: enable=C0103
