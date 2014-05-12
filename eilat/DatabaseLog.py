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

from time import time
from PyQt4.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery
from psycopg2 import connect as postgresql_connect

class DatabaseLogLite(object):
    """ Low load only; using SQLite
    To store bookmarks, configuration, etc.

    """
    def __init__(self, prefix):

        self.litedb = QSqlDatabase("QSQLITE")
        self.litedb.setDatabaseName("eilat.db")
        self.litedb.open()

        if prefix:
            self.table = 'navigation_' + prefix.lower()
        else:
            self.table = 'navigation'

        self.query_nav = QSqlQuery(
                "select host || path from " + self.table +
                " order by count desc", self.litedb)

        self.model = QSqlQueryModel()
        self.model.setQuery(self.query_nav)

    def store_navigation(self, host, path):
        """ save host, path and increase its count """

        insert_or_ignore = (
                "insert or ignore into " + self.table + " (host, path) " +
                "values (\"" + host + "\", \"" + path + "\")")

        update = (
                "update " + self.table + " set count = count + 1 where " +
                "host = \"" + host + "\" and path = \"" + path + "\"")

        self.litedb.exec_(insert_or_ignore)
        self.litedb.exec_(update)

class DatabaseLog(object):
    """ A database layer to be shared through all the application run """
    def __init__(self, prefix):

        self.prefix = prefix
        self.instance_id = time()
        self.db_conn = postgresql_connect(
                database="pguser",
                user="pguser",
                password="pgpass")
        self.db_cursor = self.db_conn.cursor()

        q_prepare_sreq = (
                "PREPARE store_request AS " +
                "INSERT INTO request " +
                "(at_time, instance, idx, op, headers, " +
                "scheme, host, path, query, fragment, data, source, prefix)" +
                "values (now(), $1, $2, $3, $4, $5, " +
                "$6, $7, $8, $9, $10, $11, $12)")
        self.db_cursor.execute(q_prepare_sreq)

        q_prepare_srep = (
                "PREPARE store_reply AS " +
                "INSERT INTO reply " +
                "(at_time, instance, idx, " +
                "scheme, host, path, query, fragment, " +
                "status, headers, prefix)" +
                "values (now(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10)")
        self.db_cursor.execute(q_prepare_srep)

    def run(self, query):
        """ Execute a query, store it. This is not the proper way.
        The 'commit' should happen only once after a page is complete.
        This can be conflictive on pages like gmail where the 'finished'
        signal appears to never happen.

        """
        self.db_cursor.execute(query)
        self.db_conn.commit()

    def store_request(self, dictionary):
        """ Fill the table 'request' """

        dictionary.update({'prefix': self.prefix})
        query = (
                "EXECUTE store_request " +
                "(%(id)s, %(idx)s, %(op)s, %(headers)s, " +
                "%(scheme)s, %(host)s, %(path)s, %(query)s, %(fragment)s, " +
                "%(data)s, %(source)s, %(prefix)s)")
        self.db_cursor.execute(query, dictionary)
        self.db_conn.commit()

    def store_reply(self, dictionary):
        """ Fill the table 'reply' """

        dictionary.update({'prefix': self.prefix})
        query = (
                "EXECUTE store_reply " +
                "(%(id)s, %(idx)s, " +
                "%(scheme)s, %(host)s, %(path)s, %(query)s, %(fragment)s, " +
                "%(status)s, %(headers)s, %(prefix)s)")
        self.db_cursor.execute(query, dictionary)
        self.db_conn.commit()
