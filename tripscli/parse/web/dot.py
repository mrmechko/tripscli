from pytrips.nodegraph import NodeGraph
import json

cell_style = {
    "bgcolor": "black",
    "font": {
        "color": "white"
    }
}

node_style = {
    "label": cell_style,
    "value": cell_style
}

FORMAT = {
    "base_node": {
        "fontname": "Work Sans",
        "shape": "plain",
        "fontsize": "8"
    },
    "table": {
        "cellspacing": "0",
        "border": "0",
        "cellborder": "0",
        "cellpadding": "1",
        "default_cell": node_style,
        "lex": node_style,
        "wn": node_style,
        "ont": node_style,
        "span": node_style,
        "id": {
            "label": dict(cell_style, colspan="2")
        },
        "indicator": node_style,
    },
    "base_edge": {
        "fontname": "Work Sans",
        "fontsize": "8"
    },
    "root": {
        "shape": "diamond",
        "style": "filled",
        "fillcolor": "grey"
    }
}

def get_format_key(format, key=None, default=None):
    if key:
        res = _get_format_key(format, *key.split("."))
        if res:
            return res
    if default:
        return get_format_key(format, key=default, default=None)
    return format

def _get_format_key(format, *keys):
    keys = list(keys)
    #print(keys)
    if not keys:
        return {}
    if len(keys) == 1:
        return format.get(keys[0], {})
    return _get_format_key(format.get(keys[0], {}), *keys[1:])


def as_dot(graph, format=None, label=None):
    """Takes a parse field from a json output, returns a graphviz graph"""
    if not format:
        format = FORMAT
    else:
        format = json.load(open(format))
    H = NodeGraph(
        default_node_attr=get_format_key(format, "base_node"),
        default_edge_attr=get_format_key(format, "base_edge"),
        no_escape=True,
        attrs=dict(rankdir="TB", size="6,12"),
        label=label
    )

    for i, utterance in enumerate(graph):
        G = NodeGraph(
            default_node_attr=get_format_key(format, "base_node"),
            default_edge_attr=get_format_key(format, "base_edge"),
            no_escape=True,
            name="utt_"+str(i),
            attrs=dict(rankdir="TB")
        )    
        render_utterance(utterance, G, format)
        render_edges(utterance, G, format)
        H.add_subgraph(G)
    return H

def render_utterance(utt, graph, format):
    # 1. Get root
    # 2. Add reference to each node
    #graph.node(utt["root"][1:], attrs={x: y for x, y in format.get("root", {}).items()})
    ports = []
    for x, v in utt.items():
        if x != "root":
            label, attrs = render_node_table(v, format)
            graph.node(x, attrs, label)

def render_edges(utt, graph, format):
    for key, val in utt.items():
        if key == "root" or "roles" not in val:
            continue
        for role, target in val["roles"].items():
            style = dict(get_format_key(format, "edge.%s" % role, "base_edge"))
            # FIX: if there are multiple edges with the same label coming out
            #      labels are supposed to be encoded as a list
            def add_edge(t):
                if type(t) is dict:
                    edge_style = dict(style, **t.get("style", {}))
                    t = t.get("target")
                else:
                    edge_style = dict(style)
                if t[0] == "#":
                    name="%s_%s" % (key, t[1:])
                    graph.edge(key, t[1:], " %s   "  % str(TEXT(role)), attrs=edge_style)
            if type(target) is list:
                for t in target:
                    add_edge(t)
            else:
                add_edge(target)

               
def render_condensed_node_table(node, format={}):
    attrs = get_format_key(format, "base_node")
    t_attrs = get_format_key(format, "table")
    make_node = lambda text, path: TEXT(text or "* ", attrs=dict(get_format_key(t_attrs, path+".value")), font=dict(get_format_key(t_attrs, path+".value.font")))
    link = "http://trips.ihmc.us/lexicon/data/ONT::%s.xml" % node["type"]
    fnode = []
    node_style = node.get("style", {})
    #fnode.append(make_node("(", ""))
    fnode.append(make_node('<br />', "wn"))
    fnode.append(make_node(node["type"], "ont"))
    fnode.append(make_node('<br />', "wn"))
    fnode.append(make_node(node["indicator"], "indicator"))
    fnode.append(make_node(node["word"], "lex"))
    if "WNSENSE" in node["roles"]:
        fnode.append(make_node('<br />', "wn"))
        fnode.append(make_node(node["roles"].get("WNSENSE", ""), "wn"))
    fnode.append(make_node('<br /> ', "wn"))
    #fnode.append(make_node(")", ""))
    #fnode.append(make_node('<br ALIGN="LEFT"/>', "wn"))

    return "<%s>" % ' '.join([str(s) for s in fnode]), dict(attrs, URL=link, **node_style)


def render_node_table(node, format={}):
    return render_condensed_node_table(node, format=format)
    attrs = get_format_key(format, "base_node")
    t_attrs = get_format_key(format, "table")

    attributes = [TR([
        TD("lex",
           attrs=get_format_key(t_attrs, "lex.label"),
           font=get_format_key(t_attrs, "lex.label.font")),
        TD(node.get("roles", {}).get("LEX") or node["word"],
           attrs=get_format_key(t_attrs, "lex.value"),
           font=get_format_key(t_attrs, "lex.value.font"))
    ])]
    if "roles" in node and "WNSENSE" in node["roles"]:
        attributes.append(TR([
            TD("wn",
               attrs=get_format_key(t_attrs, "wn.label"),
               font=get_format_key(t_attrs, "wn.label.font")),
            TD(node["roles"]["WNSENSE"],
               attrs=get_format_key(t_attrs, "wn.value"),
               font=get_format_key(t_attrs, "wn.value.font"))
        ]))
    attributes.append(TR([
        TD("span",
               attrs=get_format_key(t_attrs, "wn.value"),
               font=get_format_key(t_attrs, "wn.value.font")),
        TD("(%d, %d)" % (node["start"], node["end"]),
           attrs=get_format_key(t_attrs, "wn.value"),
           font=get_format_key(t_attrs, "wn.value.font")
        )
    ]))
    label = Table(
        [
            TR(
                TD(node["id"],
                   attrs=get_format_key(t_attrs, "id.label"),
                   font=get_format_key(t_attrs, "id.label.font"))),
            TR([
                TD(node["indicator"],
                   attrs=get_format_key(t_attrs, "indicator.label"),
                   font=get_format_key(t_attrs, "indicator.label.font")),
                TD(node["type"],
                   attrs=get_format_key(t_attrs, "ont.value"),
                   font=get_format_key(t_attrs, "ont.value.font")
                )
            ])
        ] + attributes, attrs=format.get("table", {})
    )
    #print(str(label))
    return "<%s>" % str(label), attrs

class HTMLElement:
    tag = None
    def __init__(self, value, attrs=None, font=None, tag=None):
        self.value = value
        self.attrs = attrs
        if not self.attrs:
            self.attrs = {}
        self.font = font
        if not font:
            self.font = {}

    @property
    def attributes(self):
        return " " + " ".join(['%s="%s"' % (k, v) for k, v in self.attrs.items() if type(v) is str])

    @property
    def values(self):
        if type(self.value) is list:
            value = " ".join([str(v) for v in self.value])
        elif isinstance(self.value, HTMLElement):
            value = str(self.value)
        else:
            value = str(self.value)
        if self.font:
            #print(self.font)
            return "<font %s>%s</font>" % (" ".join(['%s="%s"' % (k, v) for k, v in self.font.items() if type(v) is str]), value)
        return value

    def __str__(self):
        fmt = "%s%s%s"
        if self.tag:
            open_t = "<%s%s>" % (self.tag, self.attributes)
            close_t = "</%s>" % self.tag
        else:
            open_t, close_t = "", ""
        return fmt % (open_t, self.values, close_t)

class Table(HTMLElement):
    tag = "TABLE"

class TR(HTMLElement):
    tag = "TR"

class TD(HTMLElement):
    tag = "TD"

class TEXT(HTMLElement):
    tag = ""
