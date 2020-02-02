import json
import urllib.parse as uparse
import urllib.request as urequest

from .read import to_json

default_parameters = {
     "component": "parser",
     "semantic-skeleton-scoring": True,
     "no-sense-words": "",
     "senses-only-for-penn-poss": "",
     "tag-type": ["default"],
     "number-parses-desired": 20,
     "split-mode": "split-sentences"
}

default_step = "http://trips.ihmc.us/parser/cgi/step"

def query(text, parameters=default_parameters, input_tags=[], url=default_step, output="json", tag_combination="or", debug=True):
    """
    parameters are:
        component: parser|texttager
        semantic-skeleton-scoring: True|False
        no-sense-words: comma separated list of words to not lookup senses for
        senses-only-for-penn-poss: csl of penn treebank pos tags for TextTagger to lookup
        tag-type: (or default) / list of tag types to use
        number-parses-desired: 10 / number of parses to return
        split-mode: split-sentences|split-clauses

    output: xml|json
    url: http://trips.ihmc.us/parser/cgi/step
    """
    parameters = {p: q for p, q in parameters.items()}
    parameters["input"] = text
    ttype = parameters.get("tag-type", ["default"])

    if input_tags:
        ttype = ttype + ["input"]
        parameters["input-tags"] = "(\n\t%s\n)" % "\n\t".join([str(i) for i in input_tags])

    parameters = {p: q for p, q in parameters.items() if q}

    if ttype:
        parameters["tag-type"] = "(%s %s)" % (tag_combination, " ".join(ttype))

    return parse(parameters, url=url, output=output, debug=debug)


def parse(parameters, url=default_step, output="json", debug=True):
    data = uparse.urlencode(parameters)
    data = data.encode('ascii')

    with urequest.urlopen(url, data) as response:
        result = response.read().decode("utf-8")
        if output == "json":
            result = to_json(result)
            if not debug:
                result = result[0]#{"parse": result}
            result["sentence"] = parameters["input"]
            return result
        return result

class TripsParser:
    def __init__(self, parameters=default_parameters, url=default_step, output="json", debug=True):
        self.url = url
        self.output = output
        self.parameters = parameters
        self.debug=debug

    def set_parameters(self, parameters):
        self.parameters = parameters

    def set_parameter(self, key, value):
        self.parameters[key] = value

    def query(self, input_, plain=False):
        tags = []
        sentence = ""

        if type(input_) is dict:
            tags = read_word_tags(input_.get("input_tags", []))
            tags += read_cats(input_.get("spans", []))
            sentence = input_["sentence"]
        if type(input_) is str:
            sentence = input_

        if plain:
            tags = []

        return query(
                sentence, 
                parameters=self.parameters, 
                input_tags=tags, 
                url=self.url, 
                output=self.output,
                debug=self.debug
                )
    
    def query_json(self, fname, plain=False):
        with open(fname) as data:
            sentences = json.load(data)
            if type(sentences) is list:
                return [self.query(s, plain=plain) for s in sentences]
            else:
                return [self.query(sentences, plain)]
    

class InputTag:
    def __init__(self, lex, start, end, lftype=None, pos=None, cat=None, score=1.0, prefix="SENSE", hinter="SEM-HINT"):
        """
        prefix is one of "SENSE|POS|PHRASE"
        """
        self.lex = lex
        self.start = start
        self.end = end
        self.lftype = self._ensure_prefix(lftype)
        self.pos = pos 
        self.cat = cat
        self.score = score
        self.prefix = prefix
        self.hinter = hinter

    def _ensure_prefix(self, t):
        if not t:
            return t
        if type(t) is list:
            return " ".join([self._ensure_prefix(x) for x in t])
        elif " " in t:
            return self._ensure_prefix(t.split())
        if not t.lower().startswith("ont::"):
            t = "ont::" + t
        return t

    def __str__(self):
        lftype = ""
        postag = ""
        pencat = ""
        lex = ":LEX"
        if self.prefix in ["PHRASE", "CLAUSE"]:
            lex = ":TEXT"
        if self.lftype and self.prefix == "SENSE":
            lftype = ":LFTYPE ({}) ".format(self.lftype)
        if self.pos:
            postag = ":penn-pos ({}) ".format(self.pos)
        if self.cat:
            pencat = ":penn-cat ({}) ".format(self.cat)

        return '(%s %s "%s" :START %s :END %s %s%s%s :SCORE %f)' % (self.prefix, lex, self.lex, str(self.start), str(self.end), lftype, postag, pencat, self.score)

def read_tag(tag, hinter="SEM-HINT"):
    itags = []
    if "penn-pos" in tag:
        itags.append(
                InputTag(
                    lex=tag["lex"],
                    start=tag["start"],
                    end=tag["end"],
                    pos=tag["penn-pos"],
                    score=tag.get("score", 1.0),
                    prefix="POS",
                    hinter=hinter))
    elif "tag" in tag: # HAX!
       itags.append(
                InputTag(
                    lex=tag["lex"],
                    start=tag["start"],
                    end=tag["end"],
                    pos=tag["tag"],
                    score=tag.get("score", 1.0),
                    prefix="POS",
                    hinter=hinter))
    if "lftype" in tag:
        itags.append(
                InputTag(
                    lex=tag["lex"],
                    start=tag["start"],
                    end=tag["end"],
                    pos=tag["penn-pos"], # if you want to give sense without penn, duplicate the tag
                    lftype=tag["lftype"],
                    score=tag.get(score, 1.0),
                    prefix="SENSE",
                    hinter=hinter))
    return itags

def read_word_tags(input_tags):
    return sum([read_tag(tag) for tag in input_tags], [])

def read_span(span):
    return [InputTag(lex=span["text"], start=span["start"], end=span["end"], cat=span["penn-cat"], score=0, prefix="PHRASE")]

def read_cats(spans):
    return sum([read_span(span) for span in spans if "penn-cat" in span], [])

