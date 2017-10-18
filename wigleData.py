#!/usr/bin/env python3
import json
import requests
import math
import GenerateTopology as gt
from optparse import OptionParser

data = {}
#Parse commandline arguments
def parseOptions():
    parser = OptionParser()
    #Width
            #dest="width", default=500, help="Width of topology in meters. Default: 100")
    parser.add_option("-o", "--output", action="store", type="string",
            dest="output", default="wigledata.json",
            help="Store data. Can be used for input later, to not to network requests for data")

    parser.add_option("-i", "--input", action="store", type="string", dest="input",
            help="Input file, data parsed with this program before, that is fetched from wigle")

    parser.add_option("-x", "--longstart", action="store", type=float, dest="xstart",
            help="Longitude measure startpoint.")

    parser.add_option("-y", "--latstart", action="store", type=float, dest="ystart",
            help="Latitude measure startpoint.")

    parser.add_option("-j", "--longstop", action="store", type=float, dest="xstop",
            help="Longitude measure endpoint.")

    parser.add_option("-k", "--latstop", action="store", type=float, dest="ystop",
            help="Latitude measure endpoint.")

    parser.add_option("-d", "--dbi", action="store", type=int, dest="dbi", default=-85,
            help="-dDi threshold. Min: -85")

    return parser.parse_args()[0]

def fetchWigle(filename, startLat, stopLat, startLong, stopLong):
    global data
    apiUser = 'AID9cf690d7e05df320686cc0c0ecd232f3'
    apiKey = '32eb0b0fbc6f292d2021ed6d27e63c4b'
    resultsPerPage= '100'
    offset = 0
    urlBase = 'https://api.wigle.net/api/v2/network/search?'
    data["startLat"] = startLat
    data["stopLat"] = stopLat 
    data["startLong"] = startLong
    data["stopLong"] = stopLong
    results = 100
    i = 0
    while(results == 100):
        print("Fetching AP data...")
        url = urlBase + "onlymine=false&first="+str(offset)+"&latrange1="+str(startLat)+"&latrange2="+str(stopLat)+"&longrange1="+str(startLong)+"&longrange2="+str(stopLong)+"&freenet=false&paynet=false&resultsPerPage="+resultsPerPage
        r = requests.get(url, auth=(apiUser, apiKey))
        data[str(i)] = r.json()
        try:
            offset += data[str(i)]['resultCount']
            results = data[str(i)]['resultCount']
        except KeyError:
            print(r.json())

        i += 1
        print("> Fetched", results, "access points. ")

    data["length"] = i + 1
    jsondata = json.dumps(data, indent=2)
    f = open("wigledata.json", "w")
    f.write(jsondata)
    f.close()
    print("** Fetched data about", 100 * (i - 1) + results, "access points.")

def distanceBetweenCoordinates(startLat, stopLat, startLong, stopLong):#
    dlon = math.radians(stopLong - startLong)
    dlat = math.radians(stopLat - startLat)
    a = (math.sin(dlat / 2))**2 + math.cos(math.radians(startLat)) * math.cos(math.radians(stopLat)) * (math.sin(dlon/2))**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)) 
    #Earth diameter in meters
    R = 6371000
    d = round(R * c)
    return d

def parseNodeCoordinates(startX, startY, data): 
    nodes = []
    for i in range(0, data["length"] - 1):
        dataField = data[str(i)]
        for field in dataField["results"]:
            lat = field['trilat']
            lon = field['trilong']
            x = distanceBetweenCoordinates(0, 0, startX, lon)
            y = distanceBetweenCoordinates(startY, lat, 0, 0)
            nodes.append({"x": x, "y" : y, "ssid" : field['ssid']})
    return nodes

def getMapSize(data): 
    startY = data["startLat"]
    stopY = data["stopLat"]
    startX = data["startLong"]
    stopX = data["stopLong"]
    y = distanceBetweenCoordinates(startY, stopY, 0, 0)
    x = distanceBetweenCoordinates(0, 0, startX, stopX)
    return x, y

def main():
    global data 
    parse = parseOptions() 
    if not parse.input:
        print("No data file input. Fetching data from coordinates.")
        try:
            fetchWigle(parse.output, parse.ystart, parse.ystop, parse.xstart, parse.xstop)
        except AttributeError:
            print("Error: missing coordinates. Stopping.")
            return
    else:
        data = json.loads(open(parse.input, "r").read())

    width, height = getMapSize(data) 
    nodes = parseNodeCoordinates(data["startLong"], data["startLat"], data)
    topo = gt.Topology(width, height, 10, 0, abs(parse.dbi), premadeNodes = nodes)
    topo.newTopology()
    topo.writeData("wigletopo.topo")

if __name__ == "__main__": 
    main()
