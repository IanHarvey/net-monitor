#!/usr/bin/env python

# Utility to read output from ping.py and plot results
# as a set of graphs on an HTML page.

# This code is placed in the public domain by its author, Ian Harvey.
# It comes with NO WARRANTY

import sys
import os
import time
import glob
import pickle
import site_config

from mkgraph import StdColors, Graph, TimeGraph, TimeSeries, LinearYAxis, LogYAxis

def getTargetName(ip,mac,default=None):
    if ip in site_config.known_ips:
        return site_config.known_ips[ip]
    if mac in site_config.known_macs:
        return site_config.known_macs[mac]
    return default
      
def getDataSeries(inputFile, lastSeen):
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
            name = getTargetName(ip,mac)
            if name != None:
                # Assume last one is at end of file!
                lastSeen[name]=timestr
    return allTargets
    

  
def writeGraph(target, series, outputFile):
    font = site_config.graph_font

    graph = ( TimeGraph( yAxis=LogYAxis(maxVal=1000.0, yPixPerDecade=50) )
              .hasOrigin(45, 220)
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

def cmpCaseless(first, second):
    return cmp(first.lower(), second.lower())

def lastSeenColour(name, lastSeen):
    if name not in lastSeen:
        return '"red"'
    gap = time.time() - time.mktime(lastSeen[name])
    if gap < 300.0:
        return '"green"'
    elif gap < 7200.0:
        return '"olive"'
    elif gap < 86500.0:
        return '"darkorange"'
    else:
        return '"red"'

def writeHtmlPage( filename, outlist, lastSeen ):
    print "Writing page", filename
    lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head><title>" + site_config.page_title + "</title>",
        site_config.stylesheet,
        "</head>",
        "<body>",
    ]

    lines += [
        '<h2>Last seen</h2>',
        '<table>'
        ]
    names = lastSeen.keys()
    names.sort(cmpCaseless)
    # Arrange into two columns
    fmt = "%H:%M:%S %d-%b-%y"
    cols = [ "<td>%s</td> <td bgcolor=%s>&nbsp; %s &nbsp;</td>" % 
            (name, lastSeenColour(name, lastSeen),
            time.strftime(fmt, lastSeen[name])) for name in names ]

    nrows = (len(cols)+1) / 2
    if len(cols) < 2*nrows:
        cols += [ "<td> </td> <td> </td>" ]
                
    for i in range(nrows):
        lines += [
            "<tr>",
             cols[i],
             cols[nrows+i],
            "</tr>"
        ]
    lines += [ "</table>" ]

    
    for (target, fname) in outlist:
        (ip,mac) = target.split("/")
        name = getTargetName(ip,mac,default=mac)
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

def updateLastSeen(seenToday, dateNow):
    try:
        with open(site_config.last_seen_file, "r") as f:
            lastSeen = pickle.load(f)
    except IOError as e:
        print "Cannot load", site_config.last_seen_file, ", error is", str(e)
        lastSeen = {}
    for (name, timestr) in seenToday.iteritems():
        lastSeen[name] = time.strptime( dateNow + timestr, "%Y%m%d%H%M%S" )
    with open(site_config.last_seen_file, "w") as f:
        pickle.dump(lastSeen, f)
    print "Updated", site_config.last_seen_file
    return lastSeen

if __name__ == '__main__':
   
    while True:
        args = { 'date' : time.strftime("%Y%m%d") }
        inputFile = site_config.input_file % args
        
        if not os.path.isfile(inputFile):
            print sys.argv[0], ': No files matching', inputFile
            time.sleep(10)
            continue

        print "Reading", inputFile
        seenToday = {}
        allData = getDataSeries(inputFile, seenToday)
        targets = allData.keys()
        targets.sort(cmpByIp)
        outlist = []
        for idx in range(len(targets)):
            fname = "ping-%05d.png" % idx
            target = targets[idx]
            writeGraph( target, allData[target], os.path.join(site_config.output_path,fname) )
            outlist += [ (target, fname) ]
        lastSeen = updateLastSeen(seenToday, args['date'])
        writeHtmlPage( os.path.join(site_config.output_path, site_config.page_name), outlist, lastSeen )
        time.sleep(site_config.graph_interval)

