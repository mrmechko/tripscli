import pandas as pd
from collections import namedtuple
from itertools import takewhile

from pytrips.ontology import get_ontology as ont 
from nltk.corpus import wordnet as wn
from .entry_iterator import simple_it

class OMSTIFile:
    def __init__(self, filename, word_transformer=lambda x: x):
        self.file = map(word_transformer, pd.read_csv(filename).itertuples(index=False, name="Word"))
        #drop the first (empty) sentence
        self.get_sentence_from_iterator()

    def get_sentence_from_iterator(self):
        sentence = takewhile(lambda x: x.sid != "__start__", self.file)
        return list(filter(lambda x: x.word not in ["__start__", "__end__"], sentence))

    def __iter__(self):
        sentence = self.get_sentence_from_iterator()
        while sentence:
            yield sentence
            sentence = self.get_sentence_from_iterator()

def clean(word):
    if word == "``":
        word = '"'
    if "&apos;" in word:
        return word.replace("&apos;", "'")
    return word
    
def get_spans(sentence, add_wn=False):
    spans = []
    start = 0
    for s in sentence:
        rtag = []
        word = clean(s.word)
        if "%" in s.tag:
            lex = wn.lemma_from_key(s.tag.split()[0]).name()
            rtag = ["ont::"+x.name for x in ont().get_wordnet(s.tag.split()[0], max_depth=3)]
        this = {"start": start, "end": start+len(word), "pos": s.pos, "lex": word, "lftype": rtag, "sid": s.sid}
        if add_wn:
            this["gold"] = s.tag.split()
        spans.append(this)
        start = start + len(word) + 1
    return spans 

def read_csv_semcor(fname, add_wn=True, entries=simple_it):
    f = OMSTIFile(fname)
    return ({"sentence": " ".join([clean(x.word) for x in s]), "input_tags" : get_spans(s, add_wn)} for s in entries(f))

