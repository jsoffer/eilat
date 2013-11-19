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
from psycopg2 import connect as postgresql_connect

from time import time

from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt4.Qt import QUrl

# local
#from libeilat import log

class InterceptNAM(QNetworkAccessManager):
    """ Reimplements the Network Access Manager to see what's being requested
    by web pages, besides of the page itself. Has primitive support to allow
    requests only from whitelisted sites.

    """

    def __init__(self, parent=None, whitelist=None):
        super(InterceptNAM, self).__init__(parent)
        print "INIT InterceptNAM"
        self.instance_id = time()
        self.count = 0
        self.cheatgc = []
        self.whitelist = whitelist

        self.db_conn = postgresql_connect("dbname=pguser user=pguser")
        self.db_cursor = self.db_conn.cursor()

    # Reimplemented from PyQt
    # pylint: disable=C0103
    def createRequest(self, operation, request, data):
        """ Reimplemented to intercept requests. Stops blacklisted requests,
        matches requests with replies. Stores on a PostgreSQL database.

        """
        if (request.url().scheme() in ['data','file']
                or request.url().host() == 'localhost'):
            return QNetworkAccessManager.createRequest(
                    self, operation, request, data)

        if self.whitelist:
            if not any(
                    [request.url().host()[-len(k):] == k
                        for k in self.whitelist]):
                print "FILTERING %s" % request.url().toString()
                return QNetworkAccessManager.createRequest(
                        self,
                        operation,
                        QNetworkRequest(QUrl("about:blank")),
                        data)

        response = QNetworkAccessManager.createRequest(
                self, operation, request, data)

        def filtra(cookies):
            """ Converts a [(key,value)] list of cookies first to a dictionary
            and then to JSON. Single quotes are duplicated to allow PostgreSQL
            storage (a double single quote inside a string is a escape).

            """
            ret = {}
            for (key, value) in cookies:
                ret[unicode(key)] = unicode(value)
            return json.dumps(ret).replace("'","''")

        def escape(data):
            """ Escape quotes and limit the data length. """
            return data.replace("'","''")[:4095]

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
                try:
                    encabezados = filtra(reply.rawHeaderPairs())
                    (statuscode, _) = reply.attribute(
                            QNetworkRequest.HttpStatusCodeAttribute).toInt()
                    query = """INSERT INTO reply
                    (at, instance, id, url, status, t)
                    values (now(), %s, %s, '%s', %s, '%s')""" % (
                            self.instance_id,
                            idx,
                            escape(reply.url().toString()),
                            statuscode,
                            encabezados)
                    self.db_cursor.execute(query)
                    self.db_conn.commit()

                    # ...until we're done with the request
                    # (pyqt/sip related trouble)
                    self.cheatgc.remove(reply)
                    self.cheatgc.remove(idx)
                    print "[%s]" % (len(self.cheatgc))
                except NameError as name_error:
                    print name_error
                    print "Except NameError!"

            return ret
        response.finished.connect(indice(response, self.count))
        root = request.originatingObject().parentFrame()
        frame = request.originatingObject()
        while root:
            frame = root
            root = root.parentFrame()
        query = """INSERT INTO request
        (at, instance, id, url, frame)
        values (now(), %s, %s, '%s','%s')""" % (
                self.instance_id,
                self.count,
                escape(request.url().toString()),
                escape(frame.url().host()))
        self.db_cursor.execute(query)
        self.db_conn.commit()
        self.count += 1
        return response
    # pylint: enable=C0103
