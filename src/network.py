# -*- coding: utf-8 -*-
"""
Use NetworkX to create the desired format for Gephi

:authors: Egor Bronnikov <bronnikov.40@mail.ru>
:license: GNU General Public License v3.0

:copyright: (c) 2022 endygamedev
"""

# Modules
import networkx as nx
import json


# Filename of JSON-file
FILENAME_JSON = "friends"

# Filename for GEXF-file that contains information about graph
FILENAME_GEXF = "graph"


with open(f"{FILENAME_JSON}.json", "r") as f:
    data = json.load(f)

data = {int(k): v for k, v in data.items()}

g = nx.Graph(data)

nx.write_gexf(g, f"{FILENAME_GEXF}.gexf")

