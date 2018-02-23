#!/usr/bin/env python3
import json
import GenerateTopology as gt
from GroupEvaluation import Evaluation 
import sys
import math
import numpy as np
from collections import OrderedDict
from optparse import OptionParser
import networkx as nx
import collections

topology = None
groupCollection = None
jsonOutput = None
maxSize = 0

#Parse commandline arguments
def parseOptions():
    parser = OptionParser()
    #Width
    ##parser.add_option("-x", "--width", action="store", type="int",
            #dest="width", default=500, help="Width of topology in meters. Default: 100")
    parser.add_option("-f", "--file", action="store", type="string",
            dest="input", default="topology.json", help="Input filename, from GenerateTopology.py")
    parser.add_option("-o", "--output", action="store", type="string",
            dest="output", default="iteration_data.json", help="Output file in JSON file format.")
    parser.add_option("-s", "--size", action="store", type=int,
            dest="maxsize", default=128, help="Max group size.")
    parser.add_option("-t", "--type", action="store", help = "Splitting type. None, mincut, or kmeans.", 
            dest="type", default="none")

    return parser.parse_args()[0]

class Simulation:
    global topology
    output = None
    iterationIndex = 0;
    def __init__(self, outfile, splitMethod):
        global groupCollection
        global jsonOutput
        jsonOutput = OrderedDict()
        jsonOutput["iterations"] = {}

        self.output = outfile
        groupCollection = GroupCollection(splitMethod)

    def start(self): 
        self.initiateGroups()
        self.runIteration()
        self.writeOutput()

    #Create one group for each node as initiation
    def initiateGroups(self):
        global topology
        global groupCollection
        for node in topology.getNodes():
            node.group = groupCollection.newGroup(node)

        jsonOutput["iterations"][0] = groupCollection.getOutput()
        input("Press enter to start simulation...") 

    def runIteration(self): 
        global groupCollection 
        self.iterationIndex += 1;
        while (groupCollection.iterateGroups() != 0):
            jsonOutput["iterations"][self.iterationIndex] = groupCollection.getOutput()
            self.iterationIndex += 1
            print("iteration", self.iterationIndex)
            if (self.iterationIndex == 30):
                break;

    def writeOutput(self):
        print("Interation index", self.iterationIndex) 
        print("Lengde", len(groupCollection.groups), groupCollection.groupCount)
        jsonOutput["iterationCount"] = self.iterationIndex
        j = json.dumps(jsonOutput, indent=2)
        self.output.write(j)

    def introduceNode(self, posx, posy, name):
        node = gt.Node(posx, posy, 0, 0, 75, name=name)
        node.group = groupCollection.newGroup(node)
        self.runIteration()
    
class GroupCollection:
    groups = None
    groupDict = {}
    groupCount = 0
    splitMethod = None

    def __init__(self, sm):
        self.splitMethod = sm
        self.groups = []
           
    def size(self):
        return self.groupCount;
     
    def getOutput(self):
        data = {}
        for i in range(len(self.groups)):
            data["groupCount"] = len(self.groups)
            data[i] = {}
            data[i]["groupName"] = self.groups[i].name 
            data[i]["memberCount"] = len(self.groups[i].members)
            data[i]["members"] = {}
            for n in range(len(self.groups[i].members)):
                data[i]["members"][n] = self.groups[i].members[n].name
        return data

    def dumpGroups(self):
        for g in self.groups:
            print("#############################")
            print("GROUP ID:", g.name)
            for node in g.members:
                print("     >", node)


    def newGroup(self, member):
        groupName = "GROUP"+str(self.groupCount)
        group = Group(member, groupName)
        member.group = group
        self.appendGroup(group)
        return group

    def appendGroup(self, group):
        self.groupCount += 1
        self.groups.append(group)
        self.groupDict[group.name] = group
    
    def iterateGroups(self):
        changes = 0
        if len(self.groups) == 1:
            return changes
        
        for g in self.groups:
            changes += g.iteration()
        return changes

    def removeGroupByName(self, name):
        if name in self.groupDict: del self.groupDict[name] 
        for g in self.groups:
            if name == g.name:
                self.groups.remove(g)
                break

class Group:
    members = None
    name = None
    graph = None
    locked = False
    merges = 1

    def __init__(self, node, name):
        self.members = []
        self.members.append(node)
        self.name = name
        self.graph = nx.Graph() 
        self.graph.add_node(node)

    def kmeans(self, node, initiator, dbi):
        global maxSize
        oldName = node.group.name
        oldMembers = node.group.members
        print("Performing split")
        startMu = self.computeNewMu([(0,0), (0,0)], [self.members, oldMembers])
        return self.KmeansSplit(startMu[0], startMu[1], self, node.group, dbi)

    def nosplit(self, node, initiator):       
            return 0
 
    def wagner(self, receiver, initiator, dbi): 
        return self.createGraphAndCut(receiver.group, receiver, dbi);

    def mincut(self, receiver, initiator, dbi): 
        oldSelf = self.members.copy()
        oldGroup2 = receiver.group.members.copy()
        remove = self.mincutCreateGraphAndCut(receiver.group, receiver, dbi);
        self.members = self.members + receiver.group.members
        receiver.group.reaffirmMembers()

        for n in remove:
            self.members.remove(n)

        for n in remove:
            for m in self.members:
                nDbi = m.rssiNeighbour(n) 
                if (nDbi != None):
                    if nDbi > dbi:
                        print(nDbi, dbi, "cancel")
                        self.members = oldSelf
                        self.reaffirmMembers()
                        receiver.group.members = oldGroup2
                        receiver.group.reaffirmMembers()
                        return 0

        groupCollection.removeGroupByName(receiver.group.name) 
        print("keep")
        for n in remove:
            groupCollection.newGroup(n)
        return 1

    def merge(self, node, initiator, dbi):
        global groupCollection
        global topology 
        global maxSize
        oldName = node.group.name
        oldMembers = node.group.members

        if (node.group.name == self.name):
            print("NODE", node.name, "of group", node.group, "wants to merge with", self.name)
            print("MEMBERS", self.members)
            sys.exit(0)

        if (len(self.members) + len(oldMembers) > maxSize): 
            if groupCollection.splitMethod == "none":
                return self.nosplit(node, initiator)
            elif groupCollection.splitMethod == "wagner":
                return self.wagner(node, initiator, dbi)
            elif groupCollection.splitMethod == "mincut":
                if (len(self.members) + len(node.group.members) > (maxSize * 1.5)):
                    return 0
                return self.mincut(node, initiator, dbi)

            elif groupCollection.splitMethod == "kmeans":
                return self.kmeans(node, initiator, dbi)

        for n in oldMembers:
            n.group = self

        self.members = self.members + oldMembers
        groupCollection.removeGroupByName(oldName) 
        return 1

    def mincutCreateGraphAndCut(self, group2, receiver, dbi): 
        global groupCollection
        global maxSize
        G = self.mincutBuildGraph(self.members, group2.members, dbi)
        #print(self.name, group2.name, receiver.name)
        #print(len(self.members), len(group2.members))
        #print(G.number_of_nodes())
        minval = 9999
        cutFrom = None
        cut = None
        removedNodes = []
        while (G.number_of_nodes() > maxSize):
            cut, partition = nx.stoer_wagner(G, "capacity")
            exclude = None
            if len(partition[0]) > len(partition[1]):
                exclude = partition[1]
            else:
                exclude = partition[0]
                
            removedNodes.extend(exclude)
            for n in exclude:
                G.remove_node(n)
            
        print(G.number_of_nodes())
        return removedNodes;
       # for node in self.members: 
       #     val, cut = nx.minimum_cut(G, node, receiver, "capacity")
       #     #print(val, node.name)
       #     if (val < minval):
       #         minval = val
       #         cutFrom = node.name
       #         cut = cut
       #         
       # print(G.number_of_nodes())
       # print(minval, len(cut[0]), len(cut[1]), cutFrom)
       # if (len(cut[1]) != 1 and len(cut[0]) != 1):
       #     print(cut)
       #     sys.exit(0)
       # #if (len(list(cut[1])[0] != receiver):

       # return 0

    def mincutBuildGraph(self, members1, members2, minDbi): 
        joined = members1 + members2
        G = nx.Graph()
        for node in joined:
            node.combined = 0
            node.cHighest = 0
            for otherNode in joined:
                dbi = node.calculateInterferenceTo(otherNode)
                if dbi != None:
                    if (dbi < -75):
                        dbi = -99
                    if (dbi > minDbi):
                        
                        
                    G.add_edge(node, otherNode, capacity=int(100 + dbi))
                    node.combined += 100 + dbi
                    if (100 + dbi) > node.cHighest:
                        node.cHighest = 100 + dbi
        return G
    def createGraphAndCut(self, group2, receiver, dbi):
        global groupCollection
        r, d = self.buildGraph(self.members, group2.members, dbi);
        if r == 1:
            return 0 
        
        if (set(self.members) == set(d) or set(self.members) == set(r)):
            return 0
        groupCollection.removeGroupByName(group2.name) 
        self.members = []
        for node in r:
           node.group = self
           self.members.append(node)
        for node in d:
            groupCollection.newGroup(node)

        print("Mincut", self.name)
        print("returned 1 change")
        return 1

    def buildGraph(self, members1, members2, minDbi):
        joined = members1 + members2
        interferences = []
        G = nx.Graph()
        for node in joined:
            node.combined = 0
            node.cHighest = 0
            for otherNode in joined:
                dbi = node.calculateInterferenceTo(otherNode)
                if dbi != None:
                    interferences.append(dbi)
                    if (dbi < -100):
                        dbi = -99
                    G.add_edge(node, otherNode, capacity=int(100 + dbi))
                    node.combined += 100 + dbi
                    if (100 + dbi)  > node.cHighest: 
                        node.cHighest = 100 + dbi
        r, d = self.minCut(G, minDbi)
        if (r == 1):
            print("Minimum cut discarded")
            return 1, []
        else:
            print("Minimum cut accepted")
        return r, d

    def minCut(self, graph, minDbi):
        global maxSize
        cut, partition = nx.stoer_wagner(graph, "capacity")
        p1, p2 = partition
        r = 0;

        if (len(p1) != 1 and len(p2) != 1):
            print("Length of partition is not 1", len(p1), len(p2))
            sys.exit(0)

        #print(len(p1), len(p2))
        #print("cut", cut, "combined", p1[0].combined, "highest", p1[0].cHighest, "r", r)

        if (p1[0].cHighest > 100+minDbi):
            return 1, []

        if (len(p1) > maxSize):
            for n in p2:
                graph.remove_node(n)
            r, l = self.minCut(graph, minDbi)
            l = l + p2
        elif(len(p2) > maxSize):
            for n in p1:
                graph.remove_node(n)
            r, l  = self.minCut(graph, minDbi)
            l = l + p1
        else:
            if (len(p1) > len(p2)):
                return p1, p2
            else:
                return p2, p1
        return r, l;

    def doMinCut(self, graph, toNode, dbi):
        global maxSize
        #First merge to new oversized graph and groups
        reachable, nonreachabe = (None, None)
        cval = 0
        for n in self.members:
            cut, partition = list(nx.minimum_cut(graph, n, toNode))
            r, nr = partition
            if cut > cval and len(partition[0]) <= maxSize and len(partition[1]) <= maxSize:
                cval = cut
                reachable, nonreachable = partition
        
        #Check edges of original graph, add edges if nodes are in partition, if not, discard the edges
        newDbi = self.highestExternalDbi(reachable) 
        print(newDbi, dbi) 
        if newDbi >= dbi:
            print("ABORTS")
            return 0
        
        print(reachable, cval, "highest DBI", self.highestExternalDbi(reachable))
        sys.exit(0)

    def highestExternalDbi(self, nodeList):
        highest = -100
        disturber = None
        initiator = None
        for n in nodeList:
            node = n.getMostDisturbing(nodeList=nodeList)
            if node != None:
                gr = node["obj"].group
                if (node["dbi"] > highest and not gr.locked):
                    highest = node["dbi"]
                    disturber = node["obj"]
                    initiator = n
        return highest

    def joinGraphs(self, graph1, graph2, initiator, receiver, w): 
        #Only add the link between merging nodes, or add all connected nodes?
        graph = nx.Graph()
        graph.add_edge(initiator, receiver, capacity=int(100 - w))
        for n in graph1.edges_iter(data=True):
            graph.add_edge(n[0], n[1], n[2])

        for n in graph2.edges_iter(data=True):
            graph.add_edge(n[0], n[1], n[2])
        return graph

    def reaffirmMembers(self):
        for n in self.members:
            n.group = self

    def findNodeWithMostNeighbours(self):
        neighbours = 0 
        node = None
        for n in self.members:
            c = n.getNeighbourCount()
            if c >= neighbours:
                node = n
                neighbours = c
        return node


    #Instead of regular K-means, using random values 
    # for mu, instead use centroid position of the nodes
    # who wants to merge
    def KmeansSplit(self, point1, point2, group1, group2, oldDbi): 
        global GroupCollection
        global maxSize
        group1copy = group1.members.copy()
        group2copy = group2.members.copy()
        changes = 0
        newDbi = -100
        old = [(0,0), (0,0)]
        mu = [point1, point2]
        groups = (group1.members, group2.members)
        while not mu == old:
            groups = self.assignGroups(mu, groups)
            old = mu;
            mu = self.computeNewMu(mu, groups)

        if len(groups[0]) > maxSize or len(groups[1]) > maxSize:
            return 0

        for node in groups[0]:
            if node in group2.members: 
                changes = changes + 1
                group2.members.remove(node)
                group1.members.append(node)
                node.group = group1

        for node in groups[1]:
            if node in group1.members:
                changes = changes + 1
                group1.members.remove(node)
                group2.members.append(node)
                node.group = group2
                
        _, _, dbi1 = group1.getMostDisturbing()
        _, _, dbi2 = group2.getMostDisturbing()
        newDbi = max(dbi1, dbi2)
        if (newDbi > oldDbi):
            print("DBI Bad: Restore groups! Old dbi:", oldDbi, "newDbi", newDbi)
            group1.members = group1copy
            group2.members = group2copy
            for node in group1.members:
                node.group = group1

            for node in group2.members:
                 node.group = group2 
            return 0

        print("Keep!", group1, group2)
        return changes


 
    def computeNewMu(self, oldMu, groups): 
        newMu = []
        arrayVals = [[], []]
        for g in range(0, 2):
            x = 0
            y = 0
            for node in groups[g]:
                x = x + node.x
                y = y + node.y
            if len(groups[g]) != 0:
                newMu.append((math.ceil(x / len(groups[g])), math.ceil(y / len(groups[g]))))
            else:
                newMu.append(oldMu[g])
        return newMu

    def assignGroups(self, mu, groups):
        nodes = groups[0] + groups[1]
        newGroups = [[], []]
        for n in nodes:
            dist1 = self.distanceToPoint((n.x, n.y), mu[0])
            dist2 = self.distanceToPoint((n.x, n.y), mu[1])
            if (dist1 < dist2):
                newGroups[0].append(n)
            else:
                newGroups[1].append(n)
        
        return (newGroups[0], newGroups[1])

    
    def distanceToPoint(self, point1, point2):
       x = point2[0] - point1[0]
       y = point2[1] - point1[1]

       return math.sqrt(x**2 + y**2)

    def findLeastDisturbingMember(self): 
        least = 100
        disturber = None
        for n in self.members:
            node = n.getLeastDisturbingCompanion()
            if node != None:
                if (node["dbi"] < least):
                    least = node["dbi"]
                    disturber = node["obj"]
        return disturber

    def iteration(self):    
        if self.locked:
            return 0
        disturber, initiator, dbi = self.getMostDisturbing()
        ret = 0
        if disturber != None:
            ret = self.merge(disturber, initiator, dbi)
        return ret

    def getMostDisturbing(self):
        highest = -100
        disturber = None
        initiator = None
        for n in self.members:
            node = n.getMostDisturbing()
            if node != None:
                gr = node["obj"].group
                if (node["dbi"] > highest and not gr.locked):
                    highest = node["dbi"]
                    disturber = node["obj"]
                    initiator = n
        return disturber, initiator, highest

    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name
    def __unicode__(self):
        return self.name

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
    
def main():
    global topology
    global jsonOutput
    global maxSize
    global groupCollection
    args = parseOptions()
    maxSize = args.maxsize
    infile = open(args.input, "r")
    outfile = open(args.output, "w")
    cont = infile.read()
    topoDict = json.loads(cont)
    topology = getTopoData(topoDict)
    s = Simulation(outfile, args.type)
    s.start()
    outfile.close()
    print("Groups written to file.")
    ev = Evaluation(topology)
    print(groupCollection.groups)
    #ev.calculateGroupFitness(groupCollection.groups)

if __name__ == "__main__":
    main()
