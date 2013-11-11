from PyQt4.QtNetwork import QNetworkCookieJar

class CookieJar(QNetworkCookieJar):
    def __init__(self, parent=None, allowed = []):
        print "INIT CookieJar"
        self.allowed = allowed
        super(CookieJar, self).__init__(parent)

    def setCookiesFromUrl(self,cookies,url):
        if ".".join(url.host().split('.')[-2:]) not in self.allowed:
            ret = []
        else:
            ret = cookies
        if ret:
            print "< COOKIES " + url.host() + url.path() + ": " + ", ".join(map(lambda k: "["+unicode(k.domain())+unicode(k.path())+"]" + unicode(k.name()) + " => " + unicode(k.value()), ret))
        return QNetworkCookieJar.setCookiesFromUrl(self,ret,url)
    def cookiesForUrl(self,url):
        ret = QNetworkCookieJar.cookiesForUrl(self,url)
        if ret:
            print "> COOKIES " + url.host() + url.path() + ": " + ", ".join(map(lambda k: "["+unicode(k.domain())+unicode(k.path())+"]" + unicode(k.name()) + " => " + unicode(k.value()), ret))
        return ret
