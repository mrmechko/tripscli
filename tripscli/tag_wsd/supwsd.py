from nltk.corpus import stopwords
from it.si3p.supwsd.api import SupWSD
from it.si3p.supwsd.config import Model, Language
from pytrips.ontology import get_ontology as ont
from collections import defaultdict as ddict
import soul

from ratelimit import limits, sleep_and_retry


stop = stopwords.words("english")

#flags.DEFINE_boolean("tag_story", False, "whether the input is a story or just a sentence")
#flags.DEFINE_string("dir", "data", "input file to add sense tags to")
#flags.DEFINE_integer("n", -1, "index of sentence to add tags to. -1 adds to all")
#flags.DEFINE_integer("max", -1, "max number of sentences to tag.  -1 returns all.")
#flags.DEFINE_string("api", "", "API key to use for supwsd")
#flags.DEFINE_string("comb", "sum", "how to combine probabilities when transforming to trips.\
#        options are: sum, max, ranked")
#flags.DEFINE_string("share", "clone", "how to split probability mass when a wn sense returns \
#        multiple ont types.  Options are: uniform, first, clone")


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

    taken += api.disambiguate(sentence, Language.EN, Model.SEMCOR_OMSTI_ONESEC_WORDNET, get_distribution)
    if len(taken) < len([x for x in words if x not in stop]):
        return run_sentence(words, api, get_distribution, taken)
    return taken


def sup_sentence(sentence, api, share_val="first", dist_val="sum", get_distribution=True):
    share_fn = share(share_val)
    to_distribution = distribution(dist_val)
    text = sentence["sentence"]
    tags = [t for t in sentence["input_tags"] if text[t["start"]:t["end"]].isalpha()]
    if not "wordnet" in sentence:
        sep = SupWSD.SENSE_TAG
        payload = [text[t["start"]:t["end"]] for t in sorted(tags, key=lambda x: x["end"])]
        wsd = run_sentence(payload, api, get_distribution)
        for word, result in zip([x for x in tags if x["lex"] not in stop], wsd):
            if not result.miss():
                word["wordnet"] = {sense.id: sense.probability for sense in result.senses}
        sentence["wordnet"] = True
    
    for word in tags:
        if 'wordnet' in word:
            result = word["wordnet"]
            tps = ddict(lambda: 0)
            for key, prob in result.items():
                res = share_fn(ont().get_wordnet(key), prob)
                for k,v in res.items():
                    tps[k] += v
            word["senses"] = {k.name: v for k, v in to_distribution(tps).items()}
    return sentence


def tag_document(struct, api, share, comb, data_type="plain"):
    api = SupWSD(api)
    if data_type == "plain":
        struct = [sup_sentence(x, api, share, comb) for x in struct]
    elif data_type == "story":
        struct["sentences"] = [sup_sentence(x, api, share, comb) for x in struct["sentences"]]
    return struct

#def main(argv):
#    # 'or2333higd'
#    api = FLAGS.api
#    if not FLAGS.api:
#        api = os.environ.get("SUPWSD_API_KEY")
#
#    if not api:
#        print("please add SUPWSD_API_KEY to your environment or supply a --api argument")
#        sys.exit()
#    api = SupWSD(api)
#        
#    files = soul.files.ls(FLAGS.dir)
#    if FLAGS.max > 0:
#        data = data[:FLAGS.max]
#    elif FLAGS.n > -1:
#        if FLAGS.n > len(files):
#            raise ValueError("out of bounds. ({} of {})".format(FLAGS.n, len(files)))
#        files = [files[FLAGS.n]]
#    for datafile in tqdm(files):
#        res = tag_story(soul.files.json(datafile), api, FLAGS.share, FLAGS.comb)
#        soul.files.dump_json(res, datafile)
