#!/usr/bin/env python

import os
import time
import sys
import getopt
import re
import csv
import gcode
import TSP

from ConfigParser import *
from shapely.geometry import LineString
from shapely.geometry import Polygon
from shapely.geometry import Point
from PIL import Image, ImageDraw, ImageFont

class Toolpath:
    def __init__(self):
        self.LoadIniData()
        self.verbose = 0
        self.total_salesman = 0
        self.tag = ""
        self.gcode = ""
        self.clock_time = "gotta set time"
        self.tour_executable = "/usr/bin/LKH.UNIX"

    def LoadRawData(self):
        file = self.input_file
        self.polygons = {}
        try:
            inc = 0
            done = {}
            self.polygons[inc] = {}
            with open(file) as csv_file:
                coords = []
                first_time = 1
                for row in csv.reader(csv_file, delimiter=' '):
                    if first_time != 1: # its not first row
                        coords.append(pt)
                        self.polygons[inc] = {}
                        self.polygons[inc]['layer'] = layer
                        if row[0] not in done: # its new
                            self.polygons[inc]['data'] = LineString(coords)
                            inc += 1
                            coords = []
                    first_time = 0
                    done[row[0]] = 1
                    layer = row[1]
                    pt = (float(row[3]),float(row[4]))

                coords.append(pt)
                self.polygons[inc]['data'] = LineString(coords)

        except IOError as e:
            print 'Operation failed: %s' % e.strerror

    def AddLine(self, line, layer):
        inc = len(self.polygons)
        self.polygons[inc] = {}
        self.polygons[inc]['layer'] = layer
        self.polygons[inc]['data'] = line

    def DrawRawData(self, img_file):
        padding=20
        # shift all coords in a bit
        tmp1 = []
        first_time = 1
        for i, l in enumerate(self.polygons):
            coords = self.polygons[i]['data'].coords
            new_coords = []
            for (x,y) in coords:
                if first_time:
                    maxx,maxy=x,y
                    minx,miny=x,y
                minx=min(x,minx)
                miny=min(y,miny)
                maxx=max(x,maxx)
                maxy=max(y,maxy)
                new_coords.append((x,y))
                first_time = 0
            tmp1.append(new_coords)

        inc_x = 640 / (maxx - minx)
        inc_y = 400 / (maxy - miny)

        minx = minx * inc_x
        miny = miny * inc_y

        tmp2 = []
        for i in tmp1:
            j = []
            for (x,y) in i:
                x = int((x * inc_x) - minx) + padding                
                y = (400 - int((y * inc_y) - miny)) + padding
                j.append((x,y))
            tmp2.append(j)
            
        img=Image.new("RGB",(640 + 2*padding,400 + 2*padding),color=(255,255,255))
        font=ImageFont.load_default()
        d=ImageDraw.Draw(img);
        inc = 0
        for coords in tmp2:
            width = 1
            if self.polygons[inc]['layer'] == 'CUTS_PATH':
                width = 2
            color = self.layer_colors[self.polygons[inc]['layer']]
            num = len(coords)
            for i,q in enumerate(coords):
                if i == num - 1:
                    break
                x1,y1=coords[i]
                x2,y2=coords[i+1]
                d.line((x1,y1,x2,y2),fill=color, width = width)
            inc += 1

        img.save(img_file, "PNG")

    def str2array(self, s):
        return(tuple(int(i) for i in s.split(',')))

    def LoadIniData(self):
        FileName = re.sub(r'\.py$', "", os.path.abspath( __file__ )) + '.ini'
        self.cp=ConfigParser()
        try:
            self.cp.readfp(open(FileName,'r'))
	# f.close()
        except IOError:
            raise Exception,'NoFileError'

        self.ini_file = FileName
        self.input_file = self.cp.get('Variables', 'raw_input_file')
        self.output_file = self.cp.get('Variables', 'output_file')

        self.parts_layer = self.cp.get('Layers', 'parts_name')
        self.cuts_layer = self.cp.get('Layers', 'cuts_name')
        self.path_layer = self.cp.get('Layers', 'path_name')
        self.cutpath_layer = self.cp.get('Layers', 'cutpath_name')

        self.debug = self.cp.getboolean('Debug', 'debug')
        self.debug_file_name = self.cp.get('Debug', 'debug_file_name')

        self.layer_colors = {}
        self.layer_colors[self.parts_layer] = self.str2array(self.cp.get('Layers', 'parts_color'))
        self.layer_colors[self.cuts_layer] = self.str2array(self.cp.get('Layers', 'cuts_color'))
        self.layer_colors[self.path_layer] = self.str2array(self.cp.get('Layers', 'path_color'))
        self.layer_colors[self.cutpath_layer] = self.str2array(self.cp.get('Layers', 'cutpath_color'))

        self.iterations = self.cp.getint('TSP', 'iterations')
        self.start_temp = self.cp.getfloat('TSP', 'start_temp')
        self.alpha = self.cp.getfloat('TSP', 'alpha')

    def LinesByLayer(self, layer):
        p = []
        for i, l in enumerate(self.polygons):
            if self.polygons[i]['layer'] == layer:
                p.append(self.polygons[i]['data'])
        return p

    def GetIntersectionDistance(self, l1, l2):
        # l1 should be just two coordinate positions
        # get its starting coorinate
        pt1 = Point(l1.coords[0])
        x = l1.intersection(l2)
        # intersections can return a lot of things
        d = -1
        if x.wkt == 'GEOMETRYCOLLECTION EMPTY':
            d = -1
            # print "nothing"
        elif re.match('^POINT', x.wkt): 
            # print "point"
            pt2 = Point(x.coords[0])
            d = pt1.distance(pt2)
        elif re.match('^MULTI', x.wkt): 
            # print "mpoint"
            # this will return the minimum distance
            pt2 = Point(x[0].coords[0])
            d = pt1.distance(pt2) 
            for pt2 in x:
                pt2 = Point(pt2)
                if d < pt1.distance(pt2):
                    d = pt1.distance(pt2)
        else:
            print 'dunno what intersection pass me'
        return d

    def OrderLinesUsingPath(self, lines, path, start):
        order = []
        # tries to figure out where a user defined path interects with all your
        #  objects, to determine the order that objects should be cut
        if len(lines) == 0:
            # there are no lines to order
            print "no lines sent to OrderCutsUsingPath"
        else: 
            # go through all the segments of the path
            #  and get the distances of things it hit on segment
            coords = path.coords
            num = len(coords)
            results = {}
            dis = 0 # this accumulates distance along the path
            for i,q in enumerate(coords):
                if i == num - 1:
                    break
                seg = LineString([coords[i], coords[i+1]])
                # print seg
                inc = 0
                for line in lines:
                    d = self.GetIntersectionDistance(seg, line)
                    if d != -1:
                        d += dis
                        results[inc] = d
                    # print '%d %lf' % (inc, d)
                    inc += 1
                dis += Point(coords[i]).distance(Point(coords[i+1]))
            # this sorts on the values in the dictionary 'results'
            import operator
            [order.append(i[0]) for i in sorted(results.iteritems(), key=operator.itemgetter(1))]
                
            # now we have the order, clean it up a little
            order, path, parts = self.OptimizePartsFromOrder(lines, order, start)

            # this returns reversed lines in cases where it makes a better
            # tour. it does not delete the lines that were not in the tour
            return order, path, parts

    # this works okay-ish. Did see some examples of picking
    #  the nearest start point, at the expense of the distance
    #  to the next part. Next implementation should look ahead
    def OptimizePartsFromOrder(self, lines, order, start):
        # find nearest thing to start, rotate the order of the tour
        first = self.GetNearestCenterOrEnd(lines, order, start)
        i = order.index(first)
        order = order[i:] + order[:i]

        pos = start
        c = [start]
        c.append(start)
        for i in order:
            line = lines[i]
            if line.is_ring: 
                c.append((line.centroid.x, line.centroid.y))
                pos = (line.centroid.x, line.centroid.y)
            else: 
                d1 = Point(pos).distance(Point(line.coords[0]))
                d2 = Point(pos).distance(Point(line.coords[-1]))
                if d2 < d1:
                    lines[i] = self.ReverseLine(lines[i])
                c.append(lines[i].coords[0])
                c.append(lines[i].coords[-1])
                pos = (line.coords[-1])

        #  path is mostly used for debugging and drawing. 
        path = LineString(c)        
        return order, path, lines

    def GetNearestCenterOrEnd(self, lines, order, start):
        # collect up all the points to test
        min_line = None
        for i in order:
            line = lines[i]
            if line.is_ring: 
                pt = (line.centroid.x, line.centroid.y)
                dis = Point(start).distance(Point(pt))
            else: 
                d1 = Point(start).distance(Point(line.coords[0]))
                d2 = Point(start).distance(Point(line.coords[-1]))
                dis = min(d1, d2)
            if min_line is None or dis <= min_dis:
                min_dis = dis
                min_line = i
        # returns the line that is nearest to start
        return min_line

    def ReverseLine(self,line):
        l = list(line.coords)
        l.reverse()
        return LineString(l)

    def GatherCenterAndEndCoords(self, lines):
        # nothing special just used to grab centers of ring objects
        #  and the end points of linear ones
        coords = []
        locked = []
        info = {} # helps record what type of thing was ordered
        tour_pos = 0
        line_id = 0
        for l in lines:
            # if an object is circular, arbitrarily pick its center
            # see: http://toblerity.github.com/shapely/manual.html
            #  to understand is_ring/is circular
            if l.is_ring: 
                info[tour_pos] = {}
                coords.append((l.centroid.x, l.centroid.y))
                info[tour_pos]['line_id'] = line_id
                info[tour_pos]['type'] = 'ring'
                info[tour_pos]['pt'] = (l.centroid.x, l.centroid.y)
                tour_pos += 1
            # if an object is linear, create two points,
            #   the start and the end
            else:
                info[tour_pos] = {}
                info[tour_pos]['line_id'] = line_id
                info[tour_pos]['type'] = 'start'
                info[tour_pos]['pt'] = l.coords[0]

                info[tour_pos+1] = {}
                info[tour_pos + 1]['line_id'] = line_id
                info[tour_pos + 1]['type'] = 'end'
                info[tour_pos + 1]['pt'] = l.coords[-1]

                coords.append(l.coords[0]) # gather first coord
                coords.append(l.coords[-1]) # last
                locked.append((tour_pos,tour_pos + 1))
                tour_pos += 2
            line_id += 1
        return coords, info, locked

    # works pretty good. One issue is it does not 'cut' rings to find
    #  the optimal place to enter into them. Another issue is it does
    #  not base the shortest path on the starting position, because 
    #  it adds in the starting position after it does the tsp. 
    def OrderLines(self, lines, start, temp, alpha, iterations):
        tour = []
        # tries to figure out an order of lines to be cut
        #  using the traveling saleman algorithm

        coords, info, locked = self.GatherCenterAndEndCoords(lines)

        if len(lines) == 0:
            print "no lines sent to OrderLines"
            tour = []
        elif len(lines) == 1:
            tour = [0]
        elif len(lines) == 2:
            tour = [0,1,2]
            if len(coords) == 2:
                tour = [0,1]
        else:
            # create a path. This will this return an order of the 
            #  center of ring-shaped lines, and the start or end 
            #  points of linear lines
            print 'running tsp'
            tsp = TSP.TSP(coords = coords, start_temp = temp, alpha = alpha)
            tour = tsp.anneal(locked_points=locked, iterations = iterations)
                
        # getting tour is great, but it is not the actual order of lines.
        #  it is the tour of points defined by the centroid
        #  of rings, the start _and_ ends of linear lines.
        # Do this to get the actual order of lines:
        order = []
        for i in tour:
            if info[i]['line_id'] not in order:
                order.append(info[i]['line_id'])
                if info[i]['type'] == 'end':
                    id = info[i]['line_id']
                    lines[id] = self.ReverseLine(lines[id])

        path = LineString()
        # order now generated, but it doesnt know where the start is
        #  get nearest thing to start, rotate the order
        if len(order) != 0:
            first = self.GetNearestCenterOrEnd(lines, order, start)
            i = order.index(first)
            order = order[i:] + order[:i]

            # all that is done, now just collect the points to create the path
            #  this is mostly used for debugging and drawing. 
            c = [start]
            for i in order:
                if lines[i].is_ring: 
                    c.append((lines[i].centroid.x, lines[i].centroid.y))
                else:
                    c.append(lines[i].coords[0]) 
                    c.append(lines[i].coords[-1]) 

            path = LineString(c)        
            # this returns reversed lines in cases where it makes a better
            # tour. it does not delete the lines that were not in the tour
        return order, path, lines

    def toolpath(self):
        # check if user supplied a line connecting the parts
        path = self.LinesByLayer(self.path_layer)
    
        # get all the parts
        parts = self.LinesByLayer(self.parts_layer)
    
        # get all cuts
        cuts = self.LinesByLayer(self.cuts_layer)
    
        # get all cuts
        cuts_path = self.LinesByLayer(self.cutpath_layer)
    
        if len(path) > 1:
            print "there can only be one path to cut parts"
        elif len(path) == 1:
            order, path, parts = self.OrderLinesUsingPath(parts,
                                                          path[0],
                                                          (0.0,0.0))
        else:
            order, path, parts = self.OrderLines(parts, (0.0,0.0),
                                                 self.start_temp,
                                                 self.alpha,
                                                 self.iterations)
        # do this to debug and have a look at the part path
        if self.debug:
            self.AddLine(path, 'PART_PATH')

        gcode_cuts = [] # list to export all cuts to gcode
        cut_path = None
        for i in order:
            part = parts[i]
            gcode_cuts.append(list(part.coords))
            region = Polygon(part.coords)
            cuts_in_part = [] 
            for j in cuts:
                if region.intersects(j):
                    cuts_in_part.append(j)
            for j in cuts_path:
                if region.intersects(j):
                    cut_path = j
    
            start = (0.0,0.0) # start is goofy. could be based on actual path
                              #  of parts getting cut
            if cut_path is not None:
                tour, path, cuts_in_part = self.OrderLinesUsingPath(cuts_in_part,
                                                                    cut_path,
                                                                    start)
            else:
                tour, path, cuts_in_part = self.OrderLines(cuts_in_part,
                                                           start,
                                                           self.start_temp,
                                                           self.alpha, 
                                                           self.iterations)
            for j in tour:
                gcode_cuts.append(list(cuts_in_part[j].coords))

            if self.debug:
                self.AddLine(path, 'CUTS_PATH')

        # do this to debug and have a look paths and parts
        if self.debug:
            self.DrawRawData(self.debug_file_name)

        return gcode_cuts

if __name__ == '__main__':
    tp=Toolpath()
    tp.LoadRawData()
    gcode_cuts = tp.toolpath()

    g = gcode.setup(tp)

    p = g.MakePhrase()
    title = '(' + p + ')' + '\n\n'
    g.append(title)
    g.add_header()

    for i in gcode_cuts:
        g.write_polyline(i)

    g.add_footer()

    g.write_gcode(g)

    print '(' + p + ')'

