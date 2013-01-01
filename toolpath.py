#!/usr/bin/env python

import math
import os
import sys
import getopt
import csv
import gcode
import TSP
import re

from ConfigParser import *
from shapely.geometry import LineString
from shapely.geometry import Polygon
from shapely.geometry import Point
from PIL import Image, ImageDraw, ImageFont

class Toolpath:
    def __init__(self):
        pass # be happy!

    # this is like DrawRawData but it works better and
    #  adds lines and other information to show the path
    #  being cut
    def DrawPartsAndCuts(self, img_file, things):
        padding=20

        img=Image.new("RGB",(self.png_width + 2 * padding,
                             self.png_height + 2 * padding),
                      color=(255,255,255))

        if len(things) == 0:
            print "nothing to draw"
            return

        minx = maxx = things[0]['part'].coords[0][0]
        miny = maxy = things[0]['part'].coords[0][1]
        
        minx = miny = 0

        for i in things:
            x1, y1, x2, y2 = things[i]['part'].bounds
            # print things[i]['part'].bounds
            minx = min(minx, x1)
            miny = min(miny, y1)
            maxx = max(maxx, x2)
            maxy = max(maxy, y2)

            for j in things[i]['cuts']:
                x1, y1, x2, y2 = j.bounds
                minx = min(minx, x1)
                miny = min(miny, y1)
                maxx = max(maxx, x2)
                maxy = max(maxy, y2)

        inc = self.png_width / (maxx - minx)
        if (inc * maxy) > self.png_height:
            inc = self.png_height / (maxy - miny)

        for i in things:
            things[i]['part'] = self.TransformLine(things[i]['part'], inc, minx, miny, padding)
            l = []
            for j in things[i]['cuts']:
                l.append(self.TransformLine(j, inc, minx, miny, padding))
            things[i]['cuts'] = l

        
        font = ImageFont.load_default()
        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 40)

        d=ImageDraw.Draw(img);
        black = (0,0,0)

        parts_color = self.layer_colors['PARTS']
        cuts_color = self.layer_colors['CUTS']

        width = 1
        oldpt = self.TransformCoords((0,0), inc, minx, miny, padding)

        count = 0
        for i in things:
            for j in things[i]['cut_tour']:
                line = things[i]['cuts'][j]
                newpt = self.DrawLine(d, line, cuts_color, width)
                d.line((oldpt, newpt),fill=black, width = 1)
                oldpt = newpt

            newpt= self.DrawLine(d, things[i]['part'], parts_color, width)
            self.PlaceLabel(d, things[i]['part'], count, font)
            d.line((oldpt, newpt),fill=black, width = 1)
            oldpt = things[i]['part'].coords[0]
            count += 1

        img.save(img_file, "PNG")

    def PlaceLabel(self, draw, line, num, font):
        (x1,y1,x2,y2) = line.bounds
        x = x1 + ((x2 - x1) * .9)
        y = y1 + ((y2 - y1) * .9)
        s = str(num)
        w, h = draw.textsize(s, font=font)
        x = x - w
        y = y - h
        draw.text((x,y), s, font = font, fill="blue")
        return x, y

    def DrawLine(self, draw, line, color, width):
        x1 = line.coords[0][0]
        y1 = line.coords[0][1]
        for i in line.coords[1:]:
            (x2, y2) = i
            draw.line((int(x1),int(y1),int(x2),int(y2)),fill=color, width = 1)
            x1 = x2
            y1 = y2
        return x1, y1

    def TransformLine(self, line, inc, minx, miny, padding):
        j = []
        for c in list(line.coords):
            j.append(self.TransformCoords(c, inc, minx, miny, padding))

        return LineString(j)

    def TransformCoords(self, coords, inc, minx, miny, padding):
        (x,y) = coords
        x = int((x - minx) * inc) + padding
        y = (self.png_height - int((y - miny) * inc)) + padding
        return((x,y))

    def DrawRawData(self, img_file):

        padding=20

        img=Image.new("RGB",(self.png_width + 2*padding,
                             self.png_height + 2*padding),
                      color=(255,255,255))

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

        size = max((maxx - minx), (maxy - miny))
        if (maxx - minx) > (maxy - miny):
            inc = self.png_width / size
        else:
            inc = self.png_height / size

        minx = minx * inc
        miny = miny * inc

        tmp2 = []
        for i in tmp1:
            j = []
            for (x,y) in i:
                x = int((x * inc) - minx) + padding                
                # flips the image
                y = (self.png_height - int((y * inc) - miny)) + padding
                j.append((x,y))
            tmp2.append(j)
            
        font=ImageFont.load_default()
        d=ImageDraw.Draw(img);
        inc = 0
        for coords in tmp2:
            width = 1
            if self.polygons[inc]['layer'] == 'CUTS_PATH':
                width = 2
            color = self.layer_colors[self.polygons[inc]['layer']]
            num = len(coords)
            if len(coords) != 0:
                (x, y) = coords[0]
                for i,q in enumerate(coords):
                    if i == num - 1:
                        break
                    x1,y1=coords[i]
                    x2,y2=coords[i+1]
                    d.line((x1,y1,x2,y2),fill=color, width = width)
            inc += 1

        img.save(img_file, "PNG")

    def LoadRawData(self):
        file = self.input_file
        self.polygons = {}
        flag = True
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
                        if layer == self.parts_layer:
                            flag = False
                        if row[0] not in done: # its new
                            self.polygons[inc]['data'] = LineString(coords)
                            inc += 1
                            coords = []
                    first_time = 0
                    done[row[0]] = 1
                    layer = row[1]
                    pt = (float(row[3]),float(row[4]))
            if flag:
                print 'Didnt find any parts, bailing'
                sys.exit(1)

            coords.append(pt)
            self.polygons[inc]['data'] = LineString(coords)

        except IOError as e:
            print 'Operation failed: %s' % e.strerror

    def AddLine(self, line, layer):
        inc = len(self.polygons)
        self.polygons[inc] = {}
        self.polygons[inc]['layer'] = layer
        self.polygons[inc]['data'] = line

    def str2array(self, s):
        return(tuple(int(i) for i in s.split(',')))

    def LoadIniData(self, FileName):
        self.ini_file = FileName
        self.verbose = 0
        self.gcode = ""

        self.cp=ConfigParser()
        try:
            self.cp.readfp(open(FileName,'r'))
	# f.close()
        except IOError:
            raise Exception,'NoFileError'

        self.ini_file = FileName

        from os.path import join as pjoin
        self.input_file = pjoin(self.cp.get('RawData', 'input_dir'), 
                                 self.cp.get('RawData', 'raw_input_file'))

        self.output_file = pjoin(self.cp.get('Gcode', 'ncfile_dir'), 
                                 self.cp.get('Gcode', 'output_file'))

        self.parts_layer = self.cp.get('Layers', 'parts_name')
        self.cuts_layer = self.cp.get('Layers', 'cuts_name')
        self.path_layer = self.cp.get('Layers', 'path_name')
        self.cutspath_layer = self.cp.get('Layers', 'cutspath_name')

        self.debug = self.cp.getboolean('Debug', 'debug')
        self.debug_pic = self.cp.getboolean('Debug', 'draw_debug_pic')
        self.debug_file_name = self.cp.get('Debug', 'debug_file_name')
        self.png_width = self.cp.getint('Debug', 'png_width')
        self.png_height = self.cp.getint('Debug', 'png_height')

        self.layer_colors = {}
        self.layer_colors[self.parts_layer] = self.str2array(self.cp.get('Layers', 'parts_color'))
        self.layer_colors[self.cuts_layer] = self.str2array(self.cp.get('Layers', 'cuts_color'))
        self.layer_colors[self.path_layer] = self.str2array(self.cp.get('Layers', 'path_color'))
        self.layer_colors[self.cutspath_layer] = self.str2array(self.cp.get('Layers', 'cutspath_color'))

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
            print 'dunno what intersection passed me'
        return d

    def OrderLinesUsingPath(self, lines, path):
        order = []
        # tries to figure out where a user defined path interects with all your
        #  objects, to determine the order that objects should be cut

        if len(lines) == 0:
            # there are no lines to order
            print "no lines sent to OrderCutsUsingPath"
            return order, path, parts
        else: 
            # go through all the segments of the path
            #  and get the distances of things it hit on segment
            coords = path.coords
            start = coords[0]
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
                
            # now we have the order, clean up linear parts a little
            #   dont do this if the TSP algorithm was used.
            order, path, parts = self.OptimizeLinearPartsFromOrder(lines, order, start)

            # this returns reversed lines in cases where it makes a better
            # tour. it does not delete the lines that were not in the tour. 
            return order, path, parts

    # this works okay-ish. Did see some examples of picking
    #  the nearest start point, at the expense of the distance
    #  to the next part because the implementation doesnt look ahead.
    # This function is not needed if the path was defined using TSP,
    #  only when the user defined an order be explicitly supplying
    #  a cuts_path or part_path. 
    def OptimizeLinearPartsFromOrder(self, lines, order, pos):
        first = self.GetNearestCenterOrEnd(lines, order, pos)
        i = order.index(first)
        order = order[i:] + order[:i]

        c = []
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
        path = LineString()        
        if len(c) > 1:
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
    #  that will be optimized later. 
    def OrderLines(self, lines, temp, alpha, iterations):
        tour = []
        # tries to figure out an order of lines to be cut
        #  using the traveling saleman algorithm
        coords, info, locked = self.GatherCenterAndEndCoords(lines)

        if len(lines) == 0:
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
            tsp = TSP.TSP(coords = coords, start_temp = temp, alpha = alpha)
            tour = tsp.anneal(locked_points=locked, iterations = iterations)
            # tsp.report_stats()                

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
        # all that is done, now just collect the points to create the path
        #  this is mostly used for debugging and drawing. 
        c = []
        for i in order:
            if lines[i].is_ring: 
                c.append((lines[i].centroid.x, lines[i].centroid.y))
            else:
                c.append(lines[i].coords[0]) 
                c.append(lines[i].coords[-1]) 
        path = LineString()
        if len(c) > 1:
            path = LineString(c) # will this break if len(order) = 0?

        # re: lines being returned. in cases where it makes a better tour,
        #  this reverses the -linear- lines to so the start and end points
        #  make a better tour. The rings are not changed
        return order, path, lines

    def GetLinesInRegion(self, region, lines):
        list = [] 
        if len(region.coords) != 2:
            region = Polygon(region.coords) # convert for intersect to work
            for j in lines:
                if region.intersects(j): # shapely has lots of functions for this.
                    list.append(j)       #  intersects() seemed to work best.
        return list

    def CreateGcode(self, tours, lines):
        gcode_cuts.append(list(part.coords))
        tours.append(tour) # collect up the cuts in each part
        for j in tour:
            gcode_cuts.append(list(cuts_in_part[j].coords))

    def toolpath(self):
        tours = [] 

        # check if user supplied a line connecting the parts
        path = self.LinesByLayer(self.path_layer)
        # get all the parts
        parts = self.LinesByLayer(self.parts_layer)
        # get all cuts
        cuts = self.LinesByLayer(self.cuts_layer)
        # get all cut_paths
        cuts_path = self.LinesByLayer(self.cutspath_layer)
    
        order = [] # the order of parts to be handled
        if len(path) > 1:
            print "there can only be one path to cut parts"
        elif len(path) == 1:
            start = path[0].coords[0]
            part_tour, path, parts = self.OrderLinesUsingPath(parts,
                                                          path[0])
        else:
            start = (0.0,0.0)
            part_tour, path, parts = self.OrderLines(parts, 
                                                 self.start_temp,
                                                 self.alpha,
                                                 self.iterations)
        cut_path = None
        cut_groups = {}
        count = 0
        for i in part_tour:
            part = parts[i]

            cut_groups[count] = {}
            cut_groups[count]['part'] = part

            cuts_in_part = self.GetLinesInRegion(part, cuts)
            cut_groups[count]['cuts'] = cuts_in_part
 
            p = self.GetLinesInRegion(part, cuts_path)
            if len(p) != 0:
                cut_path = p[0] # assume there is only one
    
            if cut_path is not None:
                tour, path, cuts_in_part = self.OrderLinesUsingPath(cuts_in_part,
                                                                    cut_path)
            else:
                tour, path, cuts_in_part = self.OrderLines(cuts_in_part,
                                                           self.start_temp,
                                                           self.alpha, 
                                                           self.iterations)
            if self.debug:
                self.AddLine(path, 'CUTS_PATH')

            cut_groups[count]['cut_tour'] = tour
            count += 1

        cut_groups = self.OptimizeAllFromTour(cut_groups)
        return cut_groups

    # perform one more optimization armed with knowledge of all the tours:
    #  change the order based on the path, and it cuts rings at the 
    #  appropriate entry point.
    def OptimizeAllFromTour(self, things):
        parts_tour = []
        parts = []
        for i in things:
            parts_tour.append(i)
            parts.append(things[i]['part'])

        # find the best par to start with, then reorder the parts
        #  based on that information
        first = self.GetNearestCenterOrEnd(parts, parts_tour, (0.0,0.0))
        i = parts_tour.index(first)
        parts_tour = parts_tour[i:] + parts_tour[:i]

        # got the order, now cut parts based on the order
        parts = self.RotateRingsUsingTour(parts_tour, parts)

        # reorganize the structure that came in
        count = 0
        final = {}
        for i in parts_tour:
            final[count] = {}
            final[count]['part'] = parts[i]
            final[count]['cuts'] = things[i]['cuts']
            final[count]['cut_tour'] = things[i]['cut_tour']
            count += 1

        things = None # get rid of it in case it was big

        # now clean up all the cuts in each part.
        # use the part start coords for rotation to re-order the cuts
        for i in final:
            # print final[i]['part']
            start = final[i]['part'].coords[0]
            if len(final[i]['cut_tour']) != 0:
                cut_tour = final[i]['cut_tour']
                cuts = final[i]['cuts']
                n = self.GetNearestCenterOrEnd(cuts, cut_tour, start)
                idx = cut_tour.index(n)
                # rotate the order
                final[i]['cut_tour'] = cut_tour[idx:] + cut_tour[:idx]
                # and since the cuts get done first, reverse them
                #  so the last one cut is near staring point of part
                final[i]['cut_tour'].reverse()
                # got the order, now recut parts
                final[i]['cuts'] = self.RotateRingsUsingTour(final[i]['cut_tour'], cuts)

        return final

    def RotateRingsUsingTour(self, tour, rings):
        new = range(len(tour))
        if len(tour) == 1: # a part came down all by it's ownsome
            new[0] = rings[0]
            if rings[0].is_ring:
                l = LineString((new[0].centroid.coords[0], (0,0)))
                pt = self.RandMinPtInLine(new[0], (0,0))
                new[0] = self.RotateRingAtPt(new[0], pt)
        if len(tour) > 1:
            new = range(len(tour))
            new[tour[0]] = self.CutRingAtNearestPoint(rings[tour[0]], 
                                                      rings[tour[1]])

            for i,j in enumerate(tour[1:]):
                new[tour[i+1]] = self.CutRingAtNearestPoint(rings[tour[i+1]], 
                                                            rings[tour[i]])

        return new

    # Approximates a min point between lines, sampling to avoid N^2
    #  testing showed with this takes .3s with a sample_limit = 1000
    #  and .04 with 300
    def RandMinPtInLines(self, l1, l2):
        sample_limit = 300
        l1 = list(l1.coords)
        l2 = list(l2.coords)
        if len(l1) > sample_limit:
            l1 = random.sample(l1, sample_limit)
        if len(l2) > sample_limit:
            l2 = random.sample(l2, sample_limit)
        first_time = 1
        for i, pt1 in enumerate(l1):
            for j, pt2 in enumerate(l2):
                if first_time == 1:
                    min =  math.hypot(pt2[0]-pt1[0], pt2[1]-pt1[1])
                    i_min = i
                    j_min = j
                first_time = 0
                d = math.hypot(pt2[0]-pt1[0], pt2[1]-pt1[1])
                if d < min:
                    i_min = i
                    j_min = j
                    min = d
        return(i_min, j_min)

    # also works by sampling to avoid N^2
    def RandMinPtInLine(self, l1, pt2):
        l1 = list(l1.coords)
        sample_limit = 100000 # testing showed this can be fairly big
        if len(l1) > sample_limit:
            l1 = random.sample(l1, sample_limit)
        first_time = 1
        for i, pt1 in enumerate(l1):
            if first_time == 1:
                min =  math.hypot(pt2[0]-pt1[0], pt2[1]-pt1[1])
                i_min = i
            first_time = 0
            d = math.hypot(pt2[0]-pt1[0], pt2[1]-pt1[1])
            if d < min:
                i_min = i
                min = d
        return(i_min)

    def CutRingAtNearestPoint(self, r1, r2):
        (pt1, pt2) = self.RandMinPtInLines(r1,r2)
        if r1.is_ring:
            r1 = self.RotateRingAtPt(r1, pt1)
        return r1

    def RotateRingAtPt(self, line, i):
        # Changes starting point of a ring to point in array
        coords = list(line.coords)
        if i != 0 and i < len(coords):
            coords = coords[i:-1] + coords[:i+1]
        return LineString(coords)

    # no longer used. Replaced by RotateRingAtPt()
    def RotateRing(self, line, distance):
        # Changes starting point of a ring to point defined by distance
        if distance <= 0.0 or distance >= line.length:
            return [LineString(line)]

        traveled = []
        traveled_length = 0
        count = 0
        coords = list(line.coords)
        traveled.append(coords[0])
        test_length = LineString(coords[:2]).length
        
        while distance >= test_length:
            count += 1
            traveled.append(coords[count])
            test_length = LineString(coords[:count+2]).length
            traveled_length = LineString(traveled).length

        diff = distance - traveled_length

        pt = LineString((coords[count], 
                         coords[count+1])).interpolate(diff)

        if diff == 0:
            coords = coords[:-1] # remove the last coord
            coords = coords[1:] # remove the first coord
            coords = coords[count:] # truncate to the travel point
            coords.insert(0, pt.coords[0]) # add the new coord
        else:
            traveled.append(pt.coords[0]) # add the new coord to traveled.
            coords.insert(count+1, pt.coords[0]) # add the new coord
            coords = coords[:-1] # remove the last coord
            coords = coords[count+1:] # truncate to the travel point

        return LineString(coords + traveled)

    # returns the point where line1 crosses line2
    def GetIntersectionLocation(self, l1, l2):
        pt = Point()

        x = l1.intersection(l2)
        # shapley's intersections can return a lot of things, see docs
        if x.wkt == 'GEOMETRYCOLLECTION EMPTY':
            pass # return nothing
        elif re.match('^POINT', x.wkt): 
            pt = Point(x.coords[0])
        elif re.match('^MULTI', x.wkt): 
            # abitrarily pick one point
            pt = Point(x[0].coords[0])
        else:
            print 'dunno what intersection passed me'

        return pt

if __name__ == '__main__':
    tp=Toolpath()
    tp.LoadIniData("./tool_interface.ini")

    import random

    tp.LoadRawData()

    all_lines = tp.toolpath()

    # do this to debug and have a look paths and parts
    if tp.debug_pic:
        tp.DrawRawData(tp.debug_file_name)

    tp.DrawPartsAndCuts("thing2.png", all_lines)

    sys.exit(1)

    g = gcode.Gcode(tp)

    p = g.MakePhrase()
    title = '(' + p + ')' + '\n\n'
    g.append(title)
    g.add_header()

    for i in gcode_cuts:
        g.write_polyline(i)

    g.add_footer()

    g.write_gcode()

    print '(' + p + ')'
