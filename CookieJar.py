from PyQt4.QtNetwork import QNetworkCookieJar, QNetworkCookie

class CookieJar(QNetworkCookieJar):
    def __init__(self, parent=None, allowed = [], storage=None):
        super(CookieJar, self).__init__(parent)
        print "INIT CookieJar"
        self.allowed = allowed
        if storage:
            try:
                fh = open(storage,"r")
                cookies = map(lambda k: QNetworkCookie.parseCookies(k), fh.readlines())
                cookies = [x for y in cookies for x in y]
                #print unicode(cookies)
                self.setAllCookies(cookies)
            except Exception as e:
                print e
                print "\nCOOKIES: empty?"

    def setCookiesFromUrl(self,cookies,url):
        if ".".join(url.host().split('.')[-2:]) not in self.allowed:
            ret = []
        else:
            ret = cookies
        if ret:
            print "\n< COOKIES " + url.host() + url.path() + ": " + ", ".join(map(lambda k: "["+unicode(k.domain())+unicode(k.path())+"]" + unicode(k.name()) + " => " + unicode(k.value()), ret))
        return QNetworkCookieJar.setCookiesFromUrl(self,ret,url)
    def cookiesForUrl(self,url):
        ret = QNetworkCookieJar.cookiesForUrl(self,url)
        #if ret:
            #print "> COOKIES " + unicode(map(lambda k: k.toRawForm(), ret))
        #    print "> COOKIES " + url.host() + url.path() + ": " + ", ".join(map(lambda k: "["+unicode(k.domain())+unicode(k.path())+"]" + unicode(k.name()) + " => " + unicode(k.value()), ret))
        return ret
