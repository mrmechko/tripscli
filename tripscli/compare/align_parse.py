from soul.files import ls
from pytrips.ontology import get_ontology as ont
import pprint
import json, os

from nltk.stem import SnowballStemmer
from collections import namedtuple, Counter

AlignConfig = namedtuple("AlignConfig", ["exact", "word", "multi"])

snowball_ = SnowballStemmer("english")
snowball = lambda x: snowball_.stem(x)

SpanT = namedtuple("SpanT", ["start", "end"])

trace = 0
print_ = lambda *x: None


def stringify(element):
    if isinstance(element, TagT):
        if element.gold == "__nota__":
            prefix = "-"
        else:
            prefix = "+"
        return "{}{}[{}]{}".format(prefix, stringify(element.word), ", ".join(element.lftype), stringify(element.span))
    elif isinstance(element, NodeT):
        return "{}[{}]{}".format(stringify(element.word), element.type, stringify(element.span))
    elif isinstance(element, SpanT):
        return "({},{})".format(str(element.start), str(element.end))
    elif isinstance(element, WordT):
        if element.word != "__NO_WORD__":
            return element.word
        return element.lex
    elif isinstance(element, MatchT):
        return "{}:      {}".format(stringify(element.gold), ", ".join([stringify(x) for x in element.candidates]))
    elif isinstance(element, AlignT):
        return "{}:      {}".format(stringify(element.tag), stringify(element.node))
    elif isinstance(element, list):
        return [stringify(x) for x in element]

    return str(element)

def intersect(span1, span2):
    if span1.start > span2.start:
        return intersect(span2, span1)
    return span1.start <= span2.start <= span1.end

def substring(string, span):
    return string[span.start:span.end]

WordT = namedtuple("WordT", ["word", "stemmed", "lex"])

SentenceT = namedtuple("SentenceT", ["sentence", "tags"])
TagT = namedtuple("TagT", ["word", "lftype", "gold", "span", "sup", "sup_trips", "sid"])

ParseT = namedtuple("ParseT", ["utterances", "sentence"])
UtteranceT = namedtuple("UtteranceT", ["nodes", "root"])
NodeT = namedtuple("NodeT", ["id", "indicator", "type", "word", "roles", "span"])

def load_tag(tag_json, sentence):
    start = tag_json["start"]
    end = tag_json["end"]
    span = SpanT(start, end)

    word = _lower(substring(sentence, span))
    lex = _lower(tag_json["lex"])
    stemmed = _lower(snowball(word))
    
    wordt = WordT(word, stemmed, lex)

    lftype = tag_json["lftype"]
    for i in range(len(lftype)):
        if lftype[i].startswith("ont::"):
            lftype[i] = lftype[i][5:]
    gold = tag_json["gold"]
    if "__nota__" in gold:
        gold = "__nota__"
    sup = tag_json.get("wordnet", [])
    sup_trips = tag_json.get("senses", [])
    sid = tag_json.get("sid", "__none__")

    return TagT(wordt, lftype, gold, span, sup, sup_trips, sid)

SubT = namedtuple("SubT", "string sub ldelimiter rdelimiter")
_substitutions = [
        SubT("punc-period", ".", "-", "-")
    ]

def _subs(x):
    for s in _substitutions:
        while s.string in x:
            index = x.index(s.string)
            offs = len(s.string)
            if index + offs < len(x) and x[index + offs] == s.rdelimiter:
                offs += 1
            if index > 0 and x[index - 1] == s.ldelimiter:
                index = index - 1
                offs += 1
            x = x[:index] + s.sub + x[index+offs:]
    return x

def _lower(x, subs=True):
    if type(x) is str:
        if subs:
            return _subs(x.lower())
        else:
            return x.lower()
    if type(x) is list:
        return [_lower(a) for a in x]
    else:
        return x

def load_sentence(sentence_json):
    sentence = sentence_json["sentence"]
    tags = [load_tag(t, sentence) for t in sentence_json["input_tags"]]

    return SentenceT(sentence, tags)

def load_node(node_json):
    id_ = _lower(node_json["id"])
    indicator = _lower(node_json["indicator"])
    tpe = _lower(node_json["type"])

    word = node_json["word"]
    if not word:
        word = "__NO_WORD__"
        stemmed = "__NO_WORD__"
    else:
        word = _lower(word)
        stemmed = _lower(snowball(word))
    lex = _lower(node_json["roles"].get("LEX", stemmed))

    wordt = WordT(word, stemmed, lex)

    start = node_json["start"]
    end = node_json["end"]
    roles = {_lower(k): _lower(v) for k, v in node_json["roles"].items()}

    return NodeT(id_, indicator, tpe, wordt, roles, SpanT(start, end))

def load_utterance(utt_json):
    if type(utt_json) is list:
        return [load_utterance(dct) for dct in utt_json]
    nodes = {_lower(k): load_node(v) for k, v in utt_json.items() if k != "root" and not _lower(v["type"]).startswith("sa_")}
    root = utt_json["root"]

    return UtteranceT(nodes, root)

def flat(l):
    if type(l) is not list:
        return [l]
    else:
        return sum([flat(x) for x in l], [])

def load_parse(parse_json):
    utterances = [load_utterance(dct) for dct in parse_json["parse"]]
    sentence = parse_json["sentence"]

    return ParseT(utterances, sentence)

def word_set(word):
    return set([word.word, word.stemmed, word.lex])

def word_match(word1, word2, exact=False):
    if exact:
        return word1.word == word2.word
    w1 = word_set(word1)
    w2 = word_set(word2)
    if trace > 5:
        print("\t", "[{}]".format(", ".join(w1)), "->", "[{}]".format(", ".join(w1)))
    if w1.intersection(w2):
        if trace > 4:
            print("+", stringify(word1), "->", stringify(word2))
        return True
    if trace > 4:
        print("-", stringify(word1), "->", stringify(word2))
    return False

def exact_match(tag, node):
    return intersect(tag.span, node.span) and word_match(tag.word, node.word)


MatchT = namedtuple("MatchT", ["gold", "candidates"])
def choose_matches(matches):
    return [m for m in matches if m.gold.gold != "__nota__" and m.candidates]

AlignT = namedtuple("AlignT", ["tag", "node", "remainder", "use_all"])
def alignt_to_dict(alignt):
    return {
            "lexical": {
                "gold": {
                    "word": alignt.tag.word.word,
                    "lex": alignt.tag.word.lex,
                    "stemmed": alignt.tag.word.stemmed,
                    "span": [alignt.tag.span.start, alignt.tag.span.end]
                },
                "trips":{
                    "word": alignt.tag.word.word,
                    "lex": alignt.tag.word.lex,
                    "stemmed": alignt.tag.word.stemmed,
                    "span": [alignt.node.span.start, alignt.node.span.end]
                }
            },
        "gold": alignt.tag.lftype,
        "wordnet": alignt.tag.gold,
        "trips": alignt.node.type,
        "sup": alignt.tag.sup,
        "sup_trips": alignt.tag.sup_trips,
        "sid": alignt.tag.sid
    }

def align_match(match, used=[], use_all=False, exact_match_only=False, referential_sem_allowed=True):
    # discard referential-sem
    candidates = [c for c in match.candidates if c.type != "referential-sem" and c not in used]

    # keep referential sem for last effort
    refsem = [c for c in match.candidates if c.type == "referential-sem" and c not in used]
    if referential_sem_allowed:
        candidates += refsem
    
    # prefer exact-match
    exact = [c for c in candidates if c.type in match.gold.lftype]

    if trace > 4:
        print(stringify(match))

    if exact:
        node = exact[0]
    elif candidates:
        if not exact_match_only:
            node = candidates[0]
    else:
        node = None

    remainder = [c for c in candidates if c != node]
    return AlignT(match.gold, node, remainder, use_all)

ScoreConfig = namedtuple("ScoreConfig", "hierarchy down significant")
def list_accepts(node, values, score=ScoreConfig(-1,0,False)):
    node = ont()[node]
    values = set([ont()[v] for v in values])
    if score.significant:
        values = set([v.significant() for v in values])
        node = node.significant()

    values = set([v for v in values if v])
    if not values and trace > 1:
        print("failed mapping!")
    # bug avoidance:
    down_sig = True
    hierarchy_sig = True
    if score.hierarchy < 0:
        hierarchy_sig = False
    if score.down < 0:
        down_sig = False

    for v in values:
        if v == node:
            return True
        if score.hierarchy != 0 and v.subsumes(node, max_depth=score.hierarchy, significant=hierarchy_sig):
            return True
        if score.down != 0 and node.subsumes(v, max_depth=score.down, significant=down_sig):
            return True
    return False

# alignment strategies
def _exact(exact_matches, word_matches, multi_word_matches, aligned, used, used_tag, nodes, tags):
    exact_matches = choose_matches([MatchT(t, [x for x in nodes if exact_match(t, x)]) for t in tags])
    for x in exact_matches:
        a = align_match(x, used)
        if a.node and a.node not in used:
            used.append(a.node)
            used_tag.append(a.tag)
        aligned.append(a)

    nodes = [n for n in nodes if n not in used]
    tags = [t for t in tags if t not in used_tag]
    return exact_matches, word_matches, multi_word_matches, aligned, used, used_tag, nodes, tags
    
def _word(exact_matches, word_matches, multi_word_matches, aligned, used, used_tag, nodes, tags):
    word_matches = choose_matches(
                [MatchT(t, [x for x in nodes if word_match(x.word, t.word)]) for t in tags]
            )

    for x in word_matches:
        a = align_match(x, used)
        if a.node and a.node not in used:
            used.append(a.node)
            used_tag.append(a.tag)
            aligned.append(a)

    nodes = [n for n in nodes if n not in used]
    tags = [t for t in tags if t not in used_tag]
    return exact_matches, word_matches, multi_word_matches, aligned, used, used_tag, nodes, tags

def _multi(exact_matches, word_matches, multi_word_matches, aligned, used, used_tag, nodes, tags):
    for x in tags:
        candidates = set(x.word.lex.split())
        if len(candidates) < 2:
            continue
        multi_word_matches.append(MatchT(x, [n for n in nodes if word_set(n.word).intersection(candidates)]))
                    
    for x in multi_word_matches:
        if x in used_tag:
            continue
        a = align_match(x, used, use_all=True)
        if a.node and a.node not in used:
            used.append(a.node)
            used_tag.append(a.tag)
            aligned.append(a)

    nodes = [n for n in nodes if n not in used]
    tags = [t for t in tags if t not in used_tag]
    return exact_matches, word_matches, multi_word_matches, aligned, used, used_tag, nodes, tags

def align(sentence, nodes, config=AlignConfig(1,2,3)):
    exact_matches = []
    word_matches = []
    multi_word_matches = []

    aligned = []
    used = []
    used_tag = []

    nodes = [n for n in nodes]
    tags = [t for t in sentence.tags]

    if trace > 2:
        print("searching for:")
        print("\t" + "\n\t".join([stringify(x) for x in tags if x.gold != "__nota__"]))

    match_modes = {"exact": _exact, "word": _word, "multi": _multi}
    modes = list(sorted([c for c in config._fields if config._asdict()[c]], key=lambda x: config._asdict()[x]))
    for s in modes:
        s = match_modes.get(s, lambda x: print("Not found:", x))
        exact_matches, word_matches, multi_word_matches, aligned, used, used_tag, nodes, tags = s(exact_matches, word_matches, multi_word_matches, aligned, used, used_tag, nodes, tags)

    if trace > 1:
        rem_tag = [t for t in tags if t.gold != "__nota__"]
        if rem_tag:
            for t in rem_tag:
                print(stringify(t))
            print("++++++++++++++++++++++++++++")
            for n in nodes:
                print(stringify(n))
            print("----------------------------")
    return aligned, exact_matches, word_matches, multi_word_matches

def score_alignt(alignt, score=ScoreConfig(-1, 0, False)):
    if not alignt.node:
        return False
    if alignt.use_all:
        for r in alignt.remainder:
            res = list_accepts(r.type, alignt.tag.lftype, score)
            if res:
                return True
    return list_accepts(alignt.node.type, alignt.tag.lftype, score)

def align_sentence(sentence, parse, config=AlignConfig(1,2,3), score=ScoreConfig(-1, 0, False)):
    #3. compare elements
    if trace > 1:
        print(sentence.sentence)
    nodes = sum([list(x.nodes.values()) for x in parse.utterances], [])
    if trace > 4:
        print("\np>".join(stringify([n for n in nodes])))
    aligned, exact, words, multi = align(sentence, nodes, config=config)

    taggable = [t for t in sentence.tags if t.gold != "__nota__"]
    tagged = [a for a in aligned if a.tag.gold != "__nota__"]
    tagged_ = [a.tag for a in tagged]
    correct = [t for t in aligned if score_alignt(t, score=score)]
    untagged = [x for x in taggable if x not in tagged_]
    unmatched = [x for x in nodes if not any([x == a.node for a in aligned])]

    if trace > 3:
        for a in untagged:
            print(">>>>", stringify(a))
        print("<<<<<<<<<<<<<<<<<<<<<<")

    json_ = {"alignments": [alignt_to_dict(a) for a in aligned if a.tag.gold != "__nota__"]}
    json_["sentence"] = sentence.sentence

    #print_("--------------------------")
    #print_(sentence.sentence)
    #print_("ALIGNMENTS:")
    #print_("\n".join([stringify(x) for x in aligned]))
    #print_("----------------------untagged")
    #print_("\n".join([stringify(x) for x in untagged]))
    #print_("----------------------unaligned")
    #print_("\n".join([stringify(x) for x in unmatched]))
    #print_("\n\n")
    #
    #print_("correct:", len(correct), "tagged:", len(tagged), "untagged:", len(untagged), "taggable:", len(taggable))
    return (correct, tagged, untagged, taggable, json_)

# word, gold_tags, parser_tag

OutputConfig = namedtuple("OutputConfig", "trace verbose as_json")
def compare_parses(reference, input_file, alignc, scorec, outputc):
    global trace
    global print_
    print(alignc)
    print(scorec)
    print(outputc)
    trace = outputc.trace
    if outputc.verbose:
        print_ = print
        if outputc.as_json:
            print_ = lambda *x: print(*x, file=sys.stderr) # might need to make as_json provide a file
    scores = Counter()
    #1. load key
    key = [load_sentence(j) for j in json.load(open(reference))]
    #2. load parse
    elts = ls(input_file)

    all_sentences_json = []
    incorrect_trips = Counter()
    incorrect_gold = Counter()
    for parse_file in elts:
        try:
            n = int(parse_file.split("_")[-1].split(".")[0])
            if outputc.trace:
                print(">", parse_file)
            parse = load_parse(json.load(open(parse_file)))
            sentence = key[n]
            if outputc.trace and parse.sentence != sentence.sentence:
                print(parse.sentence)
                print(sentence.sentence)
            c, t, u, a, j = align_sentence(sentence, parse, config=alignc, score=scorec)
            j["id"] = n
            j["filename"] = parse_file

            all_sentences_json.append(j)

            incorrect = [s for s in t if s not in c]
            for i in incorrect:
                if trace > 5:
                    print(stringify(i))
                types = i.tag.lftype
                for tp in types:
                    incorrect_gold[tp] += 1
                incorrect_trips[i.node.type] += 1

            scores["correct"] += len(c)
            scores["tagged"] += len(t)
            scores["untagged"] += len(u)
            scores["taggable"] += len(a)
        except Exception as e:
            if trace:
                print(e)
            print_(parse_file, "failed")

    if not scores["tagged"]:
        precision = 0
    else:
        precision = scores["correct"]/scores["tagged"]

    if not scores["taggable"]:
        recall = 0
    else:
        recall = scores["correct"]/scores["taggable"]

    if recall:
        f1 =2*(precision*recall)/(precision+recall) 
    else:
        f1 = 0

    if outputc.as_json:
        print(json.dumps(all_sentences_json, indent=2))
    else:
        total_gold = 0
        correct_gold = 0
        for x in all_sentences_json:
            for w in x["alignments"]:
                if w["gold"]:
                    total_gold += 1
                    for f in w["sup_trips"]:
                        if f in w["gold"]:
                            correct_gold += 1
        print(correct_gold/total_gold)
        print(scores)
        print("Precision:", precision)
        print("Recall   :", recall)
        print("F1       :", f1)
        if trace > 5:
            pprint.pprint([i for i in incorrect_gold.most_common() if i[1] > 1])
            print("------")
            pprint.pprint([i for i in incorrect_trips.most_common() if i[1] > 1])
    

