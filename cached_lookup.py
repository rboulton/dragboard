from google.appengine.ext import db
from google.appengine.api.urlfetch import DownloadError
import datetime
import urllib2

class CachedLookup(db.Model):
    url = db.StringProperty(required=True)
    body = db.TextProperty(required=True)
    mtime = db.DateTimeProperty(auto_now=True)

def geturl(url):
    results = db.Query(CachedLookup).filter('url =', url.encode('utf8')).fetch(limit=1)
    if len(results) > 0:
        c = results[0]
        if c.mtime + datetime.timedelta(days=1) < datetime.datetime.now():
            c.delete()
        else:
            return c.body.encode('utf8')

    try:
        body = urllib2.urlopen(url).read()
    except DownloadError:
        raise
    l = CachedLookup(url=url.decode('utf8'), body=body.decode('utf8'))
    l.put()
    return body
