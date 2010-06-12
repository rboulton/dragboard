#!/usr/bin/env python

import urllib, urllib2
try:
    from simplejson import json
except ImportError:
    try:
        import django.utils.simplejson as json
    except ImportError:
        import json



def get_entities_(url):
    data = urllib2.urlopen('http://api.evri.com/v1/media/entities.json?uri=' + urllib.quote(url)).read()
    data = json.loads(data)
    graph = data['evriThing']['graph']
    def getname(item):
        try:
            return item['canonicalName']['$']
        except KeyError: pass
        try:
            return item['name']['$']
        except KeyError: pass
        return ''
    def getfacet(item):
        try:
            return item['facets']['facet']['$']
        except KeyError: pass
        return ''
    def gethref(item):
        try:
            return item['@href']
        except KeyError: pass
        return ''

    try:
        category_list=graph['categories']['category']
        if isinstance(category_list, dict):
            category_list = [category_list]
        categories=[item['$'] for item in category_list]
    except KeyError:
        categories=[]

    try:
        entity_list = graph['entities']['entity']
        if isinstance(entity_list, dict):
            entity_list = [entity_list]
    except KeyError:
        entity_list = []

    return dict(
        categories=categories,
        entities=[dict(
                       name=getname(item),
                       facet=getfacet(item),
                       ref=gethref(item)
                      )
                  for item in entity_list],
    )

def get_entities(url):
    try:
        return get_entities_(url)
    except KeyError:
        return dict(category='', entities=[])

def get_entity_references_(url):
    data = urllib2.urlopen('http://api.evri.com/v1/media/related.json?entityURI=' + urllib.quote(url)).read()
    data = json.loads(data)
    data = data['evriThing']['mediaResult']['articleList']['article']
    def get_path(article):
        link = article.get('link', {})
        try:
            return 'http://%s%s' % (link['@hostName'], link['@path'])
        except KeyError:
            return ''
    return [dict(
                 author=article.get('author', {}).get('$', ''),
                 content=article.get('content', {}).get('$', ''),
                 url=get_path(article),
            ) for article in data]

def get_entity_references(url):
    try:
        return get_entity_references_(url)
    except KeyError:
        return []

if __name__ == '__main__':
    import sys
    import pprint
    pprint.pprint(get_entities(sys.argv[1]))
    pprint.pprint(get_entity_references(sys.argv[1]))
