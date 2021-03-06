import json
from collections import namedtuple

import xml.etree.ElementTree as et

# @{"+_ns["rdf"]+"}ID, {"+_ns["LF"]+"}indicator, {"+_ns["LF"]+"}type, {"+_ns["role"]+"}*, {"+_ns["LF"]+"}start, {"+_ns["LF"]+"}end
def none_or_text(x):
    if x is not None:
        return x.text
    return x

def none_or_int(x):
    if x is not None:
        return int(x.text)
    return -1

_ns = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "role": "http://www.cs.rochester.edu/research/trips/role#",
    "LF": "http://www.cs.rochester.edu/research/trips/LF#"
}

def ns(n,v):
    return "{%s}%s" % (_ns[n], v)

for pre, uri in _ns.items():
    et.register_namespace(pre, uri)

class ParseObject(object):
    def __init__(self, value):
        self.value = value
        self.alts = []
        if self.value.find("alt-hyps"):
            self.alts = [ParseObject.instance(x) for x in self.value.find("alt-hyps")]

    @staticmethod
    def instance(element):
        if element.tag == "failed-to-parse":
            return FailedToParse(element)
        elif element.tag == "utt":
            return Utterance(element)
        elif element.tag == "compound-communication-act":
            return CompoundCommunicationAct(element)
        else:
            return FailedToParse(element)

    def alternative(self, i):
        if self.alts and i < len(self.alts):
            return self.alts[i]
        return None

    def as_json(self):
        parse = []
        if type(self) is Utterance:
            parse = [self._as_json()]
            alts = [[a._as_json()] for a in self.alts]
        elif type(self) is CompoundCommunicationAct:
            parse = self._as_json()
            alts = [a._as_json() for a in self.alts]
        return {"parse": parse, "alternatives": alts}

class Utterance(ParseObject):
    def _as_json(self):
        terms = self.value.find("terms")
        if not terms:
            return {}
        rdf = terms.find(ns("rdf", "RDF"))
        desc = rdf.findall(ns("rdf", "Description"))
        root = terms.attrib.get("root")
        result = {n.attrib.get(ns("rdf","ID")): {
            "id": n.attrib.get(ns("rdf", "ID")),
            "indicator": none_or_text(n.find(ns("LF","indicator"))),
            "type": none_or_text(n.find(ns("LF", "type"))),
            "word": none_or_text(n.find(ns("LF", "word"))),
            "roles":get_roles(n),
            "start": none_or_int(n.find(ns("LF", "start"))),
            "end": none_or_int(n.find(ns("LF", "end")))
            } for n in desc}
        result["root"] = root
        return result

class CompoundCommunicationAct(ParseObject):
    def _as_json(self):
        return [Utterance(u)._as_json() for u in self.value if u.find("terms")]

class FailedToParse(ParseObject):
    def _as_json(self):
        return []

def find_utts(node):
    if not node:
        return [ParseObject({})]
    # Untested <- if utts don't get properly parsed this is probably the problem
    terms = []
    for v in node:
        if v.tag == "utt":
            terms += [Utterance(v)]
        elif v.tag == "compound-communication-act":
            terms += [CompoundCommunicationAct(v)]
    if terms:
        return terms
    return [FailedToParse(v)]

def find_terms(stream):
    root = et.fromstring(stream)
    sentence = root.attrib.get("input")
    inputtags = root.attrib.get("input-tags", [])
    debug = root.find("debug")
    return find_utts(root), inputtags, debug, sentence


def val_or_ref(y):
    label = y.tag.split("}")[-1]
    link = y.attrib.get("{"+_ns["rdf"]+"}resource", None)
    if link:
        return label, link
    return label, y.text

def get_roles(term):
    return dict([val_or_ref(n) for n in term if n.tag.startswith("{"+_ns["role"]+"}")])

def _flat(x):
    if isinstance(x, list):
        return sum([_flat(y) for y in x], [])
    else:
        return [x]

def to_json(stream, debug=False):
    terms, inputtags, debug, sentence = find_terms(stream)
    res = [dict(t.as_json(), sentence=sentence) for t in terms]
    if debug:
        return {"inputtags": inputtags, "debug": debug.split("\n"), "sentence": sentence, **res[0]}
    return res
