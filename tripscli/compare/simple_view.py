import re
from collections import defaultdict as ddict

def get_nodes_only(p):
    x = {}
    for sub in p:
        for key, val in sub.items():
            if key != "root":
                x[key] = val
    return x

def tagged(sentence, sup=False):
    if sup:
        parse = sentence["input_tags"]
    else:
        parse = get_nodes_only(sentence["parse"]).values()
    text = " "+sentence["sentence"].lower() + " "
    new_sent = []
    for node in parse:
        if sup:
            word = node["lex"]
            ntype = node.get("senses", {"NOTA": 1})
            if ntype:
                ntype = max(ntype.items(), key=lambda x: x[1])[0]
            else:
                ntype = "NOTA"
        else:
            word = node.get("roles", {}).get("LEX", "++NONE++").lower()
            ntype = node["type"]
        if word == "++none++":
            continue
        span = text[node["start"]:node["end"]]
        query = re.findall("[^\w]%s[^\w]" % word, span)
        if not query:
            continue
        if len(query) > 1:
            print(word, "has multiple matches in span.")
            continue
        ind = span.find(query[0]) + node["start"]
        if ind and not ntype.startswith("SA_") and ntype != "NOTA":
            new_sent.append((ntype, word, ind, ind+len(word)))
    return sorted(new_sent, key=lambda x: x[2])

def view(sentence):
    pieces = tagged(sentence)
    text = sentence["sentence"].lower()
    final = "" 
    prev_start = 0
    ptr = 0
    for a, b, start, stop in pieces:
        final += text[ptr:start]
        if start == prev_start and ptr == stop:
            final += "|%s" % a
        else:
            final += "%s/%s" % (b,a)
        prev_start = start
        ptr = stop
    return final

def as_key_val(a):
    return ("%s (%d, %d)" % a[1:]), a[0].upper()

def compare_taggings(parse1, parse2, sup=False, diff=True):
    sentence = parse1["sentence"]
    parse1 = tagged(parse1)
    parse2 = tagged(parse2, sup=sup)

    res = ddict(lambda: ([], []))
    for x in parse1:
        a, b = as_key_val(x)
        res[a][0].append(b)
    for x in parse2:
        a, b = as_key_val(x)
        res[a][1].append(b)

    if diff:
        for r in list(res.keys()):
            if len(res[r]) == 2 and res[r][0] == res[r][1]:
                del res[r]
    
    return {"sentence": sentence, "tags": res}
