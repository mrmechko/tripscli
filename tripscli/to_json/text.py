import json

from itertools import islice


def token_to_json(token, sid=None, gold=None, lftype=None):
    """
    Build a dictionary for a word
       {
        "start": 0,
        "end": 0,
        "lex": "word",
        "pos": "pos"
        "sid": "some_word_id_if_exists",
        "gold": "any gold wordnet tags",
        "lftype": "any gold/inferred TRIPS types"
       }
    """
    start = token.idx
    end = len(token) + start - 1
    lex = str(token)
    pos = str(token.pos_)
    tag = str(token.tag_)
    res = dict(start=start, end=end, lex=lex, pos=pos, sid=sid, gold=gold, lftype=lftype, tag=tag)
    return {k: v for k, v in res.items() if v or v == 0}

def chunk_to_json(chunk):
    """
    Build a dictionary for a chunk
        {
         "start": 0,
         "end": 0,
         "text": "text",
         "cat": "chunk-cat"
        }
    """
    start = chunk.start_char
    end = chunk.end_char
    text = chunk.orth_
    tag = chunk.label_
    return dict(start=start, end=end, text=text, tag=tag)


def sentence_to_json(text, nlp):
    """convert text into a json object using a spacy instance"""
    tagged = nlp(text)
    sentence = [token_to_json(t) for t in tagged]
    chunks = [chunk_to_json(t) for t in tagged.noun_chunks]
    return {"sentence": text, "input_tags": sentence, "spans": chunks}

def story_to_json(story_id, title, sentences, nlp):
    """convert a story into a json object"""
    return {"id": story_id, "title": title, "sentences": [sentence_to_json(x, nlp) for x in sentences]}
