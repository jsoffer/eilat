from PyQt4.QtNetwork import QNetworkCookieJar

class CookieJar(QNetworkCookieJar):
    def setCookiesFromUrl(self,cookies,url):
        print "< COOKIES " + url.host() + url.path() + ": " + ", ".join(map(lambda k: "["+unicode(k.domain())+unicode(k.path())+"]" + unicode(k.name()) + " => " + unicode(k.value()), cookies))
        return QNetworkCookieJar.setCookiesFromUrl(self,cookies,url)
    def cookiesForUrl(self,url):
        ret = QNetworkCookieJar.cookiesForUrl(self,url)
        if ret:
            print "> COOKIES " + url.host() + url.path() + ": " + ", ".join(map(lambda k: "["+unicode(k.domain())+unicode(k.path())+"]" + unicode(k.name()) + " => " + unicode(k.value()), ret))
        return ret
