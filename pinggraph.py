#!/usr/bin/env python

# Utility to read output from ping.py and plot results
# as a set of graphs on an HTML page.

# This code is placed in the public domain by its author, Ian Harvey.
# It comes with NO WARRANTY

import sys
import os
import time
import glob
import site_config

from mkgraph import StdColors, Graph, TimeGraph, TimeSeries

      
def getDataSeries(inputFile):
    allTargets = {}
    with open(inputFile, "r") as infile:
        for line in infile:
            (timestr,ip,mac,delay) = line.rstrip().split(",")
            target = ip+"/"+mac
            series = allTargets.get(target)
            if series is None:
                series = TimeSeries()
                allTargets[target] = series
            series.addPoint(timestr, delay)
    return allTargets
    

  
def writeGraph(target, series, outputFile):
    font = site_config.graph_font

    graph = ( TimeGraph( yUnits=40, yPixPerUnit=5 )
              .hasOrigin(40, 220)
              .hasColors( StdColors )
              .hasStdDrawObject(640, 240)
              .hasTrueTypeFont( font, size=10 )
              .hasTitle( target +" generated at " + time.strftime("%d/%m/%Y %H:%M:%S") )
              .drawAxes()
              .plotSeriesAsBars(series, StdColors.data1)
              .drawTitle()
              .saveToDisk(outputFile)
            )
              
    print "Wrote", outputFile


def writeHtmlPage( filename, outlist ):
    print "Writing page", filename
    lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head><title>Beagleboard Network Survey</title>",
        site_config.stylesheet,
        "</head>",
        "<body>",
    ]
   
    for (target, fname) in outlist:
        (ip,mac) = target.split("/")
        if ip in site_config.known_ips:
            name = site_config.known_ips[ip]
        elif mac in site_config.known_macs:
            name = site_config.known_macs[mac]
        else:
            name = mac
        lines += [
            '<h2>%s (%s)</h2>' % (ip,name),
            '<p><img src="%s"></p>' % fname
        ]

    lines += [        
        "<hr>",
        "<p><i>Page generated at " + time.asctime() + "</i></p>",
        "</body>",
        "</html>",
        ""
    ]

    with open(filename, "w") as f:
        f.write("\n".join(lines))

def cmpByIp(first,second):
    (ip1,mac1) = first.split("/")
    (ip2,mac2) = second.split("/")
    nip1 = [ int(x) for x in ip1.split(".") ]
    nip2 = [ int(x) for x in ip2.split(".") ]
    return cmp( nip1 + [mac1], nip2 + [mac2] )
    
if __name__ == '__main__':
    
    while True:
        args = { 'date' : time.strftime("%Y%m%d") }
        inputFile = site_config.input_file % args
        
        if not os.path.isfile(inputFile):
            print sys.argv[0], ': No files matching', inputFile
            time.sleep(10)
            continue

        print "Reading", inputFile
        allData = getDataSeries(inputFile)
        targets = allData.keys()
        targets.sort(cmpByIp)
        outlist = []
        for idx in range(len(targets)):
            fname = "ping-%05d.png" % idx
            target = targets[idx]
            writeGraph( target, allData[target], os.path.join(site_config.output_path,fname) )
            outlist += [ (target, fname) ]
        writeHtmlPage( os.path.join(site_config.output_path, site_config.page_name), outlist )
        time.sleep(120)

