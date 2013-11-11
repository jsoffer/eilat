from PyQt4.QtNetwork import QNetworkCookieJar

class CookieJar(QNetworkCookieJar):
    def setCookiesFromUrl(self,cookies,url):
        print "COOKIES " + url.host() + ": " + ", ".join(map(lambda k: "["+unicode(k.domain())+"]" + unicode(k.name()) + " => " + unicode(k.value()), cookies))
        return QNetworkCookieJar.setCookiesFromUrl(self,cookies,url)
