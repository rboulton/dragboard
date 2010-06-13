import getentities
import datetime
from google.appengine.api import users
from google.appengine.ext import db
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


class BoardItem(db.Model):
    owner = db.UserProperty()
    board = db.StringProperty()
    url = db.StringProperty()
    title = db.TextProperty()
    source = db.TextProperty()
    content = db.TextProperty()
    x = db.IntegerProperty()
    y = db.IntegerProperty()
    wid = db.IntegerProperty()
    hgt = db.IntegerProperty()

class BoardMtimes(db.Model):
    board = db.StringProperty()
    mtime = db.DateTimeProperty(auto_now=True)

def get_board_mtime(board):
    mtimes = db.Query(BoardMtimes).filter('board =', board).fetch(1)
    if len(mtimes) == 0:
        return None
    return mtimes[0].mtime

def set_board_mtime(board):
    mtimes = db.Query(BoardMtimes).filter('board =', board).fetch(10)
    for mtime in mtimes:
        mtime.delete()
    item = BoardMtimes(board=board)
    item.put()

def get_board_updates():
    return db.Query(BoardMtimes).order('-mtime').fetch(30)

def get_board(board):
    user = users.get_current_user()
    return db.Query(BoardItem).filter('owner =', user).filter('board =', board).fetch(30)

def del_board_item(user, board, url):
    items = db.Query(BoardItem).filter('owner =', user).filter('board =', board).filter('url =', url).fetch(10)
    for item in items:
        item.delete()
    items = db.Query(BoardItem).filter('board =', board).fetch(10)
    if len(items) == 0:
        item = BoardMtimes(board=board)
        item.delete()

def add_board_item(user, board, url, title, source, content,
                   x=None, y=None, wid=None, hgt=None):
    if wid is None:
        wid = 400
    if hgt is None:
        hgt = 200
    if x is None or y is None:
        # FIXME - pick a good position automatically
        x = 0
        y = 0
    items = db.Query(BoardItem).filter('owner =', user).filter('board =', board).filter('url =', url)
    for item in items:
        item.delete()
    item = BoardItem(owner=user,
                     board=board,
                     url=url,
                     title=title,
                     source=source,
                     content=content,
                     x=x, y=y)
    item.put()
    set_board_mtime(board)

def move_board_item(user, board, url, x, y, wid, hgt):
    items = db.Query(BoardItem).filter('owner =', user).filter('board =', board).filter('url =', url)
    if len(items) == 0: return
    for item in items[1:]:
        item.delete()
    item = items[0]
    item.x = x
    item.y = y
    item.wid = wid
    item.hgt = hgt
    item.put()

class JinjaRequestHandler(webapp.RequestHandler):
    def render(self, tmplname, context, mimetype='text/html'):
        self.response.headers['Content-Type'] = mimetype
        self.response.out.write(render(self.request, tmplname, context))

class MainPage(JinjaRequestHandler):
    def get(self):
        user = users.get_current_user()
        context = dict(user=user)
        context['updates'] = get_board_updates()
        if user:
            context['board'] = get_board(self.request.get('board', 'default'))

        self.render("index.html", context)

class BoardPage(JinjaRequestHandler):
    def get(self):
        user = users.get_current_user()
        context = dict(user=user)
        if user:
            context['board'] = get_board(self.request.get('board', 'default'))

        self.render("display.html", context)

class TopicPage(JinjaRequestHandler):
    def get(self):
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
        fullresults = []
        count = 0
        for result in results:
            url = result['webUrl']
            if count < 1:
                entities = getentities.get_entities(url)
            else:
                entities = {}
            fullresults.append(dict(url=url.encode('utf8'),
                                    entities=entities.get('entities'),
                                    categories=entities.get('categories'),
                                    title=result['webTitle'],
                                    author='Guardian',
                               ))
            count += 1
        context['results'] = fullresults
        self.render("topic.html", context)

class UrlPage(JinjaRequestHandler):
    def get(self):
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
        self.render("url.html", context)

class RefPage(JinjaRequestHandler):
    def get(self):
        ref = self.request.get('ref', '')
        context = dict(ref=ref,
                       name=self.request.get('name', None),
                       refs=getentities.get_entity_references(ref))
        self.render("ref.html", context)

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

class DelResourcePage(JinjaRequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            return
        url = self.request.get('url')
        board = self.request.get('board')
        next = self.request.get('next')

        if not url or not board:
            return

        del_board_item(user, board, url)

        self.redirect(next)

class AddResourcePage(JinjaRequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return

        context = dict(user=user)
        self.render("add_res.html", context)

    def post(self):
        user = users.get_current_user()
        if not user:
            return

        url = self.request.get('url')
        title = self.request.get('title')
        source = self.request.get('source')
        content = self.request.get('content')
        board = self.request.get('board')
        if not board:
            board = 'default'

        add_board_item(user, board, url, title, source, content)

        fmt = self.request.get('fmt')
        if fmt == 'json':
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps({}))
        else:
            self.redirect('/')

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/board', BoardPage),
                                      ('/topic', TopicPage),
                                      ('/url', UrlPage),
                                      ('/ref', RefPage),
                                      ('/entities', EntitiesPage),
                                      ('/entity', EntityPage),
                                      ('/add_res', AddResourcePage),
                                      ('/del_res', DelResourcePage),
                                      ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
