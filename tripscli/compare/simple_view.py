import re
from collections import defaultdict as ddict

def get_nodes_only(p):
    x = {}
    for sub in p:
        for key, val in sub.items():
            if key != "root":
                x[key] = val
    return x

def tagged(sentence):
    parse = get_nodes_only(sentence["parse"])
    text = " "+sentence["sentence"].lower() + " "
    new_sent = []
    for key, node in parse.items():
        word = node.get("roles", {}).get("LEX", "++NONE++").lower()
        if word == "++none++":
            continue
        query = re.findall("[^\w]%s[^\w]" % word, text)
        if not query:
            continue
        if len(query) > 1:
            print(word, "has multiple matches")
            continue
        ind = text.find(query[0])
        if ind and not node["type"].startswith("SA_"):
            new_sent.append((node["type"], word, ind, ind+len(word)))
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
    return ("%s (%d, %d)" % a[1:]), a[0]

def compare_taggings(parse1, parse2):
    sentence = parse1["sentence"]
    parse1 = tagged(parse1)
    parse2 = tagged(parse2)

    res = ddict(lambda: ([], []))
    for x in parse1:
        a, b = as_key_val(x)
        res[a][0].append(b)
    for x in parse2:
        a, b = as_key_val(x)
        res[a][1].append(b)
    
    return {"sentence": sentence, "tags": res}
