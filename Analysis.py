#!/usr/bin/env python3
from optparse import OptionParser
import numpy as np
import random
import math
import sys
import json
from collections import OrderedDict
import networkx as nx 
import matplotlib.pyplot as plt

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

## Mincutv2
mincutv2 = groups["mincut_v2"]
mincutv2["uniform"] = ["topos/finiteTopologies/300x300_1000n.topo", "topos/finiteTopologies/mincut_new_300x300_NEWFINAL.group"]
mincutv2["forks"] = ["topos/forks/forks.topo", "topos/forks/forks_mincut_NEWFINAL.groups"]
mincutv2["tynset"] = ["topos/tynset/tynset.topo", "topos/tynset/tynset_mincut_newfinal.group"]
mincutv2["lillehammer"] = ["topos/lillehammer/lillehammer.topo", "topos/lillehammer/mincut_lillehammer_NEWFINAL.groups"]

## Mincut 
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

    return groupCollection
        #print (g.computeGroupCentroid())

def trigger(place):
    return DB(evaluate(place[0], place[1]))

def init_eval(groups):
    uniform = round(trigger(groups["uniform"]), 1)
    tynset = round(trigger(groups["tynset"]), 1)
    forks = round(trigger(groups["forks"]), 1)
    lillehammer = round(trigger(groups["lillehammer"]), 1)

    print("Uniform", uniform );
    print("Tynset", tynset) 
    print("Forks", forks);
    print("Lillehammer", lillehammer) 
    return [uniform, tynset, forks, lillehammer]


def Bouldin():
    SMALL_SIZE = 10
    plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize


    nosplit  = init_eval(groups["nosplit"])
    kmeans = init_eval(groups["kmeans"])
    mincutv1 = init_eval(groups["mincut"])
    mincutv2 = init_eval(groups["mincut_v2"])

    ind = np.arange(len(nosplit))  # the x locations for the groups
    width = 0.15  # the width of the bars
    fig, ax = plt.subplots()
    rects1 = ax.bar(ind - 2*width, nosplit, width, yerr=None, 
            color='SkyBlue', label='No splitting')
    rects2 = ax.bar(ind - width, kmeans, width, yerr=None,
            color='IndianRed', label='K-means split')
    rects3 = ax.bar(ind, mincutv1, width, yerr=None,
            color='DarkSeaGreen', label='Original mincut split')
    rects4 = ax.bar(ind + width, mincutv2, width, yerr=None,
            color='MediumOrchid', label='Improved mincut split')



# Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Davies-Bouldin index')
    ax.set_title('Davies-Bouldin index by topology')
    ax.set_xticks(ind)
    ax.set_xticklabels(('Uniform', 'Tynset', 'Forks', 'Lillehammer'))
    ax.legend()


    def autolabel(rects, xpos='center'):
        """
        Attach a text label above each bar in *rects*, displaying its height.

        *xpos* indicates which side to place the text w.r.t. the center of
        the bar. It can be one of the following {'center', 'right', 'left'}.
        """

        xpos = xpos.lower()  # normalize the case of the parameter
        ha = {'center': 'center', 'right': 'left', 'left': 'right'}
        offset = {'center': 0.52, 'right': 0.63, 'left': 0.45}  # x_txt = x + w*off

        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()*offset[xpos], 1.01*height,
                    '{}'.format(height), ha=ha[xpos], va='bottom', fontsize=8)
            


    autolabel(rects1, "center")
    autolabel(rects2, "center")
    autolabel(rects3, "center")
    autolabel(rects4, "center")
    plt.show()

def A(s):
    s = s[0];
    sm = 0;
    for n in s.members:
        for v in range(len(n._neighbours)):
            sm += v["ssid"]*-1;
    print(sm);

def triggerC(place):
     return A(evaluate(place[0], place[1]))


         
def conductance():
    uniform = round(triggerC(groups["nosplit"]), 1)
    #tynset = round(trigger(groups["tynset"]), 1)
    #forks = round(trigger(groups["forks"]), 1)
    #lillehammer = round(trigger(groups["lillehammer"]), 1)
    

conductance()

    
#def Dunn():





#evaluate(sys.argv[1], sys.argv[2])

