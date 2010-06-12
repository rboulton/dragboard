#!/usr/bin/env python

import urllib, urllib2
try:
    from simplejson import json
except ImportError:
    try:
        import django.utils.simplejson as json
    except ImportError:
        import json


def getname(item):
    try:
        return item['canonicalName']['$']
    except KeyError: pass
    try:
        return item['name']['$']
    except KeyError: pass
    return ''

def gethref(item):
    try:
        return item['@href']
    except KeyError: pass
    return ''

def mklist(items):
    if isinstance(items, dict):
        return [items]
    return items

def get_entities_(url):
    data = urllib2.urlopen('http://api.evri.com/v1/media/entities.json?uri=' + urllib.quote(url)).read()
    data = json.loads(data)
    graph = data['evriThing']['graph']
    def getfacet(item):
        try:
            return item['facets']['facet']['$']
        except KeyError: pass
        return ''

    try:
        category_list=mklist(graph['categories']['category'])
        categories=[item['$'] for item in category_list]
    except KeyError:
        categories=[]

    try:
        entity_list = mklist(graph['entities']['entity'])
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
    data = urllib2.urlopen('http://api.evri.com/v1/media/related.json?includeTopEntities=true&entityURI=' + urllib.quote(url)).read()
    data = json.loads(data)
    data = data['evriThing']['mediaResult']['articleList']['article']
    def get_path(article):
        link = article.get('link', {})
        try:
            return 'http://%s%s' % (link['@hostName'], link['@path'])
        except KeyError:
            return ''

    def getentities(article):
        try:
            entities = mklist(article['topEntities']['entity'])
        except KeyError: return []
        return [dict(
                     name=getname(entity),
                     ref=gethref(entity),
                    ) for entity in entities]
        
    return [dict(
                 author=article.get('author', {}).get('$', ''),
                 content=article.get('content', {}).get('$', ''),
                 title=article.get('title', {}).get('$', ''),
                 url=get_path(article),
                 entities=getentities(article),
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
    #pprint.pprint(get_entity_references(sys.argv[1]))
