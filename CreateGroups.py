#!/usr/bin/env python3

import json
import GenerateTopology as gt
from optparse import OptionParser

MAXSIZE = 128
topology = None
#Parse commandline arguments
def parseOptions():
    parser = OptionParser()
    #Width
    ##parser.add_option("-x", "--width", action="store", type="int",
            #dest="width", default=500, help="Width of topology in meters. Default: 100")
    parser.add_option("-f", "--file", action="store", type="string",
            dest="input", default="output.txt", help="Input filename, from GenerateTopology")
    return parser.parse_args()[0]

class Simulation:
    global topology
    groupCollection = None;
    def __init__(self, topo):
        self.groupCollection = GroupCollection()
    
    def start(self):
        self.initiateGroups()
        self.runIteration()

    #Create one group for each node as initiation
    def initiateGroups(self):
        for node in topology.getNodes():
            node.group = self.groupCollection.newGroup(node)
        print("Groups created: ", self.groupCollection.size())
    
    def runIteration(self):
        self.groupCollection.iterateGroups()

class GroupCollection:
    groups = None
    groupCount = 0
    def __init__(self):
        self.groups = []
           
    def size(self):
        return self.groupCount;

    def newGroup(self, member):
        group = "GROUP"+str(self.groupCount)
        self.appendGroup(Group(member, group)) 
        return group

    def appendGroup(self, group):
        self.groupCount += 1
        self.groups.append(group)
    
    def iterateGroups(self):
        for g in self.groups:
            g.iteration()

class Group:
    global topology
    members = None
    name = None
    def __init__(self, node, name):
        self.members = []
        node.group = name
        self.members.append(node)
        self.name = name

    def merge(self, nodename):
        node = topology.getNodeByName(nodename)
        print(node.group)
        
        #TODO: 
        #If exceed MAXSIZE, start removal of members

    def iteration(self):
        
        disturber = self.getMostDisturbing()
        if disturber != None:
            self.merge(disturber)
            #print("Disturbs most", disturber)

        #TODO:
        #Merge groups of disturbers
        #Remove old groups

        return

    def getMostDisturbing(self):
        highest = -100
        name = None
        for n in self.members:
            node = n.getMostDisturbing()
            if node != None:
                if (node["dbi"] > highest):
                    highest = node["dbi"]
                    name = node["ssid"]
        return name


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
        
    topo._nodes = nodes;
    return topo
    
def main():
    global topology
    args = parseOptions()
    infile = open(args.input, "r")
    cont = infile.read()
    topoDict = json.loads(cont)
    topology = getTopoData(topoDict)
    s = Simulation(topology)
    s.start()

if __name__ == "__main__":
    main()
