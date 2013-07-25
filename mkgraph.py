#!/usr/bin/env python

import sys
import os
import time
import glob
import math
import Image, ImageDraw, ImageFont
import array

modeRGB = "RGB"

class StdColors:
    background = (255, 255, 224)

    axes = (0, 0, 0)
    xgrid = (255, 255, 224)
    ygrid = (224, 224, 224)
    yminor =(240, 240, 224)
    data1 = (64, 64, 128)
    data2 = (255, 64, 64)
    data3 = (64, 255, 64)
    title = (255, 0, 0)

class LinearYAxis:
    def __init__(self, yUnits=1, yPixPerUnit=100):
        self.yUnits      = yUnits
        self.yPixPerUnit = yPixPerUnit
        self.yTotal = int(yUnits * yPixPerUnit)
    
    def getHeight(self):
        return self.yTotal

    def yLabel(self, y):
        '''This can be overridden in a subclass if needed'''
        if ((y%10)==0):
            return "%02d" % y
        else:
            return ""
            
    def scaleY(self, value):
        return int ( self.yPixPerUnit * value )

    def draw(self, graph):
        # Axis itself
        graph.draw.line( [ (graph.originX, graph.originY), (graph.originX, graph.originY-self.yTotal-1) ] , fill=graph.colors.axes)
        # Axis ticks and labels
        for i in range(0, self.yUnits+1):
            x = graph.originX
            y = graph.originY - (i*self.yPixPerUnit)
            graph.draw.line( [ (x,y), (x-5, y) ], fill = graph.colors.axes )
            graph.draw.text( (x-20, y-5), self.yLabel(i), fill = graph.colors.axes )
            if (i != 0) and ( i % 10 ) == 0:
                graph.draw.line( [ (x+1,y), (x+graph.xTotal, y) ], fill = graph.colors.ygrid ) 

class LogYAxis:
    def __init__(self, maxVal = 1.0, decades=4, yPixPerDecade=100, lowerMarginPix=5):
        self.minVal       = maxVal / math.pow(10.0, decades)
        self.lowerMargin  = lowerMarginPix
        self.decades      = int(decades)
        self.yPixPerDecade= yPixPerDecade
        self.yTotal = int(decades * yPixPerDecade + lowerMarginPix)
    
    def getHeight(self):
        return self.yTotal

    def yLabel(self, y):
        return "%.1f" % y
            
    def scaleY(self, value):
        if (value < self.minVal):
            return self.lowerMargin
        else:
            return self.lowerMargin + int( self.yPixPerDecade * math.log10(value/self.minVal) )

    def draw(self, graph):
        # Axis itself
        graph.draw.line( [ (graph.originX, graph.originY), (graph.originX, graph.originY-self.yTotal-1) ] , fill=graph.colors.axes)
        # Axis labels
        for i in range(0, self.decades+1):
            x = graph.originX
            val = self.minVal * math.pow(10.0, i)
            y = graph.originY - self.scaleY(val)
            graph.draw.line( [ (x,y), (x-5, y) ], fill = graph.colors.axes )
            graph.draw.text( (x-40, y-5), self.yLabel(val), fill = graph.colors.axes )
            graph.draw.line( [ (x+1,y), (x+graph.xTotal, y) ], fill = graph.colors.ygrid ) 
            # Axis ticks
            if i < self.decades:
                for j in range(2,10):
                    y = graph.originY - self.scaleY(val * j)
                    graph.draw.line( [ (x,y), (x+graph.xTotal, y) ], fill = graph.colors.yminor )
                    graph.draw.line( [ (x,y), (x-5, y) ], fill = graph.colors.axes )
        
class Graph:
    def __init__(self, xUnits=1, xPixPerUnit=100, yAxis = None):
        self.xUnits      = xUnits
        self.xPixPerUnit = xPixPerUnit
        self.xTotal = int(xUnits * xPixPerUnit)

        if yAxis != None:
            self.yAxis = yAxis
        else:
            self.yAxis = LinearYAxis()
            
        self.colors = StdColors

    def hasOrigin(self, x, y):
        self.originX = x
        self.originY = y
        return self
        
    def hasTextFont(self, font):
        self.font = font
        return self

    def hasDrawObject(self, draw):
        self.draw = draw
        return self

    def hasStdDrawObject(self, xSize, ySize):
        self.img = Image.new(modeRGB, (xSize, ySize), self.colors.background)
        self.hasDrawObject(ImageDraw.Draw(self.img))
        return self

    def hasColors(self, colors):
        self.colors = colors
        return self

    def hasTrueTypeFont(self, fontfile, size, encoding="unic"):
        self.hasTextFont( ImageFont.truetype(fontfile, size=size, encoding=encoding) )
        return self
        
    def hasTitle(self, title):
        self.title = title
        return self

    def xLabel (self, x):
        '''Typically overridden in a subclass, to get different label style'''
        return str(x)

    def drawXAxis(self):
        yTotal = self.yAxis.getHeight()
        # Axis itself
        self.draw.line( [ (self.originX, self.originY), (self.originX+self.xTotal+1, self.originY) ] , fill=self.colors.axes)
        # Axis ticks and labels
        for i in range(0, self.xUnits+1):
            x = self.originX + (i*self.xPixPerUnit)
            y = self.originY
            self.draw.line( [ (x,y), (x, y+5) ], fill = self.colors.axes )
            self.draw.text( (x-10, y+7), self.xLabel(i), fill = self.colors.axes )
            if (i != 0) and ( i % 10 ) == 0:
                self.draw.line( [ (x,y-1), (x, y-yTotal) ], fill = self.colors.xgrid ) 
            
    def drawAxes(self):
        self.drawXAxis()
        self.yAxis.draw(self)
        return self
        
    def drawTitle(self):
        self.draw.text( [ self.originX + 10, 5], self.title, fill = self.colors.title )
        return self
        
    def drawDataAsBars(self, color):
        for (pX,pY) in self.generateData():
            if pY != None:
                self.draw.line( [ self.originX+pX, self.originY-1, self.originX+pX, self.originY-pY], fill=color )
        return self
            

    def drawDataAsLine(self, color):
        yTotal = self.yAxis.getHeight()
        points = []
        for (pX,pY) in self.generateData():
            if pY != None:
                if pY > yTotal:
                    pY = yTotal
                points.append( (self.originX+pX, self.originY-pY) )
            elif len(points) > 0:
                self.draw.line(points, fill=color)
                points = []
        if len(points) > 0:
            self.draw.line(points, fill=color)
        return self

    def generateData(self):
        # Should return a list of (x,y) points for the graph
        return []

    def saveToDisk(self, filename):
        self.img.save(filename)
        return self


class TimeSeries:
    def __init__(self, countsPerHour=22.0):
        self.countsPerHour = countsPerHour
        self.length = int(countsPerHour*24)
        self.counts = array.array('I', [0]*self.length)
        self.totals = array.array('d', [0.0]*self.length)

    def addPoint(self, timestr, datum):
        assert(len(timestr)==6)
        timeHours = float(timestr[0:2]) + (float(timestr[2:4])/60.0) + float(timestr[4:6])/3600.0
        timeIndex = int(timeHours * self.countsPerHour)
        if timeIndex > self.length:
            raise ValueError("Illegal time string" + repr(timestr))
        self.counts[timeIndex] += 1
        self.totals[timeIndex] += float(datum)
                
class TimeGraph(Graph):
    def __init__(self, xUnits=24, xPixPerUnit=22, yAxis=None):
        Graph.__init__(self, xUnits, xPixPerUnit, yAxis)
        self.plotSeries=[]
        
    def xLabel(self, x):
        if ((x%2)==0):
            return "%2d00" % x
        else:
            return ""

    def plotSeriesAsBars(self, series, color):
        self.plotSeries = series
        return self.drawDataAsBars(color)
             
    def plotSeriesAsLine(self, series, color):
        self.plotSeries = series
        return self.drawDataAsLine(color)
                
    def generateData(self):
        s = self.plotSeries
        assert(s.length==self.xTotal)
        for pX in range(s.length):
            if s.counts[pX]==0:
                yield (pX, None)
            else:
                yield (pX, self.yAxis.scaleY(s.totals[pX] / s.counts[pX]))

