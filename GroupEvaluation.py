#!/usr/bin/env python3
import sys
import matplotlib.pyplot as plt
import numpy as np

def dbKey(obj):
    return int(obj["dbi"])

class Evaluation:
    topology = None

    def __init__(self, t):
        self.topology = t

    def calculateGroupFitness(self, groups):
        self.accumulatedInterferences(groups)

    def accumulatedInterferences(self, groups): 
        """ Accumulate all interferences between nodes inside the group,
        and accumulate all interferences between nodes inside the group."""
        for group in groups:
                internal, external = self.getInternalAndExternalDbi(group)
                total = internal + external 
                if (total != 0):
                    print(internal / total, len(group.members))
                    plt.hist(internal/total)
        plt.show()



    def getInternalAndExternalDbi(self, group):
        internal = 0
        external = 0
        for node in group.members:
            for neighbour in node._neighbours:
                if group.name == neighbour["obj"].group.name:
                    internal += 100 - neighbour["dbi"]
                else: 
                    external += 100 - neighbour["dbi"]

        return internal, external






                


