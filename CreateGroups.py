#!/usr/bin/env python3

import json
import GenerateTopology as gt
import sys
from collections import OrderedDict
from optparse import OptionParser


MAXSIZE = 128
topology = None
groupCollection = None

#Parse commandline arguments
def parseOptions():
    parser = OptionParser()
    #Width
    ##parser.add_option("-x", "--width", action="store", type="int",
            #dest="width", default=500, help="Width of topology in meters. Default: 100")
    parser.add_option("-f", "--file", action="store", type="string",
            dest="input", default="output.txt", help="Input filename, from GenerateTopology.py")
    parser.add_option("-o", "--output", action="store", type="string",
            dest="output", default="grouplog.json", help="Output file in Json.")

    return parser.parse_args()[0]

class Simulation:
    global topology
    output = None
    def __init__(self, outfile):
        global groupCollection
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

        groupCollection.writeOutput(self.output, 0)
        print("Number of groups created: ", groupCollection.size())
        groupCollection.dumpGroups()
        input("Press enter to start simulation...") 
    
    def runIteration(self): 
        global groupCollection 
        i = 1
        while (groupCollection.iterateGroups() != 0):
            groupCollection.dumpGroups()
            groupCollection.writeOutput(self.output, i)
            i += 1
            input("Press enter to run next iteration...") 
        groupCollection.dumpGroups()
        

class GroupCollection:
    groups = None
    groupDict = {}
    groupCount = 0

    def __init__(self):
        self.groups = []
           
    def size(self):
        return self.groupCount;
    
 #   1:
 #       1: groupName : GRUP
 #          members : { }
 
    def writeOutput(self, f, iteration):
        data = OrderedDict()
        data[iteration] = {}
        for i in range(len(self.groups)):
            data["iterationCount"] = iteration
            data[iteration]["groupCount"] = len(self.groups)
            data[iteration][i] = {}
            data[iteration][i]["groupName"] = self.groups[i].name 
            data[iteration][i]["memberCount"] = len(self.groups[i].members)
            data[iteration][i]["members"] = {}
            for n in range(len(self.groups[i].members)):
                data[iteration][i]["members"][n] = self.groups[i].members[n].name

        #print(data)
        j = json.dumps(data, indent=2)
        f.write(j)
        

    def dumpGroups(self):
        #return 
        for g in self.groups:
            print("#############################")
            print("GROUP ID:", g.name)
            for node in g.members:
                print("     >", node)


    def newGroup(self, member):
        group = "GROUP"+str(self.groupCount)
        self.appendGroup(Group(member, group)) 
        return group

    def appendGroup(self, group):
        self.groupCount += 1
        self.groups.append(group)
        self.groupDict[group.name] = group
    
    def iterateGroups(self):
        
        print("Num groups", len(self.groups))
        if len(self.groups) == 1:
            return 0
        
        for g in self.groups:
            g.iteration()
        return 1

    def removeGroupByName(self, name):
        if name in self.groupDict: del self.groupDict[name] 
        for g in self.groups:
            if name == g.name:
                self.groups.remove(g)
                break

class Group:
    members = None
    name = None
    def __init__(self, node, name):
        self.members = []
        node.group = name
        self.members.append(node)
        self.name = name

    def merge(self, node):
        global topology 
        global groupCollection
        print("Merging", node.group, "into", self.name)  
        if (node.group == self.name):
            print("NODE", node.name, "of group", node.group, "wants to merge with", self.name)
            print("MEMBERS", self.members)
            sys.exit(0)
        oldName = node.group
        oldMembers = groupCollection.groupDict[node.group]
        
        #Update group name for members
        for n in oldMembers.members:
            n.group = self.name

        #Extend this groups members with the other groups members
        self.members = self.members + oldMembers.members

        ##Remove old group
        groupCollection.removeGroupByName(oldName) 
        return 1
        
        #TODO: 
        #If exceed MAXSIZE, start removal of members

    def iteration(self):    
        disturber = self.getMostDisturbing()
        ret = 0
        if disturber != None:
            ret = self.merge(disturber)
        else:
            print("All done!")
        return ret

    def getMostDisturbing(self):
        highest = -100
        disturber = None
        for n in self.members:
            node = n.getMostDisturbing()
            if node != None:
                if (node["dbi"] > highest):
                    highest = node["dbi"]
                    disturber = node["obj"]
        return disturber

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
    args = parseOptions()
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
