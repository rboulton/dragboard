import getentities
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import os
from render import render
import urllib

try:
    from simplejson import json
except ImportError:
    try:
        import django.utils.simplejson as json
    except ImportError:
        import json

try:
    from cached_lookup import geturl
except ImportError:
    def geturl(url):
        return urllib2.urlopen(url).read()

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(render("index.html", {}))

class TopicPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        search = self.request.get('search', '')
        gurl = ('http://content.guardianapis.com/search?q=%s&format=json' %
                urllib.quote(search))
        results = geturl(gurl)
        results = json.loads(results)
        try:
            results = results['response']['results']
        except KeyError:
            results = []
        context = dict(search=search)
        if len(results) > 0:
            url = results[0]['webUrl']
            entities = getentities.get_entities(url)
            context.update(dict(url=url.encode('utf8'),
                                entities=entities.get('entities'),
                                categories=entities.get('categories'),
                               ))
        self.response.out.write(render("topic.html", context))

class UrlPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        url = self.request.get('url', '')
        if not url.startswith('http'):
            url = 'http://' + url
        context = {}
        if url is not None:
            entities = getentities.get_entities(url)
            context.update(dict(url=url.encode('utf8'),
                                entities=entities.get('entities'),
                                categories=entities.get('categories'),
                               ))
        self.response.out.write(render("url.html", context))

class RefPage(webapp.RequestHandler):
    def get(self):
        ref = self.request.get('ref', '')
        context = dict(ref=ref,
                       name=self.request.get('name', None),
                       refs=getentities.get_entity_references(ref))
        self.response.out.write(render("ref.html", context))

class EntitiesPage(webapp.RequestHandler):
    def get(self):
        url=self.request.get('url')
        entities = getentities.get_entities(url)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(entities))

class EntityPage(webapp.RequestHandler):
    def get(self):
        url=self.request.get('ref')
        refs = getentities.get_entity_references(url)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(refs))

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/topic', TopicPage),
                                      ('/url', UrlPage),
                                      ('/ref', RefPage),
                                      ('/entities', EntitiesPage),
                                      ('/entity', EntityPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
