from tripscli.parse import TripsParser
from pprint import pprint


testfile = "examples.json"

p = TripsParser(url="http://localhost:8081/cgi/STEP")
res = p.query_json(testfile, plain=False)
plain = p.query_json(testfile, plain=True)

def strip_dbg(parse):
    del parse["debug"]

for p in plain:
    strip_dbg(p)

for r in res:
    strip_dbg(r)

pprint(plain[3])
print("----------------")
pprint(res[3])

from tripscli.compare import compare_taggings

for a, b in zip(plain, res):
    comp = compare_taggings(a, b)
    pprint(comp)
