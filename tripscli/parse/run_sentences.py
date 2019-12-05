from tripsweb.query import wsd
from tripsweb.query import InputTag
import json, soul
#import sys, os, 

from collections import namedtuple
from pytrips.ontology import get_ontology as ont

EXCLUDE = ["wordnet", "gold"]
TripsOptions = namedtuple("TripsConnection", "tmp,url,sensetags,hinting,sense_pruning,pos_include,as_xml".split(","))

def clean_word(word):
    return word.replace(" ", "-")

def nbest(senses, n=3):
    return {a: b for a, b in sorted(list(senses.items()), key = lambda x: -x[1])[:n]}

def collated(senses, n=3, r=0.5):
    res = sorted(list(senses.items()), key = lambda x: -x[1])[:n]
    i = 1
    k = prob_range(1/n, r)
    out = {}
    for s, v in res:
        out[s] = i
        i = i - k
    return out

def cutoff(senses, cut=0.5):
    if not senses:
        return {}
    max_val = max(senses.values())
    if max_val == 0:
        return {}
    return {s: prob_range(v, 0.2) for s, v in senses.items() if v/max_val > cut}

def light_cutoff(senses, max_num=5, cut=0.5):
    if len(senses) > max_num:
        return cutoff(senses, cut=cut)
    return collated(senses, n=1, r=0)

def prob_range(v, r):
    return v * r + 1 - r

def abstracted(senses, n=3, r=0.5):
    senses = collated(senses, n, r)
    return {ont()[s].parent.name: v for s, v in senses.items()}


MOD = {"none": lambda x: x,
       "nbest": nbest,
       "best": lambda x: nbest(x, 1),
       "collated": collated,
       "best1": lambda x: collated(x, n=1, r=0),
       "best3": lambda x: collated(x, n=1, r=0),
       "abstracted": abstracted,
       "cutoff": cutoff,
       "lightcutoff": light_cutoff
    }

modifier_names = list(MOD.keys())

def _prefix(name, pref="ont::"):
    name = name.lower()
    if not name.startswith(pref):
        name = pref + name
    return name

def parse_sentence(entry, options, debug):
    cleaned_tags = []
    exclude = [e for e in EXCLUDE if e != options.sensetags]
    #clean the tags to prepare construction of InputTag items
    for i in entry["input_tags"]:
        i['lex'] = clean_word(i['lex'])
        if options.pos_include and "pos" in i and i["pos"].lower() not in options.pos_include:
            continue
        if not options.sensetags == "gold" and "senses" in i:
            i["senses"] = MOD[options.sense_pruning](i["senses"])
            i["senses"] = {k: prob_range(v, 0.2) for k, v in i["senses"].items()}
        cleaned_tags.append({k: v for k, v in i.items() if k not in exclude})

    with open(options.tmp, 'w') as tmp:
        if options.hinting == "prog" or options.hinting == "both":
            json.dump(cleaned_tags, tmp)
        else:
            json.dump([], tmp)
    if options.hinting == "pre" or options.hinting == "both":
        if options.sensetags == "gold":
            tags = [InputTag(
                x['lex'], 
                x['start'], 
                x['end'], 
                " ".join(x.get('lftype', [])), 
                1.0,
                x.get('penn-pos', ""), 
                ) for x in entry['input_tags'] if 'lftype' in x or 'penn-pos' in x]
        else:
            tags = [
                    [
                        InputTag(
                            word['lex'], 
                            word['start'], 
                            word['end'], 
                            sense, 
                            prob_range(prob, 0.01),
                            word.get("penn-pos", "")
                        ) 
                        for sense, prob in word['senses'].items()
                    ] for word in cleaned_tags if 'senses' in word
            ]
            # add in the penn-pos without lftypes
            tags2 = [InputTag(
                            word['lex'], 
                            word['start'], 
                            word['end'], 
                            "", 
                            1,
                            word["penn-pos"],
                            "POS"
                        ) for word in cleaned_tags if 'penn-pos' in word]
            tags = sum(tags, []) + tags2
    else:
        tags = []
    #print(entry["sentence"], [str(t) for t in tags])
    res = wsd(entry["sentence"], tags, url=options.url, as_xml=options.as_xml, debug=debug)
    if not options.as_xml:
        res["sentence"] = entry["sentence"]
    return res
