#!/usr/bin/env python3
from optparse import OptionParser
import numpy as np
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
    _ssid = None;
    _channel = None;
    _interfering = None;
    

def generateTopology(width, height, spacing, number):
    topo = [[[] for i in range(height)] for i in range(width)]
    for y in range(len(topo)):
        print(topo[y])
        #for x in len(topo[y]):
        #    print(topo[y][x])
        
    #topoMap = np.zeros((width, height));
    #for x in np.nditer(topoMap, op_flags=['readwrite']):
    #print(topoMap)
    


def main(): 
    args = parseOptions()
    print("Width: ", args.width, " height: ", args.height, "spacing: ", args.spacing)
    generateTopology(args.width, args.height, args.spacing, args.nodes)

if __name__ == "__main__":
    main()
