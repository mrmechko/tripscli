from nltk.corpus import stopwords
from it.si3p.supwsd.api import SupWSD
from it.si3p.supwsd.config import Model, Language
from pytrips.ontology import get_ontology as ont
from collections import defaultdict as ddict
import soul
from tqdm import tqdm

from ratelimit import limits, sleep_and_retry


stop = stopwords.words("english")
MODEL = Model.SEMCOR_OMSTI_ONESEC_WORDNET

def distribution(val):
    "sum, max, ranked"
    def _fn(tps):
        if not tps:
            return {}
        if val == "sum":
            return {k: v/len(tps) for k,v in tps.items()}
        if val == "max":
            max_elt, p = max(tps.items(), key=lambda x: x[1])
            return {max_elt: p}
        return {} 
    return lambda x: nmlz(_fn(x))

def nmlz(val):
    f = sum(val.values())
    if f == 0:
        return val
    return {x: y/f for x, y in val.items()}

def share(val):
    def _fn(senses, prob):
        if not senses:
            return {}
        senses = list(senses)
        if val == "uniform":
            return {s: prob/len(senses) for s in senses}
        elif val == "first":
            return {senses[0]: prob}
        elif val == "clone":
            return {s: prob for s in senses}
        return {}
    return _fn

def sep_if_not_stop(word):
    if word in stop:
        return word
    return SupWSD.SENSE_TAG+word+SupWSD.SENSE_TAG

def nth_non_stop(words, n, i=0):
    if not words or n == 0:
        return i
    if words[0] in stop:
        return nth_non_stop(words[1:], n, i+1)
    else:
        return nth_non_stop(words[1:], n-1, i+1)

@sleep_and_retry
@limits(calls=2000, period=3600)
def run_sentence(words, api, get_distribution, taken=None):
    if not taken:
        taken = []
    sep = SupWSD.SENSE_TAG
    max_tags = min(8, (SupWSD.MAX_PAYLOAD - sum([len(w) + 1 for w in words]))//(2*len(sep)))

    t_index = nth_non_stop(words, len(taken))

    untagged1 = " ".join(words[:t_index])
    tagged = " ".join([sep_if_not_stop(x) for x in words[t_index:t_index+max_tags]])
    untagged2 = " ".join(words[t_index+max_tags:])
    sentence = (untagged1 + " " + tagged + " " + untagged2).strip()

    taken += api.disambiguate(sentence, Language.EN, MODEL, get_distribution)
    if len(taken) < len([x for x in words if x not in stop]):
        return run_sentence(words, api, get_distribution, taken)
    return taken


def infer_senses(tags, share_val, dist_val):
    share_fn = share(share_val)
    to_distribution = distribution(dist_val)
    for word in tags:
        if 'wordnet' in word:
            result = word["wordnet"]
            tps = ddict(lambda: 0)
            for key, prob in result.items():
                res = share_fn(ont().get_wordnet(key), prob)
                for k,v in res.items():
                    tps[k] += v
            word["senses"] = {k.name: v for k, v in to_distribution(tps).items()}
    return tags

def sup_sentence(sentence, api, share_val="first", dist_val="sum", get_distribution=True, forced_bracketing=True):
    text = sentence["sentence"]
    tags = [t for t in sentence["input_tags"] if text[t["start"]:t["end"]].isalpha()]
    if not "wordnet" in sentence:
        if forced_bracketing:
            sep = SupWSD.SENSE_TAG
            payload = [text[t["start"]:t["end"]] for t in sorted(tags, key=lambda x: x["end"])]
            wsd = run_sentence(payload, api, get_distribution)
            for word, result in zip([x for x in tags if x["lex"] not in stop], wsd):
                if not result.miss():
                    word["wordnet"] = {sense.id: sense.probability for sense in result.senses}
        else:
            raw_align(sentence, api)
        sentence["wordnet"] = True
    
    infer_senses(tags, share_val, dist_val)
    return sentence


def tag_document(struct, api, share, comb, data_type="plain", forced_bracketing=True):
    api = SupWSD(api)
    if data_type == "plain":
        struct = [sup_sentence(x, api, share, comb, get_distribution=True, forced_bracketing=forced_bracketing) for x in tqdm(struct)]
    elif data_type == "story":
        struct["sentences"] = [sup_sentence(x, api, share, comb, get_distribution=True, forced_bracketing=forced_bracketing) for x in struct["sentences"]]
    return struct

@sleep_and_retry
@limits(calls=2000, period=3600)
def tag_text(text, api):
    api = SupWSD(api)
    result = api.disambiguate(text, Language.EN, MODEL, True)
    data = []
    index = 0
    for r in result:
        token = str(r.token)
        start = text.find(token, index)
        end = start + len(token)
        if start >= index:
            index = end
        if r.sense().id != "U":
            distr = {str(x): x.probability for x in r.senses}
            data.append(dict(lex=token, wordnet=distr, start=start, end=end))
        else:
            data.append(dict(lex=token, start=start, end=end))
    return data

def raw_align(struct, api):
    text = struct["sentence"]
    wsd = tag_text(text, api)
    input_tags = struct["input_tags"]
    res_tags = []
    unpaired_wsd = []
    unpaired_input_tags = list(range(len(input_tags)))
    # case 1. they have the same number of tokens
    for ind_w, w in enumerate(wsd):
        added = False
        for ind_i, i in enumerate(input_tags):
            if ind_i not in unpaired_input_tags:
                continue
            if w["lex"] == i["lex"] and w["start"] == i["start"] and w["end"] == i["end"]:
                unpaired_input_tags.remove(ind_i)
                if "wordnet" in w:
                    i["wordnet"] = w["wordnet"]
                res_tags.append(i)
                added = True
        if not added:
            unpaired_wsd.append(ind_w)
    return struct

