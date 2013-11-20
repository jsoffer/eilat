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

from psycopg2 import connect as postgresql_connect
from libeilat import escape

class DatabaseLog(object):
    """ A database layer to be shared through all the application run """
    def __init__(self):
        self.db_conn = postgresql_connect("dbname=pguser user=pguser")
        self.db_cursor = self.db_conn.cursor()

    def run(self, query):
        """ Execute a query, store it. This is not the proper way.
        The 'commit' should happen only once after a page is complete.
        This can be conflictive on pages like gmail where the 'finished'
        signal appears to never happen.

        """
        self.db_cursor.execute(query)
        self.db_conn.commit()

    def store_request(self, instance_id, idx, url, frame):
        """ Fill the table 'request' """
        query = """ INSERT INTO request
            (at, instance, id, url, frame)
            values (now(), %s, %s, '%s','%s') """
        self.run(query % (instance_id, idx, escape(url), escape(frame)))

    def store_reply(self, instance_id, idx, url, status, headers):
        """ Fill the table 'reply' """
        query = """ INSERT INTO reply
            (at, instance, id, url, status, t)
            values (now(), %s, %s, '%s', %s, '%s') """
        self.run(query %
                (instance_id, idx, escape(url), status, escape(headers)))
