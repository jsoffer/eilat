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

from os.path import expanduser, isfile

from PyQt5.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery


class DatabaseLogLite(object):
    """ Low load only; using SQLite
    To store bookmarks, configuration, etc.

    """
    def __init__(self):

        # ###### STARTUP

        super(DatabaseLogLite, self).__init__()
        self.litedb = QSqlDatabase("QSQLITE")

        db_file = expanduser("~/.eilat/eilat.db")
        rebuild = not isfile(db_file)

        self.litedb.setDatabaseName(db_file)
        self.litedb.open()

        if rebuild:
            query_mknav = (
                "CREATE TABLE navigation (host TEXT NOT NULL," +
                " path TEXT, count INTEGER default 0, prefix char(2)," +
                " PRIMARY KEY (host, path))")

            query_mkblacklist = (
                "CREATE TABLE blacklist (subdomain text," +
                " domain text, tld text, primary key(domain, tld, subdomain))")

            inserts = [
                ('google', 'com'),
                ('googleusercontent', 'com'),
                ('gstatic', 'com'),
                ('googleapis', 'com'),
                ('facebook', 'com'),
                ('fbcdn', 'net'),
                ('twitter', 'com'),
                ('twimg', 'com')]

            query_insertbl = (
                "INSERT INTO blacklist values (NULL, '{}', '{}')")

            self.litedb.exec_(query_mknav)
            self.litedb.exec_(query_mkblacklist)

            for host, tld in inserts:
                self.litedb.exec_(query_insertbl.format(host, tld))

        # ###### VALIDATION
        # verifies database structure, not datatypes

        tables = self.litedb.tables()
        tables_ok = [k in tables for k in ['navigation', 'blacklist']]
        if not all(tables_ok):
            raise RuntimeError("tables missing from database")

        fnav_ok = [self.litedb.record('navigation').contains(k)
                   for k in ['host', 'path', 'count', 'prefix']]

        if not all(fnav_ok):
            raise RuntimeError("bad structure for 'navigation' table")

        fbl_ok = [self.litedb.record('blacklist').contains(k)
                  for k in ['subdomain', 'domain', 'tld']]

        if not all(fbl_ok):
            raise RuntimeError("bad structure for 'blacklist' table")

        # it seems to be unable to do completion if 'model' creates and
        # returns a locally scoped variable... why?
        self.__models = {}

    def model(self, prefix=None):
        """ recreate the model each call; opening a new window will not
        be needed to use the recent completions

        """

        if prefix is None:
            query_nav = QSqlQuery(
                "select host || path from navigation " +
                "order by count desc",
                self.litedb)
        else:
            query_nav = QSqlQuery(
                "select host || path from navigation " +
                "where prefix = '{}' ".format(prefix) +
                "order by count desc",
                self.litedb)

        self.__models[prefix] = QSqlQueryModel()
        self.__models[prefix].setQuery(query_nav)
        return self.__models[prefix]

        # return completion_model

    def store_navigation(self, host, path, prefix):
        """ save host, path and increase its count """

        host = host.replace("'", "%27")
        path = path.replace("'", "%27")

        insert_or_ignore = (
            "insert or ignore into navigation (host, path, prefix) " +
            "values ('{}', '{}', '{}')".format(host, path, prefix))

        update = (
            "update navigation set count = count + 1 where " +
            "host = '{}' and path = '{}'".format(host, path))

        self.litedb.exec_(insert_or_ignore)
        self.litedb.exec_(update)

    def is_blacklisted(self, domain, suffix, subdomain=None):
        """ Returns a bool indicating if subdomain.domain.tld is
        going to be blocked

        Missing case: when we'll blanket block all suffixes and
        subdomains of a domain

        """

        def run_query(query):
            """ template; returns bool of existence of result """
            q_query = QSqlQuery(query, self.litedb)
            q_query.exec_()
            q_query.next()
            return bool(q_query.value(0))

        if not run_query(
                "select count(*) from blacklist where " +
                "domain = '{}' and tld = '{}'".format(domain, suffix)):
            return False

        # first, if there's a no-subdomain entry, it covers everything
        if run_query(
                "select count(*) from blacklist where " +
                "domain = '{}' and tld = '{}' ".format(domain, suffix) +
                "and subdomain is null"):
            return True

        # lastly (rare case), if only a subdomain is blacklisted,
        # let's check if it's this one

        if subdomain is None:
            return False

        return run_query(
            "select count(*) from blacklist where " +
            "domain = '{}' and tld = '{}' ".format(domain, suffix) +
            "and subdomain = '{}'".format(subdomain))
