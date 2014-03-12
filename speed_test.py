#!/usr/bin/env python

import sys
import os
import ConfigParser
import time

class Gcode:
    def __init__(self, file_name):

        print "loading: %s" % file_name

        self.ini_file = file_name
        parser = ConfigParser.RawConfigParser()
        parser.read(file_name)

        self.config_parser = parser

        self.parts_layer = parser.get('layers', 'parts_layer')
        self.cuts_layer = parser.get('layers', 'cuts_layer')
        self.path_layer = parser.get('layers', 'parts_path_layer')
        self.cutspath_layer = parser.get('layers', 'cuts_path_layer')
        self.showpaths = parser.getboolean('layers', 'showpaths')

        self.iterations = parser.getint('tsp', 'iterations')
        self.start_temp = parser.getfloat('tsp', 'start_temp')
        self.alpha = parser.getfloat('tsp', 'alpha')
        
        self.dictionary_file = parser.get('gcode', 'dictionary')
        self.move_feed_rate = parser.getint('gcode', 'move_feed_rate')
        self.cut_feed_rate = parser.getint('gcode', 'cut_feed_rate')
        self.dwell_time = parser.getfloat('gcode', 'dwell_time')

        from os.path import join as pjoin
        self.output_file = pjoin(parser.get('gcode', 'ncfile_dir'), 
                                 parser.get('gcode', 'output_file'))

        self.power = parser.getint('laser', 'power')

        self.gcode_string_parts = list()

        self.cut_speed_variable = '#<cutfeedrate>'
        self.move_speed_variable = '#<movefeedrate>'
        self.dwell_time_variable = '#<dwelltime>'

        # return True

    def gcode_string(self):
        return "".join(self.gcode_string_parts)

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
                the_file.write(self.gcode_string())
            print 'wrote (%s) in %s' % (p, g.output_file)
        except IOError: 
            print "%s is not available" % f

    def WritePolyline(self, poly):
        pt = poly[0]
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
        self.Append('G1 X0.000 Y0.000 F%s (HOME AGAIN HOME AGAIN)\n' % self.move_speed_variable)
        self.Append('M2 (LinuxCNC program end)')
        self.AddEOL()


    def Append(self, s):
        self.gcode_string_parts.append(s)

    def Prepend(self, s):
        ## these are more expensive operations than appending
        self.gcode_string_parts.insert(0, s)

    def LoadCurve(self, file):
        f = open(file, 'rt')
        l = []
        for row in f: 
            q = row.strip().split(' ')
            l.append([float(q[0]), float(q[1]), float(q[2])])
        f.close()
                                   
        return(l)

if __name__=="__main__":
    g = Gcode("polyline_dump.ini")

    out_files = list()

    parts = []

    debug_tests_to_execute = 5

    while debug_tests_to_execute > 0:
        parts.append(g.LoadCurve("scrap.txt"))
        debug_tests_to_execute -= 1
    
    for part in parts:
        t1 = time.time()
        g.WritePolyline(part)
        print "  time :: %lf" % (time.time() - t1)


