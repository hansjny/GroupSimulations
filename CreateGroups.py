#!/usr/bin/env python3
import json
import GenerateTopology as gt
import sys
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
        groupCollection.dumpGroups()
        input("Press enter to start simulation...") 
    
    def runIteration(self): 
        global groupCollection 
        i = 1
        while (groupCollection.iterateGroups() != 0):
            groupCollection.dumpGroups()
            jsonOutput["iterations"][i] = groupCollection.getOutput()
            i += 1
            input("Press enter to run next iteration...") 
        jsonOutput["iterationCount"] = i
        j = json.dumps(jsonOutput, indent=2)
        self.output.write(j)
        groupCollection.dumpGroups()
        

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
        print("Made new group: ", group.name, "for node", member.name)
        return group

    def appendGroup(self, group):
        self.groupCount += 1
        self.groups.append(group)
        self.groupDict[group.name] = group
    
    def iterateGroups(self):
        changes = 0
        print("Num groups", len(self.groups))
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
    def __init__(self, node, name):
        self.members = []
        self.members.append(node)
        self.name = name

    def merge(self, node):
        global topology 
        global groupCollection
        global maxSize
        print("Merging", node.group, "into", self.name)  
        if (node.group == self.name):
            print("NODE", node.name, "of group", node.group, "wants to merge with", self.name)
            print("MEMBERS", self.members)
            sys.exit(0)
        oldName = node.group.name
        oldMembers = node.group
        print("OLDMEMBERS", oldMembers.members)

        #Update group name for members
        for n in oldMembers.members:
            n.group = self

        #Extend this groups members with the other groups members
        self.members = self.members + oldMembers.members

        ##Remove old group
        groupCollection.removeGroupByName(oldName) 

        #If exceed MAXSIZE, start removal of members
        #if (len(self.members) > maxSize):
            #self.removeExcessMembers(maxSize)        
            #self.locked = True
        return 1
        
    def removeExcessMembers(self, maxSize):
        global groupCollection
        while (len(self.members) > maxSize):
            n = self.findLeastDisturbingMember()
            node = list(filter(lambda x: x.name == n.name, self.members))[0]
            self.members.remove(node)
            input();
            groupCollection.newGroup(node)
            print("REMOVING NODE", node.name, "FROM:", self.name)
            
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
        disturber = self.getMostDisturbing()
        ret = 0
        if disturber != None:
            ret = self.merge(disturber)
        else:
            print("No changes")
        return ret

    def getMostDisturbing(self):
        highest = -100
        disturber = None
        for n in self.members:
            node = n.getMostDisturbing()
            if node != None:
                gr = node["obj"].group
                if (node["dbi"] > highest and not gr.locked):
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
