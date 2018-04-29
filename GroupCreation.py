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
def StoerWagnerMincut(G, initiator):
    excluded = []
    while(1):
        if (G.number_of_nodes() <= 1):
            break;
        cut, partition = nx.stoer_wagner(G, "capacity")
        if (cut >= 99999):
            break;
        if initiator in partition[0]:
            exclude = partition[1]
        elif initiator in partition[1]:
            exclude = partition[0]
        else: 
            print("Couldn't find initiating node in stoer_wagner cut partitions!")
            sys.exit(0)
        tmp = []
        for n in exclude:
            G.remove_node(n)
            tmp.append(n)
        excluded.append(tmp)
    return excluded;

def RegularMincut(G, initiator):
    print("Performing mincut...")
    gr = initiator.group.members
    excluded = []
    minCutVal = 1000000; 
    minCutPart = None; 
        #Todo: run thorough all nodes and kick every shit where cut is less than line
    for source in gr:
            if source == initiator:
                continue;
            try:
                cut, partition = nx.minimum_cut(G, source, initiator, "capacity")
                if (cut >= 99999):
                    continue; 
                if initiator in partition[0]:
                    exclude = partition[1]
                elif initiator in partition[1]:
                    exclude = partition[0]
                else: 
                    print("Couldn't find initiating node in stoer_wagner cut partitions!")
                    sys.exit(0)
                tmp = []
                for n in exclude:
                    G.remove_node(n)
                    tmp.append(n)
                excluded.append(tmp)
            except nx.exception.NetworkXError:
                continue;
    return excluded;

def MincutWorst(G, initiator):
    gr = initiator.group.members
    minCutVal = 1000000
    minCutPart = []
    for source in G.nodes_iter():
        if source == initiator:
            continue
        cut, partition = nx.minimum_cut(G, source, initiator, "capacity")
        if (cut >= 99999):
            continue
        if cut < minCutVal:
            minCutVal = cut;
            if initiator in partition[0]:
                minCutPart = partition[1]
            elif initiator in partition[1]:
                minCutPart = partition[0]
    print(initiator.group.name, minCutPart)
    for n in minCutPart:
            G.remove_node(n)
    return list(minCutPart);
    


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
            if (self.iterationIndex == 100):
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
    dbiMinVal = -9999;
    memoiser = {}

    def __init__(self, node, name):
        self.members = []
        if (node != None):
            self.members.append(node)
        self.name = name
    
    def __hash__(self):
        hstr = ""
        bigstr = []
        for n in self.members:
            bigstr.append(n.name)
        for n in sorted(bigstr):
                hstr = hstr + n
        return hash(hstr)

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
        if (self.buildGraphAndMinCut(receiver, initiator, dbi) == True):
            return 1
        return 0

        

    def buildGraphAndMinCut(self, receiver, initiator, minDbi):
        global maxSize
        global groupCollection
        print("Attempting mincut")
        G1 = initiator.group.buildNxGraph(minDbi)
        G2 = receiver.group.buildNxGraph(minDbi)
            
        excl1 = []
        excl2 = []

#        excl1 = StoerWagnerMincut(G1, initiator)
#        excl2 = StoerWagnerMincut(G2, receiver)

        #excl1 = RegularMincut(G1, initiator)
        #excl2 = RegularMincut(G2, receiver)


        print("Group size before merge: ", G1.number_of_nodes() + G2.number_of_nodes())
        doExcl1 = True
        doExcl2 = True
        while (doExcl1 and doExcl2):
                if (doExcl1):
                        newExcl1 = MincutWorst(G1, initiator)
                        if (newExcl1 == []):
                                doExcl1 = False;
                        else:
                                excl1.append(newExcl1)
                if (doExcl2):
                        newExcl2 = MincutWorst(G2, receiver)
                        if (newExcl2 == []):
                                doExcl2 = False;
                        else:
                                excl2.append(newExcl2)
                if (not doExcl1 and not doExcl2):
                        break;
        
       

        print("Group size after merge: ", G1.number_of_nodes() + G2.number_of_nodes())
        if (G1.number_of_nodes() + G2.number_of_nodes()) > maxSize:
            print("Group too large after mincut. Abandoning merge")
            return False;

        excludedNodes = excl1 + excl2
        self.members = self.members + receiver.group.members;
        groupCollection.removeGroupByName(receiver.group.name)
        for n in self.members:
            n.group = self
       
        for l in excludedNodes:
            try:
                self.members.remove(l[0])
                gr = groupCollection.newGroup(l[0])
                if (len(l) <= 1):
                        continue;
                for n in l[1:]:
                    self.members.remove(n)
                    gr.members.append(n)
                    n.group = gr

            except ValueError:
                continue;
                
        self.dbiMinVal = minDbi;
        print("Mincut accepted")
        return True

    def buildNxGraph(self, minDbi):
        G = nx.Graph()
        for n in self.members:
            for m in self.members:
                if n == m:
                    continue
                rssi = n.rssiNeighbour(m)
                if (rssi == None):
                    continue
                if (rssi >= minDbi):
                    rssi = 99999;
                else:
                    rssi = 100 + rssi;
                G.add_edge(n, m, capacity=rssi)
        return G;


    def merge(self, node, initiator, dbi):
        global groupCollection
        global topology 
        global maxSize
        oldGr = node.group
        oldName = node.group.name
        oldMembers = node.group.members


        if (node.group.name == self.name):
            print("NODE", node.name, "of group", node.group, "wants to merge with", self.name, initiator.name)
            print("MEMBERS", self.members)
            sys.exit(0)

        if (len(self.members) + len(oldMembers) > maxSize): 
            if groupCollection.splitMethod == "none":
                return self.nosplit(node, initiator)
            elif groupCollection.splitMethod == "wagner":
                return self.wagner(node, initiator, dbi)
            elif groupCollection.splitMethod == "mincut":
                try:
                        if self.memoiser[oldGr.__hash__()] == self.__hash__():
                                print("Already tried to merge with group in same state");
                                return 0;
                except KeyError:
                        self.memoiser[oldGr.__hash__()] = self.__hash__()
                return self.mincut(node, initiator, dbi)
            elif groupCollection.splitMethod == "kmeans":
                return self.kmeans(node, initiator, dbi)

        self.members = self.members + oldMembers
        for n in self.members:
            n.group = self

        groupCollection.removeGroupByName(oldName)
        return 1
   
        

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

    def computeGroupCentroid(self):
        x = 0;
        y = 0;
        for node in self.members:
            x = x + node.x;
            y = y + node.y;
            
        return  np.array((math.ceil(x / len(self.members)),  math.ceil(y / len(self.members))))


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
