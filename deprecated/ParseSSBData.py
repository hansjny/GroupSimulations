#!/usr/bin/env python3
#62 18'11.0"N 10 41'21.8"Ø - x 62 14'46.7"N 10 51'17.8"Ø
from optparse import OptionParser
import codecs
import GenerateTopology as gt
import random
parser = OptionParser()
parser.add_option("-f", "--file", action="store", type=str, dest="inputFile", help="Input file")
(options, args) = parser.parse_args()

if not options.inputFile:
    parser.error("No filename given.")

def getDBFLines(raw):
    datalines = []
    tmp = []
    for elem in raw:
        if (len(tmp) == 7):
            datalines.append(tmp)
            tmp = []
        if elem.isdigit():
            tmp.append(elem)
    return datalines

def parseDBF(f, cellsize):
    raw = f.read().split()
    datalines = getDBFLines(raw)
    nodes = []
    listx = []
    listy = []
    count = 0
    for line in datalines: 
        listx.append(int(line[4]))
        listy.append(int(line[5]))
        count += int(line[6])

    for line in datalines: 
        cell = [[[] for i in range(cellsize)] for i in range(cellsize)]
        nodesx = int(line[4]) - min(listx)
        nodesy = int(line[5]) - min(listy)
        nodeC  = int(line[6])
        print (line)
        for i in range(0, nodeC):
            isBreak = True
            while(isBreak):
                x = random.randint(0, cellsize - 1)
                y = random.randint(0, cellsize - 1)
                node = cell[x][y]
                if (node == []):
                    cell[x][y] = "Occupied"
                    nodes.append({"x": nodesx + x, "y": nodesy + y})
                    isBreak = False
    print(nodes)
    input("..")
    sizex = max(listx) - min(listx)
    sizey = max(listy) - min(listy)
    print("Num nodes", len(nodes))
    topo = gt.Topology(sizex, sizey, 10, 0, 95, nodes)
    topo.newTopology()
    topo.writeData("testdata.topo")
                    
def main():
    cellsize = 100
    with codecs.open(options.inputFile, "r",encoding='utf-8', errors='ignore') as data:
        parseDBF(data, cellsize) 

if __name__ == "__main__":
    main()
