#!/usr/bin/env python3
from optparse import OptionParser
import numpy as np
import random
import math

#Global arguments
args = None

#Parse commandline arguments
def parseOptions():
    parser = OptionParser()
    #Width
    parser.add_option("-x", "--width", action="store", type="int",
            dest="width", default=100, help="Width of topology in meters. Default: 100")
    #Height
    parser.add_option("-y", "--height", action="store", type="int",
            dest="height", default=100, help="Height of topology in meters. Default: 100")
    #Spacing
    parser.add_option("-s", "--space", action="store", type="int",
            dest="spacing", default=10,
            help="Minimum spacing between nodes (access points). Default: 10")

    #Number of nodes
    parser.add_option("-n", "--nodes", action="store", type="int",
            dest="nodes", default=128, help="Number of nodes. Default: 128")

    return parser.parse_args()[0]

class Node:
    _ssid = None
    _channel = None
    _interfering = None
    
    def __str__(self):
        return "NODE"
    def __repr__(self):
        return "NODE"
    def __unicode__(self):
        return u"NODE"
class Topology: 
    _map = None
    _width = None
    _height = None
    _spacing = None
    _nodes = None
    _minimumRadiusVectors = None

    def __init__(self, width, height, spacing, nodes):
        self._width = width
        self._height = height
        self._spacing = spacing
        self._nodes = nodes
        self.initMap() 
        self.createMinimumRadiusVectors()
        self.populateMap()
    
    def initMap(self):
        topo = [[[] for i in range(self._height)] for i in range(self._width)]
        for y in range(len(topo)):
            for x in range(len(topo[y])):
                topo[y][x] = None
        self._map = topo
    
#TODO: Set node positions, node parameters. When all set
#Express attenuation formula, then create lists of most
#disturbing neighbours
    def populateMap(self): 
        for i in range(self._nodes): 
            while 1:
                y = random.randint(0, self._height - 1)
                x = random.randint(0, self._width - 1)
                if self.isPositionAvailable(x, y) == True:
                    print("X: ", x, " Y", y)
                    self._map[y][x] = Node()
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


def main(): 
    args = parseOptions()
    print("Width: ", args.width, " height: ", args.height, "spacing: ", args.spacing)
    topo = Topology(args.width, args.height, args.spacing, args.nodes)
    topo.printTopology()

if __name__ == "__main__":
    main()
