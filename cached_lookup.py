from google.appengine.ext import db
import datetime
import urllib2

class CachedLookup(db.Model):
    url = db.StringProperty(required=True)
    body = db.TextProperty(required=True)
    mtime = db.DateTimeProperty(auto_now=True)

def geturl(url):
    results = db.Query(CachedLookup).filter('url =', url).fetch(limit=1)
    if len(results) > 0:
        c = results[0]
        if c.mtime + datetime.timedelta(days=1) < datetime.datetime.now():
            c.delete()
        else:
            return c.body

    body = urllib2.urlopen(url).read()
    l = CachedLookup(url=url, body=body)
    l.put()
    return body
