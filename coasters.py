#!/usr/bin/env python

# this program was used to make coasters for Carl's wedding
#  the interesting trick here was that text that was placed on the coaster
#  was rotated to curve along the coaster. 

import rhinoscriptsyntax as rs
import Rhino
import glob
import string
import random
import math
import os
import sys
import time
import re
from math import sqrt

class Thing:
    def __init__(self):
        self.radius = 1.8
        self.border = .2
        self.bump = .5

    def MakeBorders(self, objs, layer):
        borders = []

        for obj in objs:
            if rs.IsSurface(obj):
                ids = rs.DuplicateSurfaceBorder(obj, type=0)
                if ids:
                    for id in ids:
                        id = rs.ConvertCurveToPolyline(id, min_edge_length = .01, delete_input=True)
                        borders.append(id)
                        rs.ObjectLayer(id, layer)
                rs.DeleteObjects(obj)
        return borders


    def GetBoxFromObjects(self, objs):
        minX = 9999999.0
        maxX = -9999999.0
        minY = 9999999.0
        maxY = -9999999.0

        for id in objs:
            box = rs.BoundingBox(id)
            for point in box:
                if (point[0] < minX):
                    minX = point[0]
                if (point[0] > maxX):
                    maxX = point[0]
                if (point[1] < minY):
                    minY = point[1]
                if (point[1] > maxY):
                    maxY = point[1]

        midX = ((maxX - minX) / 2) + minX
        midY = ((maxY - minY) / 2) + minY
        return(minX, minY, maxX, maxY, midX, midY)

    def GetBoxFromObject(self, obj):
        minX = 9999999.0
        maxX = -9999999.0
        minY = 9999999.0
        maxY = -9999999.0

        box = rs.BoundingBox(obj)
        for point in box:
            if (point[0] < minX):
                minX = point[0]
            if (point[0] > maxX):
                maxX = point[0]
            if (point[1] < minY):
                minY = point[1]
            if (point[1] > maxY):
                maxY = point[1]
        midX = ((maxX - minX) / 2) + minX
        midY = ((maxY - minY) / 2) + minY
        return(minX, minY, maxX, maxY, midX, midY)


    def AddLine(self, pts, layer):
        id = rs.AddPolyline(pts)
        rs.ObjectLayer(id, layer)
        return(id)

    def GetDistances(self, string):
        return distances

        
    def AddTextToCircle(self, textstring, radius, final_dest, final_angle, layer):

        commandString = "-_TextObject _Height=.18 _FontName=\"Batang\" _Output=_Surfaces " + "\"" + textstring + "\"" + " 0,0,0 _Enter"
        rs.Command(commandString)
        objs = rs.LastCreatedObjects()

        # center the thing
        (minX, minY, maxX, maxY, midX, midY) = self.GetBoxFromObjects(objs)
        # and move to bottom of circle
        y_pos = (radius * -1) + self.border
        rs.MoveObjects(objs, rs.VectorSubtract((0, y_pos, 0), (midX, 0, 0)))

        tuples = []
        count = 0
        for obj in objs:
            (minX, minY, maxX, maxY, midX, midY) = self.GetBoxFromObject(obj)
            tuples.append([count, minX])
            count += 1

        # sort left to right
        distances = []
        for tup in sorted(tuples, key=lambda s : s[1]):
            distances.append((objs[tup[0]], tup[1]))

        center = (0,0,0)
        for obj, d in distances:
            (minX, minY, maxX, maxY, midX, midY) = self.GetBoxFromObject(obj)
            # move from current position to right in the middle
            rs.MoveObject(obj, rs.VectorSubtract((0, midY, 0), (minX, midY, 0)))
            pt = self.PointAlongCircleByDistance((0,y_pos,0), d)
            angle = rs.Angle2((center, pt), (center, (0,y_pos,0)))
            # print d, " :: ", angle
            if d < 0:
                rs.RotateObject(obj, center, angle[0] * -1)
            else:
                rs.RotateObject(obj, center, angle[0])

            rs.RotateObject(obj, center, final_angle)
            rs.MoveObject(obj, rs.VectorSubtract(final_dest, center))
            
        return self.MakeBorders(objs, layer)
    
    # terrible implementation, not generalized
    def PointAlongCircleByDistance(self, pt, dis):
        c1 = rs.AddCircle((0,0,0), self.radius - self.border)
        c2 = rs.AddCircle(pt, abs(dis))
        isx = rs.CurveCurveIntersection(c1, c2)
        rs.DeleteObject(c1)
        rs.DeleteObject(c2)
        if isx is None:
            return
        else:
            pt = isx[0][1]
            return (abs(pt[0]), pt[1], pt[2])

    def RemoveParts(self, objs):
        rs.DeleteObjects(objs)

    def _boolean(self, value):
        if value == "True":
            return True
        if value == "False":
            return False

    def Str2Array(self, s):
        return(tuple(int(i) for i in s.split(',')))


if __name__ == '__main__':
    g = Thing()
    
    name_file = '/Users/owhite/Documents/names.txt'
 
    rows = []
    for line in open(name_file,'r'):
        line = line.replace('\n', '')
        rows.append(line)

    countX = 0
    countY = 0
    for name in rows:
        o1 =  rs.CopyObjects(rs.BlockObjects("MyBlock"), (0,0,0))
        o2 = g.AddTextToCircle(name, g.radius, (0,0,0), 90, "Default")
        objs = o1 + o2

        x = countX * ((g.radius * 2) + g.bump)
        y = countY * ((g.radius * 2) + g.bump)

        rs.MoveObjects(objs, rs.VectorSubtract((x, y, 0), (0, 0, 0)))

        countY += 1

        if countY > 4:
            countY = 0
            countX += 1
