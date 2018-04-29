#!/usr/bin/env python3
from optparse import OptionParser
import numpy as np
import random
import math
import sys
import json
from collections import OrderedDict
import networkx as nx 

import GenerateTopology as gt
import GroupCreation as gc
#Global arguments
args = None

topos = "";
group = "";

groups = {}
groups["nosplit"] = {}
groups["mincut_v2"] = {}
groups["mincut"] = {}
groups["kmeans"] = {}

## NO SPLIT
nosplit = groups["nosplit"]
nosplit["uniform"] = ["topos/finiteTopologies/300x300_1000n.topo", "topos/finiteTopologies/Basic300x300_1000n.groups"]
nosplit["forks"] = ["topos/forks/forks.topo", "topos/forks/forks_nosplit.json"]
nosplit["tynset"] = ["topos/tynset/tynset.topo", "topos/tynset/nosplit.groups"]
nosplit["lillehammer"] = ["topos/lillehammer/lillehammer.topo", "topos/lillehammer/nosplit.groups"]

#Kmeans
kmeans = groups["kmeans"]
kmeans["uniform"] = ["topos/finiteTopologies/300x300_1000n.topo", "topos/finiteTopologies/mincut_new_300x300_NEWFINAL.group"]
kmeans["forks"] = ["topos/forks/forks.topo", "topos/forks/forks_kmeans.json"]
kmeans["tynset"] = ["topos/tynset/tynset.topo", "topos/tynset/kmeans.groups"]
kmeans["lillehammer"] = ["topos/lillehammer/lillehammer.topo", "topos/lillehammer/kmeans.groups"]

## Mincut
mincutv2 = groups["mincut_v2"]
mincutv2["uniform"] = ["topos/finiteTopologies/300x300_1000n.topo", "topos/finiteTopologies/mincut_new_300x300_NEWFINAL.group"]
mincutv2["forks"] = ["topos/forks/forks.topo", "topos/forks/forks_mincut_NEWFINAL.groups"]
mincutv2["tynset"] = ["topos/tynset/tynset.topo", "topos/tynset/tynset_mincut_newfinal.group"]
mincutv2["lillehammer"] = ["topos/lillehammer/lillehammer.topo", "topos/lillehammer/mincut_lillehammer_NEWFINAL.groups"]

## Mincut v2
mincut = groups["mincut"]
mincut["uniform"] = ["topos/finiteTopologies/300x300_1000n.topo", "topos/finiteTopologies/mincut_new_300x300_FINAL.group"]
mincut["forks"] = ["topos/forks/forks.topo", "topos/forks/forks_mincut_FINAL.groups"]
mincut["tynset"] = ["topos/tynset/tynset.topo", "topos/tynset/tynset_mincut_FINAL.groups"]
mincut["lillehammer"] = ["topos/lillehammer/lillehammer.topo", "topos/lillehammer/mincut_lillehammer_FINAL.groups"]



def getNodeData(n):
    node = gt.Node(n["posX"], n["posY"], 0, n["frequency"], 0,  name = n["ssid"])
    neighbourCount = n["neighbourCount"] 
    neighbours = []
    for i in range(neighbourCount):
        neighbours.append(n["neighbours"][str(i)])
    node._neighbours = neighbours
    return node

def getTopoData(t):
    topo = gt.Topology(t["mapWidth"], t["mapHeight"], None, t["nodeCount"], None) 
    nodes = []
    for i in range(topo.getNodeCount()):
        node = getNodeData(t["nodes"][str(i)])
        nodes.append(node)
        topo._nodesDict[node.name] = node

    topo._nodes = nodes
    for i in topo._nodes:
        for n in i._neighbours:
            n["obj"] = topo._nodesDict[n["ssid"]]
    return topo

    
def S(group):
    Ti = len(group.members)
    Ai = group.computeGroupCentroid()
    val = 0
    for n in group.members:
        Xi = np.array((n.x, n.y))
        val = val + np.linalg.norm(Xi - Ai) #math.sqrt((Xi - Ai)**2)
    return val/Ti;

def M(i, j):
    Ai = i.computeGroupCentroid()
    Aj = j.computeGroupCentroid()
    return np.linalg.norm(Ai - Aj)

def R(i, j):
    return S(i) + S(j) / M(i,j)
def DB(groupCollection):
    end = []
    for i in groupCollection:
        vals = []
        for j in groupCollection:
            if j.name != i.name:
                vals.append(R(i, j))
        end.append(max(vals))

    DB = 1/len(groupCollection) * sum(end);
    return DB;


def evaluate(thetopo, thegroup):
    try: 
        topos = thetopo;
        group = thegroup;
    except IndexError:
        print("Specify an input filename");
        sys.exit(0);

    try:
        f = open(group).read()
        topo = open(topos).read()

    except FileNotFoundError:
        print("File not found!")
        sys.exit(0)

    t = json.loads(f)
    topoDict = json.loads(topo);
    topology = getTopoData(topoDict);

    i = str(t["iterationCount"] - 1);
    iteration = t["iterations"][i];
#groupCount = iteration["groupCount"]
    groupCollection = []
    for key, value in iteration.items():
        if (key != "groupCount"):
            group = gc.Group(None, value["groupName"])

            for key, value in value["members"].items():
                node = topology._nodesDict[value]
                group.members.append(node)
                node.group = group
            groupCollection.append(group)

    return DB(groupCollection)
        #print (g.computeGroupCentroid())

def trigger(place):
    return evaluate(place[0], place[1])

def init_eval(groups):
    print("Uniform", trigger(groups["uniform"]));
    print("Tynset", trigger(groups["tynset"]));
    print("Forks", trigger(groups["forks"]));
    print("Lillehammer", trigger(groups["lillehammer"]))

#print("Method: nosplit")
#init_eval(groups["nosplit"])


#print("Method: mincut_v2")
#init_eval(groups["mincut_v2"])

print("Method: kmeans")
#init_eval(groups["kmeans"])


import matplotlib.pyplot as plt

men_means, men_std = (20, 35, 30, 35, 27), (2, 3, 4, 1, 2)
women_means, women_std = (25, 32, 34, 20, 25), (3, 5, 2, 3, 3)

ind = np.arange(len(men_means))  # the x locations for the groups
width = 0.35  # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(ind - width/4, men_means, width, yerr=men_std,
        color='SkyBlue', label='KCN-Clustering')
rects2 = ax.bar(ind + width/4, women_means, width, yerr=women_std,
        color='IndianRed', label='K-means splitting')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Scores')
ax.set_title('Scores by group and gender')
ax.set_xticks(ind)
ax.set_xticklabels(('G1', 'G2', 'G3', 'G4', 'G5'))
ax.legend()


def autolabel(rects, xpos='center'):
    """
    Attach a text label above each bar in *rects*, displaying its height.

    *xpos* indicates which side to place the text w.r.t. the center of
    the bar. It can be one of the following {'center', 'right', 'left'}.
    """

    xpos = xpos.lower()  # normalize the case of the parameter
    ha = {'center': 'center', 'right': 'left', 'left': 'right'}
    offset = {'center': 0.5, 'right': 0.57, 'left': 0.43}  # x_txt = x + w*off

    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()*offset[xpos], 1.01*height,
                '{}'.format(height), ha=ha[xpos], va='bottom')


        autolabel(rects1, "left")
autolabel(rects2, "right")

plt.show()

#evaluate(sys.argv[1], sys.argv[2])

