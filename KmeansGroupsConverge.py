#!/usr/bin/env python3
import json
import GenerateTopology as gt
import sys
import math
import numpy as np
from collections import OrderedDict
from optparse import OptionParser

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

    return parser.parse_args()[0]

class Simulation:
    global topology
    output = None
    def __init__(self, outfile):
        global groupCollection
        global jsonOutput
        jsonOutput = OrderedDict()
        jsonOutput["iterations"] = {}

        self.output = outfile
        groupCollection = GroupCollection()
    
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
        print("Number of groups created: ", groupCollection.size())
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
        print("Writing to group iterations to file...")
        #groupCollection.dumpGroups()
        

class GroupCollection:
    groups = None
    groupDict = {}
    groupCount = 0

    def __init__(self):
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
        return group

    def appendGroup(self, group):
        self.groupCount += 1
        self.groups.append(group)
        self.groupDict[group.name] = group
    
    def iterateGroups(self):
        changes = 0
        #print("Num groups", len(self.groups))
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
    locked = False
    merges = 500
    def __init__(self, node, name):
        self.members = []
        self.members.append(node)
        self.name = name

    def merge(self, node, initiator):
        global topology 
        global groupCollection
        global maxSize
        #print("Merging", node.group.name, "into", self.name)  
        if (node.group.name == self.name):
            print("NODE", node.name, "of group", node.group, "wants to merge with itself", self.name, initiator.name)
            print("Error... exiting!")
            sys.exit(0)

        oldName = node.group.name
        oldMembers = node.group.members

        #If exceed MAXSIZE, start removal of members
        #Split algorithm
        if (len(self.members) + len(oldMembers) > maxSize):
            if (self.merges <= 1):
                return 0
            point1 = initiator
            point2 = node
            #self.KmeansSplit((initiator.x, initiator.y), (node.x, node.y))
            split = self.KmeansSplit((point1.x, point1.y), (point2.x, point2.y), self.members, oldMembers)
            if split == 0: 
                return 0
            groupCollection.removeGroupByName(oldName) 
            self.merges = self.merges - 1
            print("MERGES", self.merges)
        else:
            for n in oldMembers:
                n.group = self
            #print("Setting group for", n.name, "to", self.name)
            self.members = self.members + oldMembers
            groupCollection.removeGroupByName(oldName) 

        return 1
        

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
    def KmeansSplit(self, point1, point2, origGroup1, origGroup2): 
        global GroupCollection
        old = [(0,0), (0,0)]
        mu = [point1, point2]
        groups = (origGroup1 + origGroup2, [])
        while not mu == old:
            groups = self.assignGroups(mu, groups)
            old = mu;
            mu = self.computeMu(groups, mu)
    
        originalMu = self.computeMu([origGroup1, origGroup2])

        newDist1 = self.nodeClosestToPoint(groups[0], mu[1])
        newDist2 = self.nodeClosestToPoint(groups[1], mu[0])
        oldDist1 = self.nodeClosestToPoint(origGroup1, point2)
        oldDist2 = self.nodeClosestToPoint(origGroup2, point1)
         
        newDistSum = newDist1 + newDist2
        oldDistSum = oldDist1 + oldDist2
        if (newDistSum + 100 < oldDistSum):
            return 0

        try:
            newGroup = groupCollection.newGroup(groups[1][0])
            newGroup.merges = self.merges - 1
        except IndexError:
            return 0

        for node in groups[1]:
            if node in self.members:
                self.members.remove(node)
            newGroup.members.append(node)
            node.group = newGroup
        for node in groups[0]:
            if node not in self.members:
                node.group = self
                self.members.append(node)
        return 1

    def computeMu(self, groups, oldMu = [(0,0), (0,0)]):
        newMu = []
        arrayVals = [[], []]
        for g in range(0, len(oldMu)):
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

    def nodeClosestToPoint(self, group, point):
        dist = 0
        node = 0
        for n in group:
            d = self.distanceToPoint((n.x, n.y), point)
            if d > dist:
                dist = d
                node = n
        return dist

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
            ret = self.merge(disturber, initiator)
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
        
    topo._nodes = nodes;

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
    s = Simulation(outfile)
    s.start()
    outfile.close()

if __name__ == "__main__":
    main()
