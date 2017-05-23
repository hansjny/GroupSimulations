#!/usr/bin/env python3
from optparse import OptionParser
import numpy as np
import random
import math
import json
from collections import OrderedDict

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
    _freq = 0
    _constant  = -27.55
    _minimumInterference = 0
    group = None
    name = None
    x = 0
    y = 0

    def __init__(self, posx, posy, n, freq, thresh, name = None):
        self._neighbours = []
        self._minimumInterference = thresh*-1
        self.x = posx
        self.y = posy
        self._freq = freq
        if (name == None):
            self.name = "NODE" + str(n)
        else:
            self.name = name
        self._ssid = self.name

    def distanceTo(self, node):
        x = node.x - self.x
        y = node.y - self.y
        return math.sqrt(x**2+y**2)

    def getMostDisturbing(self):
        highest = -100
        nodeinfo = None
        for n in self._neighbours:
            if n["dbi"] > highest and n["obj"].group.name != self.group.name and not n["obj"].group.locked:
                nodeinfo = n
        return nodeinfo

    def getLeastDisturbingCompanion(self):
        lowest = 100
        nodeinfo = None
        for n in self._neighbours:
            if n["dbi"] < lowest and n["obj"].group.name == self.group.name:
                nodeinfo = n
        return nodeinfo

 
    def calculateInterferenceTo(self, nodeObject):
        if self == nodeObject:
            return
        dist = round(self.distanceTo(nodeObject))
        dBi  = self.measureDbi(dist)*-1
        if (dBi > self._minimumInterference):
            self._neighbours.append({"ssid": nodeObject._ssid, "dbi": dBi, "obj:": nodeObject})
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
    _map = None
    _width = None
    _height = None
    _spacing = None
    _nodes = []
    _nodesDict = {}
    _nodeCount = None
    _frequency = 2437
    _thresh = 0
    _minimumRadiusVectors = None

    def __init__(self, width, height, spacing, nodeCount, dbThresh):
        self._thresh = dbThresh
        self._width = width
        self._height = height
        self._spacing = spacing
        self._nodeCount = nodeCount

    def newTopology(self):
        self.initMap() 
        self.createMinimumRadiusVectors()
        self.populateMap()
        self.measureInterference()
    
    def getNodeCount(self):
        return self._nodeCount

    #def getNodeByName(self, name):
        #return self._nodesDict[name]
        #for n in self._nodes:
            #if n.name == name:
                #return n
        #return None
    
    def getNodes(self):
        return self._nodes;


    def initMap(self):
        topo = [[[] for i in range(self._height)] for i in range(self._width)]
        for y in range(len(topo)):
            for x in range(len(topo[y])):
                topo[y][x] = None
        self._map = topo

    def measureInterference(self):
        for nodeSubject in self._nodes:  
            for nodeObject in self._nodes:
                nodeSubject.calculateInterferenceTo(nodeObject) 

    def populateMap(self): 
        nodeCount = 0
        for i in range(self._nodeCount): 
            while 1:
                y = random.randint(0, self._height - 1)
                x = random.randint(0, self._width - 1)
                if self.isPositionAvailable(x, y) == True:
                    node =  Node(x, y, nodeCount, self._frequency, self._thresh)
                    self._map[y][x] = node
                    self._nodes.append(node)
                    nodeCount += 1
                    break

    def isPositionAvailable(self, testx, testy):
        for pos in self._minimumRadiusVectors:
            x = testx + pos[0]
            y = testy + pos[1]
            node = None
            try:
                node = self._map[y][x]
            except IndexError:
                node = None 

            if node != None:
                return False

        return True

    def createMinimumRadiusVectors(self):
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
        print("Data written to file", outfile)

def main(): 
    args = parseOptions()
    print("Width: ", args.width, " height: ", args.height, "spacing: ", args.spacing)
    topo = Topology(args.width, args.height, args.spacing, args.nodes, args.thresh)
    topo.newTopology()
    topo.writeData(args.output)
    #topo.printTopology()

if __name__ == "__main__":
    main()
