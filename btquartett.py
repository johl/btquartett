# -*- coding: utf-8 -*-
import requests, re, json
import pystache as mustache
from urllib import quote
# Please stop the UTF-8-related whining, Python.
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def getlabel(itemid):
# Get the label of a property
    r = requests.get("http://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=%s&sites=dewiki&languages=en&props=labels" % itemid)
    return r.json()['entities'][itemid]['labels']['en']['value']

def search(label):
# Search for a Wikidata item by name
    l = quote(label.encode('utf8'), "")
    r = requests.get("http://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&search=%s&language=de&type=item" % l)
    return r.json()['search']

def getimages(names):
# Get the URL on Wikimedia Commons for the image of a politician's name.
# This is surprisingly complicated 
    print "Getting images..."
    images = {}
    for name in names:
        print name
        images[name] = {}
        n = re.sub('^(Prof\. )?Dr\.( Dr\.)*([a-z. ])*', '', name)
        wikidata = search(n)
        if wikidata == []:
            next
        else:
            qid = wikidata[0]['id']
            r = requests.get("http://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=%s&sites=dewiki&languages=de" % qid)
            if 'claims' in r.json()['entities'][qid]:
                claims = r.json()['entities'][qid]['claims']
                if not 'image' in [getlabel(x) for x in claims.keys()]:
                    next
                else:
                    for key in claims.keys():
                        if getlabel(key) == 'image':
                            file = 'File:' + claims[key][0]['mainsnak']['datavalue']['value']
                            r = requests.get("https://commons.wikimedia.org/w/api.php?action=query&titles=%s&prop=imageinfo&iiprop=url&format=json" % file) 
                            pagenumber = r.json()['query']['pages'].keys()[0]
                            page = r.json()['query']['pages'][pagenumber]
                            image = page['imageinfo'][0]['url']
                            images[name]['image'] = image
    return images

def sumcards(cards):
# Sum it up.
    minimum = [0, 1000, 3500, 7000, 15000, 30000, 50000, 75000, 100000, 150000, 250000]
    maximum = [1000, 3500, 7000, 15000, 30000, 50000, 75000, 100000, 150000, 250000, 500000]
    for n in nebeneinkuenfte:
        cards[n['name']].setdefault('fraktion', n['party'])
        if n['periodical'] in ('einmalig', 'monatlich', u'jährlich'):
            if not n['periodical'] + '-min' in cards[n['name']]:
                cards[n['name']].setdefault(n['periodical'] + '-min', minimum[n['level']])
                cards[n['name']].setdefault(n['periodical'] + '-max', maximum[n['level']])
            else:
                cards[n['name']][n['periodical'] + '-min'] += minimum[n['level']]
                cards[n['name']][n['periodical'] + '-max'] += maximum[n['level']]
    return cards

def rendercards(cards):
# Render SVG template to file
    print "Rendering cards..."
    with open('quartett.svg') as x: f = x.read()
    for card in cards:
        print card
        template = cards[card]
        template['name'] = card
        for n in ('einmalig-min', 'monatlich-min', u'jährlich-min', 'einmalig-max', 'monatlich-max', u'jährlich-max'):
            if not n in template: 
                template[n] = '–'
            else:
                template[n] = str(template[n]) + ' €'
        for n in ('einmalig-min', 'monatlich-min', u'jährlich-min'):
            if template[n] == '0 €': template[n] = 'unter 1000 €'
        with open("cards/" + card + ".svg", "w") as text_file: text_file.write(mustache.render(f, template))

#r = requests.get("http://apps.opendatacity.de/nebeneinkuenfte-recherche/assets/data/nebeneinkuenfte.json")
#nebeneinkuenfte = r.json()
with open("nebeneinkuenfte.json") as json_file: nebeneinkuenfte = json.load(json_file)
names = list(set([x['name'] for x in nebeneinkuenfte]))
cards = sumcards(getimages(names))
rendercards(cards)
