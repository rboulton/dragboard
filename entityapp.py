import getentities
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
try:
    from simplejson import json
except ImportError:
    try:
        import django.utils.simplejson as json
    except ImportError:
        import json

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Hello, webapp World!')

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
                                      ('/entities', EntitiesPage),
                                      ('/entity', EntityPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
