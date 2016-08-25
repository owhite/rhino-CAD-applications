#!/usr/bin/env python

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
    def __init__(self, FileName):
        self.ini_file = FileName
        self.name_file = rs.GetSettings(FileName, 'GCODE', 'name_file')

        self.cardX = 3.5
        self.cardY = 2
        self.border = .35
        self.bump = .75


    def MakeBorders(self, objs):
        borders = []

        for obj in objs:
            if rs.IsSurface(obj):
                ids = rs.DuplicateSurfaceBorder(obj, type=0)
                if ids:
                    for id in ids:
                        id = rs.ConvertCurveToPolyline(id, min_edge_length = .01, delete_input=True)
                        borders.append(id)
                        rs.ObjectLayer(id, "PARTS")
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
        return(minX, minY, maxX, maxY)
        

    def ScaleObjectsToFit(self, objs):
        (minX, minY, maxX, maxY) = self.GetBoxFromObjects(objs)
        midX = (maxX - minX) / 2
        midY = (maxY - minY) / 2
        factor = (self.cardX - (self.border * 2)) / (maxX - minX)
        things = []
        for obj in objs:
            x = rs.ScaleObject( obj, (midX, midY, 0) , (factor,factor,1), False )
            things.append(x)

        return things

    def AddObjectsToBox(self, objs, location, scale):
        if scale is True:
            objs = self.ScaleObjectsToFit(objs)

        (minX, minY, maxX, maxY) = self.GetBoxFromObjects(objs)

        midX = ((maxX - minX) / 2) + minX
        midY = ((maxY - minY) / 2) + minY

        if location == "lower":
            # center at the bottom of box
            rs.MoveObjects(objs, rs.VectorSubtract((self.cardX / 2, self.border, 0), (midX, minY, 0)))

        if location == "upper":
            # center at the top of box
            rs.MoveObjects(objs, rs.VectorSubtract((self.cardX / 2, self.cardY - self.border, 0), (midX, maxY, 0)))

        if location == "center":
            # center at the top of box
            rs.MoveObjects(objs, rs.VectorSubtract((self.cardX / 2, (self.cardY / 2), 0), (midX, midY, 0)))

        return(objs)


    def AddTextToBox(self, textstring, location, scale):
        commandString = "-_TextObject _Height=.18 _FontName=\"Batang\" _Output=_Surfaces " + "\"" + textstring + "\"" + " 0,0,0 _Enter"
        rs.Command(commandString)
        objs = rs.LastCreatedObjects()
        objs = self.MakeBorders(objs)
        objs = self.AddObjectsToBox(objs, location, scale)
        return objs
    
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
    g = Thing("tableguides.ini")
 
    rows = []
    for line in open(g.name_file,'r'):
        line = line.replace('\n', '')
        rows.append(line)

    countX = 0
    countY = 0
    for row in rows:
        (table, name) = re.split(r'\t+', row)

        objs =  rs.CopyObjects(rs.BlockObjects("MyBlock"), (0,0,0))
        o1 = g.AddObjectsToBox(objs, 'lower', False)
        o2 = g.AddTextToBox(table, 'center', False)
        o3 = g.AddTextToBox(name, 'upper', True)
        
        objs = o1 + o2 + o3

        rs.MoveObjects(objs, rs.VectorSubtract((countX * (g.cardX + g.bump), countY * (g.cardY + g.bump), 0), (0, 0, 0)))

        countY += 1

        if countY > 4:
            countY = 0
            countX += 1
