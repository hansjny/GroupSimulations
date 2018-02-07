#!/usr/bin/env python3
from optparse import OptionParser
import numpy as np
import random
import math
import sys
import json
from collections import OrderedDict
import networkx as nx 
#Global arguments
args = None

#Parse commandline arguments
def parseOptions():
    parser = OptionParser()
    #Width
    parser.add_option("-x", "--width", action="store", type="int",
            dest="width", default=500, help="Width of topology in meters. Default: 100")
    #Height
    parser.add_option("-y", "--height", action="store", type="int",
            dest="height", default=500, help="Height of topology in meters. Default: 100")
    #Spacing
    parser.add_option("-s", "--space", action="store", type="int",
            dest="spacing", default=10,
            help="Minimum spacing between nodes (access points). Default: 10")

    #Number of nodes
    parser.add_option("-n", "--nodes", action="store", type="int",
            dest="nodes", default=128, help="Number of nodes. Default: 128")

    parser.add_option("-o", "--output", action="store", type="string",
            dest="output", default="topology.json", help="Output filename")

    parser.add_option("-d", "--dbithresh", action="store", type="int",
            dest="thresh", default=87, help="Absolute value. Threshold to consider neighbours non-interfering")

    return parser.parse_args()[0]

class Node:
    _ssid = None
    _channel = None
    _neighbours = None
    gg_neighbourMembers = None
    _freq = 0
    _constant  = -27.55
    _minimumInterference = 0
    group = None
    name = None
    x = 0
    y = 0

    def __init__(self, posx, posy, n, freq, thresh, name = None):
        self._neighbours = []
        #Data structure 
        self.edges = {}
        self._minimumInterference = thresh*-1
        self.x = posx
        self.y = posy
        self._freq = freq
        if (name == None):
            self.name = "NODE" + str(n)
        else:
            self.name = name
        self._ssid = self.name

    def __hash__(self):
        return hash(self.name)

    #def __eq__(self, other):
        #return self.name == other.name

    def rssiNeighbour(self, node):
        for n in self._neighbours:
            if n["ssid"] == node.name:
                return n["dbi"]
        return None
            
    def distanceTo(self, node):
        x = node.x - self.x
        y = node.y - self.y
        return math.sqrt(x**2+y**2)

    def getNeighbourCount(self):
        return len(self._neighbours)

    def getMostDisturbing(self, nodeList=None):
        highest = -100
        nodeinfo = None

        if nodeList == None:
            for n in self._neighbours:
                if n["dbi"] > highest and n["obj"].group.name != self.group.name and not n["obj"].group.locked:
                    nodeinfo = n
                    highest = n["dbi"]
        else:
            for n in self._neighbours:
                if n["dbi"] > highest and n["obj"] not in nodeList and not n["obj"].group.locked:
                    nodeinfo = n
                    highest = n["dbi"]
        return nodeinfo


    def getLeastDisturbingCompanion(self):
        lowest = 100
        nodeinfo = None
        for n in self._neighbours:
            if n["dbi"] < lowest and n["obj"].group.name == self.group.name:
                lowest = n["dbi"]
                nodeinfo = n
        return nodeinfo


    def getDBSum(self):
        sum = 0;
        for n in self._neighbours:
            sum += n["dbi"]
        return sum

    def calculateInterferenceTo(self, nodeObject):
        if self == nodeObject:
            return None
        dist = round(self.distanceTo(nodeObject))
        if (dist == 0):
            dBi = -40
        else:
            dBi  = self.measureDbi(dist)*-1
        if (dBi > self._minimumInterference):
            self._neighbours.append({"ssid": nodeObject._ssid, "dbi": dBi, "obj:": nodeObject})
        return dBi
            #print("Distance:", dist, "m,  dBi:", dBi)

    def getData(self):
        data = OrderedDict()
        data.update(posX = self.x)
        data.update(posY = self.y)
        data.update(frequency = self._freq)
        data.update(ssid = self.name)
        data.update(neighbourCount = len(self._neighbours))
        data.update(neighbours = {})
        for i in range(len(self._neighbours)):
            data["neighbours"].update({i : {"ssid" : self._neighbours[i]["ssid"],
                                            "dbi" : self._neighbours[i]["dbi"]}})
        return data

    def measureDbi(self, dist):
        return (20 * math.log(self._freq, 10)) + (20 * math.log(dist, 10)) + self._constant

    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name
    def __unicode__(self):
        return self.name

class Topology: 
    _map = {}
    _width = None
    _height = None
    _spacing = None
    _nodes = []
    _nodesDict = {}
    _nodeCount = 0
    _frequency = 2437
    _thresh = 0
    _minimumRadiusVectors = None
    premadeNodes = None

    def __init__(self, width, height, spacing, nodeCount, dbThresh, premadeNodes = None):
        self._thresh = dbThresh
        self._width = width
        self._height = height
        self._spacing = spacing
        self.premadeNodes = premadeNodes
        if (premadeNodes != None):
            self._nodeCount = len(premadeNodes)
        else:
            self._nodeCount = nodeCount

    def newTopology(self):
        #self.initMap() 
        self.createMinimumRadiusVectors()
        self.populateMap()
        self.measureInterference()
    
    def getNodeCount(self):
        return self._nodeCount

    def getNodes(self):
        return self._nodes;

    def initMap(self):
        print("Generated topo")
        print("Generated filled topo with None objects")

    def measureInterference(self):
        print("> Calculating interference between all nodes.")
        i = 0
        printPercentage = 5
        percentageMark = len(self._nodes) / (100 / 5)

        for nodeSubject in self._nodes:  
            if (i % percentageMark == 0):
                print(" *", i, "of", len(self._nodes), "nodes done.")
            for nodeObject in self._nodes:
                nodeSubject.calculateInterferenceTo(nodeObject) 
            i += 1
     

    def createNode(self, posx, posy, nodeNumber, nodeFreq, nodeDbiThresh, name=None):
        node =  Node(posx, posy, nodeNumber, nodeFreq, nodeDbiThresh, name=name)
        try: 
            self._map[posy][posx] = node
        except KeyError:
            self._map[posy] = {}
            self._map[posy][posx] = node

        self._nodes.append(node)

    def generateRandomNodes(self):
        nodeCount = 0
        for i in range(self._nodeCount): 
            while 1:
                y = random.randint(0, self._height - 1)
                x = random.randint(0, self._width - 1)
                if self.isPositionAvailable(x, y) == True:
                    self.createNode(x, y, nodeCount, self._frequency, self._thresh)
                    nodeCount += 1
                    break

    def placeExistingNodes(self):
        nodeCount = 0
        print("> Placing nodes in topology.")
        for n in self.premadeNodes:
            self.createNode(n['x'], n['y'], nodeCount, self._frequency, self._thresh)
            nodeCount += 1

        print("> Nodes placed.")

    def populateMap(self): 
        if self.premadeNodes == None:
            self.generateRandomNodes()
        else:
            self.placeExistingNodes()
         
    def isPositionAvailable(self, testx, testy):
        for pos in self._minimumRadiusVectors:
            x = testx + pos[0]
            y = testy + pos[1]
            node = None
            try:
                node = self._map[y][x]
            except KeyError:
                return True

        return False

    def createMinimumRadiusVectors(self):
        """Creates a list of relative positions to a node, where
        no other node can be placed because of the minimum spacing
        between nodes."""
        positions = []
        for i in range(-self._spacing, self._spacing + 1):
            for j in range(-self._spacing, self._spacing + 1): 
                dist = math.sqrt(i**2+j**2)
                if dist <=  self._spacing:
                    positions.append((i, j))
        self._minimumRadiusVectors = positions

    def printTopology(self):
        for y in range(len(self._map)):
            print(self._map[y])

    def writeData(self, outfile):
        data  = OrderedDict()
        data.update(mapWidth = self._width)
        data.update(mapHeight = self._height)
        data.update(nodeCount = self._nodeCount)

        allnodes = {}
        for i in range(self._nodeCount):
            allnodes.update({i : self._nodes[i].getData()})

        data.update(nodes = allnodes)
        j = json.dumps(data, indent=2) 
        f = open(outfile, "w")
        f.write(j)
        f.close()
        print("> Topology data written to file: ", outfile)

def main(): 
    args = parseOptions()
    print("Width: ", args.width, " height: ", args.height, "spacing: ", args.spacing)
    topo = Topology(args.width, args.height, args.spacing, args.nodes, args.thresh)
    topo.newTopology()
    topo.writeData(args.output)

if __name__ == "__main__":
    main()
