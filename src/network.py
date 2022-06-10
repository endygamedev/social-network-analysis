import networkx as nx
import json

with open("friends.json", "r") as f:
    data = json.load(f)

data = {int(k): v for k, v in data.items()}

g = nx.Graph(data)

nx.write_gexf(g, "graph.gexf")
