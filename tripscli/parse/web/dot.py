from pytrips.nodegraph import NodeGraph

FORMAT = {
    "default" : {
        "base_node": {
            "fontname": "Work Sans",
            "shape": "plain",
            "fontsize": "8"
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
}

def as_dot(graph, format="default"):
    """Takes a parse field from a json output, returns a graphviz graph"""
    format = FORMAT.get(format, {})
    H = NodeGraph(
        default_node_attr=format.get("base_node", {}),
        default_edge_attr=format.get("base_edge", {}),
        no_escape=True
    )

    for i, utterance in enumerate(graph):
        G = NodeGraph(
            default_node_attr=format.get("base_node", {}),
            default_edge_attr=format.get("base_edge", {}),
            no_escape=True,
            name="cluster_utt_"+str(i)
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
            #val, attrs = render_node(v, format)
            #graph.node(x, label=val, attrs=attrs)
            label, attrs = render_node_table(v, format)
            graph.node(x, attrs, label)

def render_edges(utt, graph, format):
    for key, val in utt.items():
        if key == "root" or "roles" not in val:
            continue
        for role, target in val["roles"].items():
            if target[0] == "#":
                span = {} #{"ltail":"cluster_"+key, "lhead":"cluster_"+target[1:]}
                graph.edge(key+"_type", target[1:], role, attrs=dict(format.get("base_edge", {}),
                                                             **span
                                                             ))

def render_node_graph(node, format):
    G = NodeGraph(
        default_node_attr=format.get("base_node", {}),
        default_edge_attr=dict(format.get("base_edge", {}), arrowhead="none"),
        no_escape=True,
        name="cluster_{}".format(node["id"]),
        attrs={
            "style": "filled",
            "fillcolor": "white",
            "rankdir": "LR"
        }
    )
    
    G.node(node["id"], attrs={"fontcolor": "red"})
    get_label = lambda label: node["id"]+"_"+label

    G.node(get_label("type"), label=node["type"])
    G.edge(node["id"], get_label("type"))
    
    G.node(get_label("indicator"), label=node["indicator"])
    G.edge(get_label("indicator"), get_label("type"), attrs={"arrowhead": "none"})
    
    if "WNSENSE" in node["roles"]:
        G.node(get_label("wn"), label=node["roles"]["WNSENSE"])
        G.edge(node["id"], get_label("wn"))
    if "word" in node and node["word"]:
        G.node(get_label("word"), label=node["word"])
        G.edge(node["id"], get_label("word"))
    return G

def render_node_table(node, format={}):
    row = "<TR><TD>%s</TD><TD>%s</TD></TR>"
    attrs = format.get("base_node", {})
    lex = ""
    if "word" in node:
        lex = row % ("LEX",  node["word"])
    if "roles" in node and "WNSENSE" in node["roles"]:
        lex += "\n    " + row % ("wn", node["roles"]["WNSENSE"])
    lex += row % ("span", "(%d, %d)" % (node["start"], node["end"]))
    label = """<<TABLE cellspacing="0" border="0" cellborder="1" cellpadding="0">
    <TR><TD colspan='2'>%s</TD></TR>
    <TR><TD>%s</TD><TD>%s</TD></TR>
    %s
    </TABLE>>""" % (node["id"], node["indicator"], "ONT::"+node["type"], lex)
    return label, attrs
