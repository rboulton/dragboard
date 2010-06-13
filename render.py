import datetime
import jinja2
import os
import urllib
import wsgiref.util
from google.appengine.api import users

def guess_autoescape(template_name):
    """Use autoescape for all the templates we've got so far.

    """
    return True

tmpldir = os.path.join(os.path.dirname(__file__), 'templates')
loader = jinja2.FileSystemLoader(tmpldir, encoding='utf-8')
extensions = ['jinja2.ext.with_']
myenv = jinja2.Environment(loader=loader, extensions=extensions,
                           trim_blocks=True, autoescape=True,
                           line_statement_prefix="#")
myenv.filters['urlencode'] = urllib.quote

def timeagoformat(value):
    format = '%H:%M / %d-%m-%Y'
    delta = datetime.datetime.now() - value
    if delta.days > 0:
        return "%d days ago" % delta.days
    if delta.seconds >= 3600:
        return "%d hours ago" % (delta.seconds // 3600)
    if delta.seconds >= 60:
        return "%d minutes ago" % (delta.seconds // 60)
    return "%d seconds ago" % delta.seconds
myenv.filters['timeagoformat'] = timeagoformat

def render(request, template_name, context={}):
    """Render the template named in `template`.

    - `context` may be used to provide variables to the template.

    """
    # Add any universal bits to the context
    user = users.get_current_user()
    newcontext = dict(user=user)
    if not user:
        newcontext['loginurl'] = users.create_login_url(request.uri)

    newcontext['thisurl'] = wsgiref.util.request_uri(request.environ)

    newcontext.update(context)
    template = myenv.get_template(template_name)
    return template.render(newcontext)
