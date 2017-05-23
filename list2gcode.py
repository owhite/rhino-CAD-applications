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

class Gcode:
    def __init__(self, FileName):

        self.ini_file = FileName
        self.gcode_string = ""

        self.dictionary_file = rs.GetSettings(FileName, 'GCODE', 'dictionary')
        self.move_feed_rate = int(rs.GetSettings(FileName, 'GCODE', 'move_feed_rate'))
        self.cut_feed_rate = int(rs.GetSettings(FileName, 'GCODE', 'cut_feed_rate'))
        self.dwell_time = float(rs.GetSettings(FileName, 'GCODE', 'dwell_time'))

        from os.path import join as pjoin
        self.output_path = rs.GetSettings(FileName, 'GCODE', 'ncfile_dir')
        self.output_extension = rs.GetSettings(FileName, 'GCODE', 'output_file_ext')

        self.cut_speed_variable = '#<cutfeedrate>'
        self.move_speed_variable = '#<movefeedrate>'
        self.dwell_time_variable = '#<dwelltime>'

        self.name_file = rs.GetSettings(FileName, 'GCODE', 'name_file')
        return True

    def MakeKeyObject(self, word, pt):
        textLocationPt = (2.628,0.880,0.000)

        ids = []
        id = self.AddLine(((1.5350,1.0618,0), (1.5350,0.7048,0)))
        ids.append(id)
        id = self.AddLine(((1.6847,0.7048,0), (1.6847,1.0618,0)))
        ids.append(id)
        
        for id in self.AddTextObject(word, textLocationPt):
            ids.append(id)

        id = self.AddLine(((2.6813,0.7389,0), (3.6082,0.7389,0)))
        ids.append(id)
        id = self.AddLine(((3.6556,0.7036,0), (3.6556,1.0517,0)))
        ids.append(id)
        id = self.AddLine(((3.8053,0.7149,0), (3.8053,1.0517,0)))
        ids.append(id)

        rs.MoveObjects(ids, pt)

        return(ids)

    def AddLine(self, pts):
        id = rs.AddPolyline(pts)
        rs.ObjectLayer(id, "PARTS")
        return(id)

    def RemoveParts(self, objs):
        rs.DeleteObjects(objs)

    def AddTextObject(self, word, pt):
        commandString = "-_TextObject _Height=.18 _FontName=\"Batang\" _Output=_Surfaces " + "\"" + word + "\"" + " 0,0,0 _Enter"
        print commandString
        rs.Command(commandString)
        objs = rs.AllObjects()
        borders = []

        for obj in objs:
            if rs.IsSurface(obj):
                ids = rs.DuplicateSurfaceBorder(obj, type=0)
                if ids:
                    for id in ids:
                        # angle_tolerance=1, 
                        # tolerance=0.5,

                        id = rs.ConvertCurveToPolyline(id,
                                                       min_edge_length = .01,
                                                       delete_input=True)
                        borders.append(id)
                        rs.ObjectLayer(id, "PARTS")
                rs.DeleteObjects(obj)
        # rs.SelectObjects(borders)

        min = 9999999.0
        max = -9999999.0

        for id in borders:
            box = rs.BoundingBox(id)
            for point in box:
                if (point[0] < min):
                    min = point[0]
                if (point[0] > max):
                    max = point[0]

        midX = (max - min) / 2.0

        min = 9999999.0
        max = -9999999.0

        for id in borders:
            box = rs.BoundingBox(id)
            for point in box:
                if (point[0] < min):
                    min = point[1]
                if (point[0] > max):
                    max = point[1]

        midY = (max - min) / 2.0

        pt2 = (midX, midY, 0)
        rs.MoveObjects(borders, rs.VectorSubtract(pt, pt2))

        return(borders)

    def _boolean(self, value):
        if value == "True":
            return True
        if value == "False":
            return False

    def Str2Array(self, s):
        return(tuple(int(i) for i in s.split(',')))

    # MUCH more testing could happen here
    def IfBackupFileReady(self):
        if len(self.backup_dir) == 0:
            sys.exit("need backup_dir in ini file")
        if not self.backup_file_count:
            sys.exit("need backup_file_count in ini file")
        if len(self.backup_file_ext) == 0:
            sys.exit("need backup_file_ext in ini file")
            

    # this tests how many backups there are, 
    # kills the oldest one > backup_file_count
    def WhackOldBackupFiles(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        path = os.path.join(self.backup_dir, "*." + self.backup_file_ext)

        files = filter(os.path.isfile, glob.glob(path))
        files.sort(key=lambda x: os.path.getmtime(x) , reverse=True)

        count = 1
        for f in files:
            if count > self.backup_file_count:
                os.remove(f) # bye bye
            count += 1

    def RandName(self):
        size=6
        chars=string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    def AddNewBackupFile(self):
        self.IfBackupFileReady()
        self.WhackOldBackupFiles()
        name = self.RandName()
        path = os.path.join(self.backup_dir, name + "." + self.backup_file_ext)

        objects = rs.SelectedObjects()  
        count = 0
        for object_id in objects:
            layer = rs.ObjectLayer(object_id)
            if rs.IsCurve(object_id) and layer == self.parts_layer:
                count+=1
        if count >= 0:
            # this will export everything that is selected, including
            # things that are not cuts or paths
            commandString = "-_Export " + path + " _Enter _Enter"
            rs.Command(commandString)
    

    def TestIfOK2(self):
        return 1

    def TestIfOK(self):
        path = rs.GetSettings(self.ini_file, 'GCODE', 'ncfile_dir')
        # is there a .ini file?
        if not os.path.isdir(path):
            rs.MessageBox("%s .ini file section GCODE, value for ncfile_dir = %s. %s is not a directory" % (self.ini_file,path, path))
            return False
        # awesome, do we have destination directory? 
        f = self.output_file
        try:
            with open(f, 'wb') as the_file:
                the_file.write(self.gcode_string)
            print 'wrote (%s) in %s' % (path, g.output_file)
        except IOError: 
            rs.MessageBox("%s is not available" % f)

        return True

    def MakePhrase(self):
        try:
            ins = open(self.dictionary_file, "r")
        except IOError:
            raise Exception,'NoFileError : %s' % (self.dictionary_file)
    
        adjective_count = 0
        adverb_count = 0
        adj = []
        adv = []
        for line in ins:
            line = line.strip()
            (word,type) = line.split('\t')
            if type == "A":
                adj.append(word)
                adjective_count += 1
            if type == "v":
                adv.append(word)
                adverb_count += 1

        import random

        s = '%s %s' % (adv[int(adverb_count * random.random())], 
                       adj[int(adjective_count * random.random())])
        return s.upper()

    def WriteGcode(self): 
        f = self.output_file
        try:
            with open(f, 'wb') as the_file:
                the_file.write(self.gcode_string)
            print 'wrote %s' % (g.output_file)
        except IOError: 
            rs.MessageBox("%s is not available" % f)

    def DumpPolyline(self, file, line):
        try:
            with open(file, 'wb') as the_file:
                for pt in rs.PolylineVertices(line):
                    the_file.write("%lf %lf %lf\n" % (pt[0], pt[1], pt[2]))
            print 'wrote to %s' % file
        except IOError: 
            rs.MessageBox("%s is not available" % f)

    def WritePolyline(self, line, comment):
        poly = rs.PolylineVertices(line)
        pt = poly[0]
        self.AddEOL()
        self.AddComment(comment)
        self.MoveNoCut(pt[0], pt[1])

        self.OxygenOn()
        self.CuttingToolOn()
        self.AddEOL()
        for pt in poly[1:]:
            self.Move(pt[0], pt[1])

        self.CuttingToolOff()
        self.OxygenOff()
        self.AddEOL()

    def Move(self, x, y):
        self.Append('G01 X%0.4lf Y%0.4lf F%s\n' % (x, y, self.cut_speed_variable))

    def MoveNoCut(self, x, y):
        self.CuttingToolOff()
        self.Append('G00 X%0.4lf Y%0.4lf F%s\n' % (x, y, self.move_speed_variable))
        self.AddEOL()

    def AddComment(self, c):
        self.Append('(%s)\n' % c)

    def AddEOL(self):
        self.Append('\n')

    def CuttingToolOff(self):
        self.Append('M65 P03 (LASER OFF)\n')

    def CuttingToolOn(self):
        self.Append('M64 P03 (LASER ON)\n')
        if self.dwell_time != 0.0:
            self.Append('G4 P%s\n' % (self.dwell_time_variable))

    def OxygenOn(self):
        self.Append('M64 P01 (GAS LINE ON)\n')

    def OxygenOff(self):
        self.Append('M65 P01 (GAS LINE OFF)\n')

    def AddHeader(self):
        header = ('%s=%s\n'
                  '%s=%s\n'
                  '%s=%s\n'
                  'G17 G20 G40 G49 G80 G90\n'
                  'G92 X0 Y0 (SET CURRENT POSITION TO ZERO)\n'
                  'G64 P0.005 (Continuous mode with path tolerance)\n\n'
                  'M64 P00 (VENTILATION ON)\n'
                  'M65 P01 (GAS LINE OFF)\n'
                  'M65 P03 (LASER OFF)\n\n') % (self.move_speed_variable, self.move_feed_rate, self.cut_speed_variable, self.cut_feed_rate, self.dwell_time_variable, self.dwell_time)

        self.Append(header)

    def AddFooter(self):
        self.CuttingToolOff()
        self.Append('M65 P00 (VENTILATION OFF)\n')
        self.Append('G1 X0.000 Y0.000 F%s (HOME AGAIN HOME AGAIN)\n' % (self.move_speed_variable))
        self.Append('M2 (LinuxCNC program end)')
        self.AddEOL()


    def Append(self, s):
        self.gcode_string = self.gcode_string + s

    def Prepend(self, s):
        self.gcode_string = s + self.gcode_string

    def MakePartsWithTag(self, tags, pt):
        objects = []
        newPt = (0,0,0)
        for tag in tags:
            ids = g.MakeKeyObject(tag, newPt)
            newPt = rs.VectorAdd(pt,newPt)
            objects += ids
        return(objects)

    def DumpPartsToFile(self, objects, name, p): 
        from os.path import join as pjoin
        name = name + "." + g.output_extension
        self.output_file = pjoin(g.output_path, name)

        title = '(' + p + ')' + '\n'
        self.Append(title)
        self.AddHeader()

        for id in objects:
            g.WritePolyline(id, "LAYER: PARTS")

        self.AddFooter()
        self.WriteGcode()
        self.gcode_string = ""


if __name__ == '__main__':
    g = Gcode("list2gcode.ini")
 
    if g.TestIfOK2():
        rows = []
        for line in open(g.name_file,'r'):
            line = line.replace('\n', '')
            rows.append(line)

        tag_num = 8
        count = 0
        tags = []
        w = ""
        for row in rows:
            tags.append(row)
            w = w + row + " "
            if len(tags) >= tag_num:
                objects = []
                objects = g.MakePartsWithTag(tags, (0,1.75,0))
                g.DumpPartsToFile(objects, ("thing%d" % count), w)
                # g.RemoveParts(objects)
                count += 1
                del tags[:]
                w = ""


        if len(tags) > 0:
            objects = []
            objects = g.MakePartsWithTag(tags, (0,1.75,0))
            g.DumpPartsToFile(objects, ("thing%d" % count), w)
            # g.RemoveParts(objects)
