import getentities
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import os
from render import render

try:
    from simplejson import json
except ImportError:
    try:
        import django.utils.simplejson as json
    except ImportError:
        import json

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        url = self.request.get('url', '')
        context = {}
        if url is not None:
            entities = getentities.get_entities(url)
            context.update(dict(url=url.encode('utf8'),
                                entities=entities.get('entities'),
                                categories=entities.get('categories'),
                               ))
        context['url'] = url
        self.response.out.write(render("index.html", context))

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
        entities['url'] = url
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(entities))

class EntityPage(webapp.RequestHandler):
    def get(self):
        url=self.request.get('ref')
        refs = getentities.get_entity_references(url)
        refs['url'] = url
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(refs))

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/ref', RefPage),
                                      ('/entities', EntitiesPage),
                                      ('/entity', EntityPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
