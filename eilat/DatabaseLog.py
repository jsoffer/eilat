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

from os.path import expanduser

from PyQt4.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery

class DatabaseLogLite(object):
    """ Low load only; using SQLite
    To store bookmarks, configuration, etc.

    """
    def __init__(self, prefix):

        self.litedb = QSqlDatabase("QSQLITE")
        self.litedb.setDatabaseName(expanduser("~/.eilat/eilat.db"))
        self.litedb.open()

        if prefix != '':
            self.table = 'navigation_' + prefix.lower()
        else:
            self.table = 'navigation'

        query_nav = QSqlQuery(
            "select host || path from %s " % (self.table) +
            "order by count desc",
            self.litedb)

        self.model = QSqlQueryModel()
        self.model.setQuery(query_nav)

    def store_navigation(self, host, path):
        """ save host, path and increase its count """

        host = host.replace("'", "%27")
        path = path.replace("'", "%27")

        insert_or_ignore = (
            "insert or ignore into %s (host, path) " % (self.table) +
            "values ('%s', '%s')" % (host, path))

        update = (
            "update %s set count = count + 1 where " % (self.table) +
            "host = '%s' and path = '%s'" % (host, path))

        self.litedb.exec_(insert_or_ignore)
        self.litedb.exec_(update)

    def is_blacklisted(self, domain, suffix, subdomain=None):
        """ Returns a bool indicating if subdomain.domain.tld is
        going to be blocked

        Missing case: when we'll blanket block all suffixes and
        subdomains of a domain

        """

        check_tld = (
            "select count(*) from blacklist where " +
            "domain = '%s' and tld = '%s'" % (domain, suffix))

        query_tld = QSqlQuery(check_tld, self.litedb)
        query_tld.exec_()
        query_tld.next()
        blacklisted_tld = bool(query_tld.value(0))

        if not blacklisted_tld:
            return False

        # first, if there's a no-subdomain entry, it covers everything
        check_no_subdomain = (
            "select count(*) from blacklist where " +
            "domain = '%s' and tld = '%s' " % (domain, suffix) +
            "and subdomain is null")

        query_no_subdomain = QSqlQuery(check_no_subdomain, self.litedb)
        query_no_subdomain.exec_()
        query_no_subdomain.next()
        blacklisted_plus_no_subdomain = bool(query_no_subdomain.value(0))

        if blacklisted_plus_no_subdomain:
            return True

        # lastly (rare case), if only a subdomain is blacklisted,
        # let's check if it's this one

        if subdomain is None:
            return False

        check_subdomain = (
            "select count(*) from blacklist where " +
            "domain = '%s' and tld = '%s' " % (domain, suffix) +
            "and subdomain = '%s'" % (subdomain))

        query_subdomain = QSqlQuery(check_subdomain, self.litedb)
        query_subdomain.exec_()
        query_subdomain.next()
        blacklisted_plus_subdomain = bool(query_subdomain.value(0))

        return blacklisted_plus_subdomain
