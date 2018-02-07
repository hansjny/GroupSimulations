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


topology = None
groupCollection = None
jsonOutput = None
maxSize = 0
times = 0
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

    #Create one group for each node as initiation
    def initiateGroups(self):
        global topology
        global groupCollection
        for node in topology.getNodes():
            node.group = groupCollection.newGroup(node)

        jsonOutput["iterations"][0] = groupCollection.getOutput()
        #print("Number of groups created: ", groupCollection.size())
        #groupCollection.dumpGroups()
        input("Press enter to start simulation...") 
    
    def runIteration(self): 
        global groupCollection 
        i = 1
        while (groupCollection.iterateGroups() != 0):
            #groupCollection.dumpGroups()
            jsonOutput["iterations"][i] = groupCollection.getOutput()
            i += 1
        jsonOutput["iterationCount"] = i
        j = json.dumps(jsonOutput, indent=2)
        self.output.write(j)
        #groupCollection.dumpGroups()
        

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
     
    #Structure dictionairy suitable for JSON-output
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
        #return 
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
        #print("Made new group: ", group.name, "for node", member.name)
        return group

    def appendGroup(self, group):
        self.groupCount += 1
        self.groups.append(group)
        self.groupDict[group.name] = group
    
    def iterateGroups(self):
        changes = 0
       # print("Num groups", len(self.groups))
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

    def kmeans(self, node, initiator):
        if (len(self.members) > maxSize):
            point1 = self.findNodeWithMostNeighbours()
            point2 = node.group.findNodeWithMostNeighbours()
            #self.KmeansSplit((initiator.x, initiator.y), (node.x, node.y))
            self.KmeansSplit((point1.x, point1.y), (point2.x, point2.y))
            self.merges = self.merges - 1
        if (self.merges == 0):     
            self.locked = True

        return 0

    def nosplit(self, node, initiator):
        oldName = node.group.name
        oldMembers = node.group.members
        #print("OLDMEMBERS", oldMembers)
        
        if (len(self.members) + len(node.group.members) > maxSize):
            return 0
        #Update group name for members
        for n in oldMembers:
            n.group = self
        #    print("Setting group for", n.name, "to", self.name)

        self.members = self.members + oldMembers
        groupCollection.removeGroupByName(oldName) 


                #Split algorithm
        return 1
        
    def mincut(self, receiver, initiator, dbi): 
        oldName = receiver.group.name
        oldMembers = receiver.group.members
        I = receiver.group.graph 
        global times

        if (len(self.members) + len(receiver.group.members) > maxSize):
            #minimum_cut(inode, init
            split = self.joinGraphs(self.graph, I, initiator, receiver, dbi)
            mincut = 10000
            subset = None
            source = None
            #Fint best mincut, change source node
            cut, partition = nx.stoer_wagner(split, "capacity")
            print(cut)
            print(partition)

            for n in partition[0]: 
                split.remove_node(n)
            cut, partition = nx.stoer_wagner(split, "capacity")
            print(cut)
            print(partition)

            for n in partition[0]: 
                split.remove_node(n)
            cut, partition = nx.stoer_wagner(split, "capacity")
            print(cut)
            print(partition)
                #
            #accept cut
            sys.exit(0)
            return 0


        print(receiver.group.name, nx.number_of_edges(I))
        print(self.name, nx.number_of_edges(self.graph))

        self.graph = self.joinGraphs(self.graph, I, initiator, receiver, dbi)

        for n in oldMembers:
            n.group = self

        self.members = self.members + oldMembers
        groupCollection.removeGroupByName(oldName) 

        print(self.name, nx.number_of_edges(self.graph))
        return 1
    
    def joinGraphs(self, graph1, graph2, initiator, receiver, dbi): 
        #print("ORIGIN", nx.number_of_edges(graph1))
        #G = nx.disjoint_union(graph1, graph2)
        G = nx.Graph()
        G.add_edge(initiator, receiver, capacity=100-dbi)
        for n in graph1.edges_iter(data=True):
            G.add_edge(n[0], n[1], capacity=n[2]["capacity"])
        for n in graph2.edges_iter(data=True):
            G.add_edge(n[0], n[1], capacity=n[2]["capacity"])
        return G


        #print(dict(self.graph.edges))
        #self.graph = nx.disjoint_union(G, I)
        #self.graph.add_edge(initiator, receiver, weight=4.7 )
        #print(list(I.edges_iter(data=True)))



        #self.graph.add_nodes_from(self.graph.nodes()+I.nodes())



    def merge(self, node, initiator, dbi):
        global groupCollection
        global topology 
        global maxSize

        #print("Merging", node.group.name, "into", self.name)  

        if (node.group.name == self.name):
            print("NODE", node.name, "of group", node.group, "wants to merge with", self.name)
            print("MEMBERS", self.members)
            sys.exit(0)

        if groupCollection.splitMethod == "none":
            return self.nosplit(node, initiator)
        elif groupCollection.splitMethod == "mincut":
            return self.mincut(node, initiator, dbi)
        elif groupCollection.splitMethod == "kmeans":
            return self.kmeans(node, initiator)
    

    #
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
    # for mu, instead use the position of the nodes
    # who wants to merge
    def KmeansSplit(self, point1, point2): 
        global GroupCollection
        print(point1, point2)
        old = [(0,0), (0,0)]
        mu = [point1, point2]
        groups = (self.members, [])
        while not mu == old:
            groups = self.assignGroups(mu, groups)
            old = mu;
            mu = self.computeNewMu(mu, groups)
    
        try:
            newGroup = groupCollection.newGroup(groups[1][0])
        except IndexError:
            return
        
        newGroup.locked = True

        for node in groups[1]:
            self.members.remove(node)
            newGroup.members.append(node)
 
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
        else:
            print("No changes")
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
    ev.prioritizeClosest()

if __name__ == "__main__":
    main()
