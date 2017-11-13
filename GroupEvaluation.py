#!/usr/bin/env python3
import sys

def dbKey(obj):
    return int(obj["dbi"])

class Evaluation:
    topology = None

    def __init__(self, t):
        #print("Evaluation init")
        self.topology = t

        

    def prioritizeClosest(self):
        #Go through all nodes
        #Go through all neighbours of node
        #Find most disturbing. Share group? Penalty 0.
        #Not sharing group, find node N with highest disturbance that shares group
        #and penalize Ndisturbing + (mostDisturbing *-1)
        if 1 == 1:
            return 
        for n in self.topology._nodes:
            neighbs = sorted(n._neighbours, key=dbKey, reverse=True)
            nearest = self.topology._nodesDict[neighbs[0]["ssid"]]
            if (n.group.name == nearest.group.name):
                sys.stdout.write(".")
            else:
                sys.stdout.write("x")
            #for i in neighbs
               #neighbs[0]

