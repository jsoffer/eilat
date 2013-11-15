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

import json
import psycopg2 as postgres

from time import time

from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt4.Qt import QUrl

# local
from libeilat import log, printHost, printHeaders

class InterceptNAM(QNetworkAccessManager):
    def __init__(self, parent=None, whitelist=None):
        print "INIT InterceptNAM"
        self.instance_id = time()
        self.count = 0
        self.cheatgc = []
        self.whitelist = whitelist

        self.db_conn = postgres.connect("dbname=pguser user=pguser")
        self.db_cursor = self.db_conn.cursor()

        super(InterceptNAM, self).__init__(parent)

    def createRequest(self, operation, request, data):

        # Storables:
        # + datetime
        # - operation
        # * request:
        #     + url: toString
        #     * scheme, path, host, port, fragment, query (json)
        #     + originatingObject (frame): parentFrame (recursive), requesterUrl
        #     * headers (request, json)
        #     - priority
        # * data: split as query (json)

        #qurl = request.url()
        # falta puerto, fragmento...
        #url = unicode(qurl.scheme() + "://" + qurl.host() + qurl.path())
        #if operation == QNetworkAccessManager.PostOperation:
        #    post_str =  unicode(data.peek(4096))
        #    if post_str:
        #        try:
        #            print "POST < " + " ".join(map(lambda (a,b): "("+a+" => "+b+")", map(lambda k: k.split('='), post_str.split('&'))))
        #        except:
        #            print post_str
        #    else:
        #        print "POST < ()"
        #if qurl.scheme() == "data":
        #    print "<-- " + url.split(',')[0]
        #else:
        #    if qurl.hasQuery():
        #        print "QRY  < " + " ".join((map(lambda (a,b): unicode("(" + a + " => " + b +")"), qurl.queryItems())))
        #    print "<"+unicode(operation)+"< " + url
        if self.whitelist:
            if not any(map(lambda k: request.url().host()[-len(k):] == k, self.whitelist)):
                print "FILTERING %s" % request.url().toString()
                return QNetworkAccessManager.createRequest(self, operation, QNetworkRequest(QUrl("about:blank")), data)

        response = QNetworkAccessManager.createRequest(self, operation, request, data)
        #response.error.connect(lambda: printHost(response, "ERROR> " ))
        def filtra(xs):
            ret = {}
            for (p,q) in xs:
                ret[unicode(p)] = unicode(q)
            return json.dumps(ret).replace("'","''")

        def s(x):
            return x.replace("'","''")

        def indice(r, k):
            # please don't do garbage collection...
            self.cheatgc.append(r)
            self.cheatgc.append(k)
            def ret():
                try:
                    # Storables:
                    # + reply's datetime
                    # + k (indice)
                    # * ID de sesión y de instancia de navegador
                    #   reply:
                    #    + headers (reply)
                    #    - url: mismos campos (puede variar desde el request)

                    encabezados = filtra(r.rawHeaderPairs())
                    query = "INSERT INTO reply (at, instance, id, url, t) values (now(), %s, %s, '%s','%s')" % (self.instance_id, k, s(r.url().toString()), encabezados)
                    self.db_cursor.execute(query)
                    self.db_conn.commit()

                    # ...until we're done with the request
                    # (pyqt/sip related trouble)
                    try:
                        self.cheatgc.remove(r)
                        self.cheatgc.remove(k)
                        print "[PENDING: %s] " % (len(self.cheatgc)),
                    except Exception as e:
                        print ">>> Exception: %s" % (e)
                except NameError:
                    print "Except NameError!"
                except Exception as e:
                    print "+++ Except %s" % (e)

            return ret
        response.finished.connect(indice(response, self.count))
        #log(unicode(self.count) + " > " + request.url().toString() + " [" +request.originatingObject().requestedUrl().toString() + "]")
        root = request.originatingObject().parentFrame()
        frame = request.originatingObject()
        while root:
            frame = root
            root = root.parentFrame()
        query = "INSERT INTO request (at, instance, id, url, frame) values (now(), %s, %s, '%s','%s')" % (self.instance_id, self.count, s(request.url().toString()), s(frame.url().host()))
        self.db_cursor.execute(query)
        self.db_conn.commit()
        self.count += 1
        return response

