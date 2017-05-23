#!/usr/bin/env python3
from optparse import OptionParser
import codecs
parser = OptionParser()
parser.add_option("-f", "--file", action="store", type=str, dest="inputFile", help="Input file")
(options, args) = parser.parse_args()

if not options.inputFile:
    parser.error("No filename given.")

def parseDBF(f):
    datalines = []
    raw = f.read().split()
    tmp = []
    for elem in raw:
        if (len(tmp) == 7):
            datalines.append(tmp)
            tmp = []
        if elem.isdigit():
            tmp.append(elem)
    for i in datalines:
        input("next")
        print(i)

def main():
    with codecs.open(options.inputFile, "r",encoding='utf-8', errors='ignore') as data:
        parseDBF(data) 

if __name__ == "__main__":
    main()
