#!/usr/bin/env python

import rhinoscriptsyntax as rs
import Rhino
import random
import math
import os
import sys
import re
from math import sqrt

class Toolpath:
    def __init__(self, file_name):
        self.ini_file = file_name
        self.verbose = 0
        self.gcode = ""

        from os.path import join as pjoin
        output_file = rs.GetSettings(file_name, 'GCODE', 'output_file')

        self.parts_layer = rs.GetSettings(file_name, 'LAYERS', 'parts_layer')
        self.cuts_layer = rs.GetSettings(file_name, 'LAYERS', 'cuts_layer')
        self.path_layer = rs.GetSettings(file_name, 'LAYERS', 'parts_path_layer')
        self.cutspath_layer = rs.GetSettings(file_name, 'LAYERS', 'cuts_path_layer')
        self.showpaths = self.boolean(rs.GetSettings(file_name, 'LAYERS', 'showpaths'))

        self.iterations = int(rs.GetSettings(file_name, 'TSP', 'iterations'))
        self.start_temp = float(rs.GetSettings(file_name, 'TSP', 'start_temp'))
        self.alpha = float(rs.GetSettings(file_name, 'TSP', 'alpha'))

        self.layer_colors = {}
        self.layer_colors[self.parts_layer] = self.Str2Array(rs.GetSettings(file_name, 'LAYERS', 'parts_color'))
        self.layer_colors[self.cuts_layer] = self.Str2Array(rs.GetSettings(file_name, 'LAYERS', 'cuts_color'))
        self.layer_colors[self.path_layer] = self.Str2Array(rs.GetSettings(file_name, 'LAYERS', 'path_color'))
        self.layer_colors[self.cutspath_layer] = self.Str2Array(rs.GetSettings(file_name, 'LAYERS', 'cutspath_color'))

        self.tmp_layer_extension = ".tmp"

        for layer in (self.parts_layer, self.cuts_layer, self.path_layer, self.cutspath_layer):
            
            if (not rs.IsLayer(layer)):
                rs.AddLayer(layer)
                rs.LayerColor(layer, self.layer_colors[layer])


    # Gets selected curves and polylines from parts, cuts, paths layers
    #  converts them to simple polylines
    def CopyLinesToNewLayers(self): 
        objects = rs.SelectedObjects()  
        count = 0
        for object_id in objects:
            layer = rs.ObjectLayer(object_id)
            if rs.IsCurve(object_id) and layer == self.parts_layer:
                count+=1

        if count == 0:
            print "no part was selected"
            return False

        # make new layers
        part_layers = (self.parts_layer, self.cuts_layer)
        for layer in (self.parts_layer, self.cuts_layer, self.path_layer, self.cutspath_layer):
            new_layer = layer + self.tmp_layer_extension
            if rs.IsLayer(new_layer):
                rs.PurgeLayer(new_layer)
            rs.AddLayer(new_layer)
            rs.LayerColor(new_layer, color = self.layer_colors[layer])

        object_list =[]
        # collect everything that was selected
        for object_id in objects:
            layer = rs.ObjectLayer(object_id)
            if rs.IsCurve(object_id) and layer in part_layers:
                object_list.append(object_id)

        # now find if you have any paths
        # its okay if we didnt find any
        for object_id in rs.SelectedObjects():
            if (rs.IsPolyline(object_id) and 
                (rs.ObjectLayer(object_id) == self.path_layer or 
                 rs.ObjectLayer(object_id) == self.cutspath_layer)):
                object_list.append(object_id)

        # got all the objects, now make sure curves are actually polylines
        # and put them on a new set of layers
        self.ConvertAndLoadCurves(object_list)

        # I hope this over writing the layer names doesnt 
        #  catch up to me later. 
        self.parts_layer = self.parts_layer + self.tmp_layer_extension
        self.cuts_layer = self.cuts_layer + self.tmp_layer_extension
        self.path_layer = self.path_layer + self.tmp_layer_extension
        self.cutspath_layer = self.cutspath_layer + self.tmp_layer_extension
        return True

    # converts objects that are curves to a polyline
    #   copies polylines to a new polyline
    def ConvertAndLoadCurves(self, list):
        for object_id in list:
            id = rs.CopyObject(object_id) # make a copy
            rs.SimplifyCurve(id) # make sure it's simple...
            # curves can be polylines or not polylines
            #  for the ones that are not....
            if rs.IsCurve(id) and not (rs.IsPolyline(id)):
                id = rs.ConvertCurveToPolyline(id, angle_tolerance=1, 
                                               tolerance=0.01, delete_input=True)
            new_layer = rs.ObjectLayer(object_id) + self.tmp_layer_extension 
            rs.ObjectLayer(id, layer = new_layer) # set the layer of the new object

    def Str2Array(self, s):
        return(tuple(int(i) for i in s.split(',')))

    def MakeLine(self, line, layer):
        id = rs.AddPolyline(line)
        rs.ObjectLayer(id, layer)

    def ShowPaths(self, struct):
        parts = struct['parts']
        coords = []
        draw_layer = "Default"
        if not rs.IsLayer(draw_layer):
            rs.AddLayer(draw_layer)
        for part in parts:
            pt = rs.CurveStartPoint(part)
            coords.append((pt[0], pt[1], pt[2]))
            if not rs.IsCurveClosed(part):
                pt = rs.CurveEndPoint(part)
                coords.append((pt[0], pt[1], pt[2]))
        if coords:
            coords.insert(0, (0.0, 0.0, 0.0))
            self.MakeLine(coords, draw_layer)

        for part in parts:
            cuts = struct[part]['cuts']
            if cuts:
                coords = []
                pt = rs.CurveEndPoint(part)
                if rs.IsCurveClosed(part):
                    pt = rs.CurveStartPoint(part)
                coords.append((pt[0], pt[1], pt[2]))
                for cut in cuts:
                    pt = rs.CurveStartPoint(cut)
                    coords.append((pt[0], pt[1], pt[2]))
                    if not rs.IsCurveClosed(cut):
                        pt = rs.CurveEndPoint(cut)
                        coords.append((pt[0], pt[1], pt[2]))
                if coords:
                    self.MakeLine(coords, draw_layer)

    def FlushObjects(self):
        for l in (self.parts_layer, self.cuts_layer, self.path_layer, self.cutspath_layer):
            rs.PurgeLayer(l)


    def FindToolpath(self):
        if not self.CopyLinesToNewLayers():
            return

        tours = [] 
        # check if we have the objects we need
        parts = rs.ObjectsByLayer(self.parts_layer)
        cuts = rs.ObjectsByLayer(self.cuts_layer)
        path = rs.ObjectsByLayer(self.path_layer) # optional
        cuts_path = rs.ObjectsByLayer(self.cutspath_layer) # optional
    
        if len(path) > 1:
            print "there can only be one path to cut parts"
        elif len(path) == 1:
            pt = rs.CurveStartPoint(path[0])
            print "got cuts path"
            part_tour = self.OrderLinesUsingPath(parts, path[0])
        else:
            part_tour = self.OrderLines(parts)
            part_tour = self.ReorderByNearestPoint(part_tour, (0,0,0))

        cut_path = None
        cut_groups = {}
        cut_groups['parts'] = part_tour
        for part in part_tour:
            cut_groups[part] = {}
            # this finds cuts that are fully contained in the ROI
            cuts_in_part = self.GetLinesInRegion(part, cuts)

            p = self.GetLinesInRegion(part, cuts_path)
            if p:
                # this assumes length of list p is 1
                cuts_tour = self.OrderLinesUsingPath(cuts_in_part,p[0])
            else:
                cuts_tour = self.OrderLines(cuts_in_part)

            cut_groups[part]['cuts'] = cuts_tour

        # cut_groups = self.OptimizeAllFromTour(cut_groups)

        return cut_groups

    def GetRawPoints(self, line):
        c = []
        # print rs.ObjectType(line)
        for pt in rs.PolylineVertices(line):
            c.append((pt[0],pt[1]))
        return c

    def GetLinesInRegion(self, region, lines):
        list = [] 
        coords = rs.PolylineVertices(region)
        if len(coords) == 2:
            return

        for line in lines:
            success = True
            for pt in rs.PolylineVertices(line):
                if not self.PointInRegion(pt, region):
                    success = False
                    break
            if success:
                list.append(line)

        return list

    # this bails as soon as it finds a point not in the region
    #  only works in 2d
    def PointInRegion(self, pt, line):
        poly = rs.PolylineVertices(line)
        n = len(poly)
        inside =False
        
        p1x,p1y,p1z = poly[0]
        for i in range(n+1):
            p2x,p2y,p2z = poly[i % n]
            if pt[1] > min(p1y,p2y):
                if pt[1] <= max(p1y,p2y):
                    if pt[0] <= max(p1x,p2x):
                        if p1y != p2y:
                            xinters = (pt[1]-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or pt[0] <= xinters:
                            inside = not inside
            p1x,p1y = p2x,p2y

        return inside

    def GetIntersectionDistance(self, c1, c2):
        d = -1
        start = rs.CurveStartPoint(c1)
        int_list = rs.CurveCurveIntersection(c1, c2)
        if int_list:
            # use first element in results
            intersection = int_list[0] 
            # this means it was not an overlap
            if intersection[0] == 1: 
                pt = intersection[1]
                d = rs.Distance(start,pt)
        return d

    # use a user defined path to find interections with all the
    #  objects to determine the order that objects should be cut
    def OrderLinesUsingPath(self, lines, path):
        if len(lines) == 0:
            # there are no lines to order
            print "no lines sent to OrderCutsUsingPath"
            return order

        coords = rs.PolylineVertices(path)
        num = len(coords)
        start = coords[0]
        results = {}
        travel = 0 # this accumulates distance along the path

        for i,q in enumerate(coords):
            if i == num - 1:
                break
            segment = rs.AddPolyline([coords[i], coords[i+1]])
            for line in lines:
                d = self.GetIntersectionDistance(segment, line)
                if d != -1:
                    results[line] = d + travel
            rs.DeleteObject(segment)
            travel += rs.Distance(coords[i], coords[i+1])

        order = []
        for x in sorted(results, key=results.get):
            order.append(x)

        # we have the order, this rearranges the linear lines to improve cutting 
        order = self.OptimizeLinearPartsFromOrder(order, start)

        # this returns reversed lines in cases where it makes a better
        # tour. it does not delete the lines that were not in the tour. 
        return order

    # this works okay-ish. Did see some examples of picking
    #  the nearest start point, at the expense of the distance
    #  to the next part because the implementation doesnt look ahead.
    # This function is not needed if the path was defined using TSP,
    #  only when the user defined an order be explicitly supplying
    #  a cuts_path or part_path. 
    def OptimizeLinearPartsFromOrder(self, order, pt):
        # think I'm retiring this part
        # first = self.ReorderByNearestPoint(lines, order, pos)
        # i = order.index(first)
        # order = order[i:] + order[:i]

        pos = rs.AddPoint(pt)

        path = []
        for line in order:
            if rs.IsCurveClosed(line): 
                pt = rs.CurveAreaCentroid(line)
                pos = pt[0]
            else: 
                d1 = rs.Distance(pos, rs.CurveStartPoint(line))
                d2 = rs.Distance(pos, rs.CurveEndPoint(line))
                if d2 < d1:
                    rs.ReverseCurve(line)
                pos = rs.CurveEndPoint(line)

        DeleteObject(pos)
        return order

    def ReorderByNearestPoint(self, lines, start):
        if len(lines) == 1:
            return lines

        # collect up all the points to test
        min_line = None
        count = 0
        for line in lines:
            if rs.IsCurveClosed(line): 
                pos = rs.CurveAreaCentroid(line)
                r = rs.Distance(start, pos)
                dis = r[0]
            else: 
                d1 = rs.Distance(start, rs.CurveStartPoint(line))
                d2 = rs.Distance(start, rs.CurveEndPoint(line))
                dis = min(d1, d2)
            if min_line is None or dis <= min_dis:
                min_dis = dis
                min_line = count
            count += 1
        return lines[min_line:] + lines[:min_line]

    def GatherCenterAndEndCoords(self, lines):
        # nothing special just used to grab centers of ring objects
        #  and the end points of linear ones
        coords = []
        locked = []
        info = {} # helps record what type of thing was ordered
        tour_pos = 0
        for l in lines:
            # if an object is circular, arbitrarily pick its center
            # see: http://toblerity.github.com/shapely/manual.html
            #  to understand is_ring/is circular
            if rs.IsCurveClosed(l): 
                info[tour_pos] = {}
                pt = rs.CurveAreaCentroid(l)
                coords.append((pt[0][0],pt[0][1],0.0))
                info[tour_pos]['line_id'] = l
                info[tour_pos]['type'] = 'ring'
                info[tour_pos]['pt'] = pt
                tour_pos += 1
            # if an object is linear, create two points,
            #   the start and the end
            else:
                info[tour_pos] = {}
                info[tour_pos]['line_id'] = l
                info[tour_pos]['type'] = 'start'
                pt = rs.CurveStartPoint(l)
                pt1 = (pt[0], pt[1], 0.0)
                info[tour_pos]['pt'] = pt1

                info[tour_pos+1] = {}
                info[tour_pos + 1]['line_id'] = l
                info[tour_pos + 1]['type'] = 'end'
                pt = rs.CurveEndPoint(l)
                pt2 = (pt[0], pt[1], 0.0)
                info[tour_pos + 1]['pt'] = pt2

                coords.append(pt1) # gather first coord
                coords.append(pt2) # last
                locked.append((tour_pos,tour_pos + 1))
                tour_pos += 2
        return coords, info, locked

    # This returns list of object_ids are returned corresponding
    #   to the best shortest path between objects. this reverses 
    #   the -linear- lines to so the start and end points
    #   make a better tour. The rings are not changed
    # it also makes a new line that indicates the path for drawing
    #   later on
    # this works pretty good. One issue is it does not 'cut' rings to find
    #   that will be optimized later. 
    def OrderLines(self, lines):
        tour = []
        coords, info, locked = self.GatherCenterAndEndCoords(lines)

        if len(lines) == 0:
            tour = []
        elif len(lines) == 1:
            tour = [0]
        elif len(lines) == 2:
            tour = [0,1,2]
            if len(coords) == 2:
                tour = [0,1]
        # worry about what this does with just two parts
        #  consider if parts IsClosed and not IsClosed
        else:
            # create a path. This will this return an order of the 
            #  center of ring-shaped lines, and the start or end 
            #  points of linear lines
            tsp = TSP(self)
            tour = tsp.anneal(coords, locked)

            # tsp.report_stats()                

        # getting tour is great, but it is not the actual order of lines.
        #  it is the tour of points defined by the centroid
        #  of rings, the start _and_ ends of linear lines.
        # Do this to get the actual order of lines:
        order = []
        for i in tour:
            object_id = info[i]['line_id']
            if object_id not in order:
                order.append(object_id)
                if info[i]['type'] == 'end':
                    rs.ReverseCurve(object_id)

        return order

    # perform one more optimization armed with knowledge of all the tours:
    #  change the order based on the path, and it cuts rings at the 
    #  appropriate entry point.
    #
    # the thing getting passed to this function is:
    # structure['parts'] = list of parts
    # structure[part]['cuts'] = the object_ids of reflecting order of cuts
    def OptimizeAllFromTour(self, struct):
        # find the best part to start with, then reorder the parts
        #  based on that information

        # got the order, now cut parts based on the order
        new_parts, replace = self.RotateRingsUsingTour(parts)

        struct['parts'] = new_parts
        # new parts were made, so they get loaded back into the structure
        for part in parts:
            struct[replace[part]] = struct.pop(part)

        # now clean up all the cuts in each part.
        # use the part start coords for rotation to re-order the cuts
        for part in new_parts:
            start = rs.CurveStartPoint(part)
            cuts = struct[part]['cuts']
            if len(cuts) != 0:
                c = self.ReorderByNearestPoint(cuts, rs.CurveStartPoint(part))
                # and since the cuts get done first, reverse them
                #  so the last one cut is near staring point of part
                c.reverse()
                # got the order, now recut parts
                cuts, replace = self.RotateRingsUsingTour(c)
                struct[part]['cuts'] = cuts

        return struct


    # Does what it says. 
    #  also returns improved parts, and a dictionary to 
    #  figure out what happened to the old parts
    def RotateRingsUsingTour(self, tour):
        new = []
        if len(tour) == 1: # a part came down all by it's ownsome
            line = tour[0]
            if rs.IsCurveClosed(line):
                results = rs.PointClosestObject((0,0,0), [line])
                line = self.RotateRingAtPt(line, results[1])
            new.append(line)

        if len(tour) > 1:
            old_id = self.CutRingAtNearestPoint(tour[0], tour[1])
            new.append(old_id)
            for i,j in enumerate(tour[1:]):
                id = self.CutRingAtNearestPoint(tour[i+1],old_id)
                new.append(id)
                old_id = id

        replace = {}
        count = 0
        for x in new:
            replace[tour[count]] = x
            count += 1
        return new, replace

    def CutRingAtNearestPoint(self, r1, r2):
        if rs.IsCurveClosed(r1):
            results = rs.CurveClosestObject(r1,[r2])
            r1 = self.RotateRingAtPt(r1, results[2])
        return r1

    def RotateRingAtPt(self, line, point):
        objs = [line]
        results = rs.PointClosestObject(point, objs)
        if results:
            pt3 = results[1]
            # find which segment of the polyline has the point
            coords = rs.PolylineVertices(line)
            add_new = True
            for i,j in enumerate(coords[1:]):
                if self.IsBetween(coords[i], coords[i+1], pt3):
                    if (rs.Distance(coords[i], pt3) > 0.0001 and
                        rs.Distance(coords[i+1], pt3) > 0.0001):
                        i+=1
                        coords.insert(i, pt3)
                    break 
            # now reorganize the ring 
            coords = coords[i:-1] + coords[:i+1]
        else:
            print "odd, RotateRingAtPt did not find a object close to pt"

        new = rs.AddPolyline(coords)
        rs.ObjectLayer(new, rs.ObjectLayer(line))
        rs.DeleteObject(line) # bye bye
        return new


    def IsBetween(self, pt1, pt2, pt3):
        # from http://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
        epsilon = 0.00000001

        crossproduct = (pt3[1] - pt1[1]) * (pt2[0] - pt1[0]) - (pt3[0] - pt1[0]) * (pt2[1] - pt1[1])

        if abs(crossproduct) > epsilon : return False   # (or != 0 if using integers)

        dotproduct = (pt3[0] - pt1[0]) * (pt2[0] - pt1[0]) + (pt3[1] - pt1[1])*(pt2[1] - pt1[1])
        if dotproduct < 0 : return False

        squaredlengthba = (pt2[0] - pt1[0])*(pt2[0] - pt1[0]) + (pt2[1] - pt1[1])*(pt2[1] - pt1[1])
        if dotproduct > squaredlengthba: return False

        return True


    def collinear(self, pt1, pt2, pt3):
        # Return true iff a, b, and c all lie on the same line.
        return (pt2[0] - pt1[0]) * (pt3[1] - pt1[1]) == (pt3[0] - pt1[0]) * (pt2[1] - pt1[1])

    def within(self, p, q, r):
        # Return true iff q is between p and r (inclusive)."
        return p <= q <= r or r <= q <= p


    def boolean(self, value):
        if value == "True":
            return True
        if value == "False":
            return False


class TSP:

    def __init__(self,parent):
        self.reset()
        self.parent = parent
        self.start_temp = parent.start_temp
        self.alpha = parent.alpha
        self.iterations = parent.iterations

    # Not tested. It's meant to be called when the user
    #   lots of new parameters.
    def reset(self):
        self.best=None
        self.best_score=None
        self.start_temp = None
        self.locked_points = None
        self.alpha=None
        self.coords = None
        self.current=None
        self.iterations=None
        self.matrix = None

    def check(self):
        if self.coords is None:
            print 'tsp cant run without coords, call tsp.set_coords'

        if self.start_temp is None:
            print 'tsp cant run without self.start_temp = int'

        if self.alpha is None:
            print 'tsp cant run without self.alpha = int'

        if self.iterations is None:
            print 'tsp cant run without self.iterations = int'

        if self.locked_points is None:
            print 'tsp cant run with self.locked_points = None'

    def set_coords(self, coords):
        self.coords = coords
        self.current=range(len(coords)) # the current tour of points
        self.matrix = self.cartesian_matrix(coords)
    
    # Total up the total length of the tour based on the distance matrix
    def objective_function(self,solution):
        score=0
        num_cities=len(solution)
        for i in range(num_cities):
            j=(i+1)%num_cities
            city_i=solution[i]
            city_j=solution[j]
            score+=self.matrix[city_i,city_j]
        score *= -1
        if self.best is None or score > self.best_score:
            self.best_score=score
            self.best=solution
        return score

    def kirkpatrick_cooling(self):
        T=self.start_temp
        while True:
            yield T
            T=self.alpha*T

    def p_choice(self, prev_score,next_score,temperature):
        if next_score > prev_score:
            return 1.0
        else:
            return math.exp( -abs(next_score-prev_score)/temperature )

    def rand_seq(self,size,positions):
        values=range(size)
        inc = 0
        for i in positions:
            del values[i-inc]
            inc += 1
    
        size -= len(positions)
    
        for i in xrange(size):
            # pick a random index into remaining values
            j=i+int(random.random()*(size-i))
            # swap the values
            values[j],values[i]=values[i],values[j]
            # restore the value if it is in our special list
            yield values[i] 
    
    def all_pairs(self,size,positions):
        '''generates all i,j pairs for i,j from 0-size'''
        for i in self.rand_seq(size, positions):
            for j in self.rand_seq(size,positions):
                yield (i,j)
    
    # Return all variations where the 
    #  section between two cities are swappedd
    def reversed_sections(self):
        positions = self.find_locked_points()
        for i,j in self.all_pairs(len(self.current), positions):
            # print 'ij %d %d' % (i, j)
            if i != j and abs(i-j) != 1:
                copy=self.current[:]
                if i < j:
                    copy[i:j]=reversed(self.current[i:j])
                else:
                    copy[j:i]=reversed(self.current[j:i])
                    copy.reverse()
                if copy != self.current: # no point returning the same tour
                    # print 'copy %s' % (copy)
                    yield copy

    def find_locked_points(self):
        # points is a list of positions that are linked to 
        #  each element in the array. For this list:
        #  [pos1, pos2, pos3]
        #  The locked_points refer the comma's separating the positions
        #  [,pos1, pos2, pos3,]. 
        # there was not a strong logical reason for doing this, this
        #  just won compared to a couple other attempts. 
        l = []
        list = self.current
        for i in self.locked_points:
            (e1, e2) = i
            p1 = list.index(e1)
            p2 = list.index(e2)
            if p1 < p2:
                if (p2 - p1) != 1:
                    print "p1 and p2 not next to each other"
                    sys.exit(1)
                l.append(p2)
            else:
                if (p1 - p2) != 1:
                    print "p2 and p1 not next to each other"
                    sys.exit(1)
                l.append(p1)
        return sorted(l)

    # create a distance matrix for the city coords 
    #   that uses straight line distance
    def cartesian_matrix(self, coords):
        matrix={}
        for i,pt1 in enumerate(coords):
            for j,pt2 in enumerate(coords):
                dx,dy=pt1[0]-pt2[0],pt1[1]-pt2[1]
                dist=sqrt(dx*dx + dy*dy)
                matrix[i,j]=dist
        return matrix

    # read coordinates file return the distance matrix.
    #  coords should be stored as comma separated floats, 
    #  one x,y pair per line.
    def read_coords(self,coord_file):
        coords=[]
        for line in coord_file:
            x,y=line.strip().split(',')
            coords.append((float(x),float(y)))
        return coords

    def write_tour_to_img(self,coords,tour,locked_points,title,img_file):
        # a cheezebag display of the tour, doesnt even scale small routes
        padding=20
        # shift all coords in a bit
        coords=[(x+padding,y+padding) for (x,y) in coords]
        maxx,maxy=0,0
        for x,y in coords:
            maxx=max(x,maxx)
            maxy=max(y,maxy)
        maxx+=padding
        maxy+=padding
        img=Image.new("RGB",(int(maxx),int(maxy)),color=(255,255,255))
        
        font=ImageFont.load_default()
        d=ImageDraw.Draw(img);
        num_cities=len(tour)
        for x,y in coords:
            x,y=int(x),int(y)
            d.ellipse((x-5,y-5,x+5,y+5),outline=(0,0,0),fill=(196,196,196))
    
        inc = 0
        for i in range(num_cities):
            j=(i+1)%num_cities
            city_i=tour[i]
            city_j=tour[j]
            x1,y1=coords[city_i]
            x2,y2=coords[city_j]
            d.line((int(x1),int(y1),int(x2),int(y2)),fill=(0,0,0))
            d.text((int(x1)+7,int(y1)-5),str(i),font=font,fill=(32,32,32))
            inc += 1
        
        for i in locked_points:
            (x, y) = i
            (x1, y1) = coords[x]
            (x2, y2) = coords[y]
            x,y=int(x1),int(y1)
            d.ellipse((x-5,y-5,x+5,y+5),outline=(0,0,0),fill=(255,0,0))
    
            x,y=int(x2),int(y2)
            d.ellipse((x-5,y-5,x+5,y+5),outline=(0,0,0),fill=(255,0,0))
    
        d.text((1,1),title,font=font,fill=(0,0,0))
        
        del d
        img.save(img_file, "PNG")
    
    def report_stats(self):
        print self.matrix
        print self.coords 
        print self.current
        print self.best
        print self.best_score
        print self.start_temp 
        print self.locked_points 
        print self.alpha
        print self.iterations

    # Where all the fun happens.
    def anneal(self, coords, locked_points):
        self.set_coords(coords)
        self.locked_points = locked_points

        current_score=self.objective_function(self.current)
        num_evaluations=1
    
        self.check()

        cooling_schedule=self.kirkpatrick_cooling()
        
        for temperature in cooling_schedule:
            done = False
            # examine moves around our current position
            for next in self.reversed_sections():
                if num_evaluations >= self.iterations:
                    done=True
                    break
                
                next_score=self.objective_function(next)
                num_evaluations+=1
                
                # print (current_score,next_score,temperature)
                # probablistically accept this solution
                # always accepting better solutions
                p=self.p_choice(current_score,next_score,temperature)
                if random.random() < p:
                    self.current=next
                    current_score=next_score
                    break
            # see if completely finished
            if done: break
        
        # self.report_stats()

        self.iterations = num_evaluations
        # starts with a list of coordinates
        #  returns a path - the list of numbers that point to the original
        #  list of coordinates, giving the order of coordinates that
        #  compose the shortest path between all coordinates
        return self.best


class Gcode:
    def __init__(self, FileName):
        self.gcode_string = ""

        self.dictionary_file = rs.GetSettings(FileName, 'GCODE', 'dictionary')
        self.move_feed_rate = int(rs.GetSettings(FileName, 'GCODE', 'move_feed_rate'))
        self.cut_feed_rate = int(rs.GetSettings(FileName, 'GCODE', 'cut_feed_rate'))
        self.dwell_time = float(rs.GetSettings(FileName, 'GCODE', 'dwell_time'))
        self.use_cut_variable = self.boolean(rs.GetSettings(FileName, 'GCODE', 'use_cut_variable'))
    
        from os.path import join as pjoin
        self.output_file = pjoin(rs.GetSettings(FileName, 'GCODE', 'ncfile_dir'), 
                                 rs.GetSettings(FileName, 'GCODE', 'output_file'))
    
        if self.use_cut_variable:
            self.cut_speed = '#<cutfeedrate>'
        elif len(self.cut_feed_rate) > 0:
            self.cut_speed = self.cut_feed_rate
        else:
            self.cut_speed = 10
    
        if self.use_cut_variable:
            self.move_speed = '#<movefeedrate>'
        elif len(self.move_feed_rate) > 0:
            self.move_speed = self.move_feed_rate
        else:
            self.move_speed = 10
    
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

    def write_gcode(self): 
        f = self.output_file
        try:
            with open(f, 'w') as the_file:
                the_file.write(self.gcode_string)
            print 'wrote (%s) in %s' % (p, g.output_file)
        except IOError: 
            print "%s is not available" % f

    def write_polyline(self, line):
        poly = rs.PolylineVertices(line)
        pt = poly[0]
        self.move_no_cut(pt[0], pt[1])

        self.oxygen_on()
        self.cutting_tool_on()
        self.add_EOL()
        for pt in poly[1:]:
            self.move(pt[0], pt[1])

        self.cutting_tool_off()
        self.oxygen_off()
        self.add_EOL()

    def move(self, x, y):
        self.append('G01 X%0.4lf Y%0.4lf F%s\n' % (x, y, self.cut_speed))

    def move_no_cut(self, x, y):
        self.cutting_tool_off()
        self.append('G00 X%0.4lf Y%0.4lf F%s\n' % (x, y, self.move_speed))
        self.add_EOL()

    def add_EOL(self):
        self.append('\n')

    def cutting_tool_off(self):
        self.append('M65 P2 (LASER OFF)\n')

    def cutting_tool_on(self):
        self.append('M64 P2 (LASER ON)\nG4 P%s\n' % (self.dwell_time))

    def oxygen_on(self):
        self.append('M64 P1 (GAS LINE ON)\n')

    def oxygen_off(self):
        self.append('M65 P1 (GAS LINE OFF)\n')

    def add_footer(self):
        self.cutting_tool_off()
        self.append('M65 P0 (VENTILATION OFF)\n')
        self.append('G1 X0.000 Y0.000 F%s (HOME AGAIN HOME AGAIN)\n' % self.move_speed)
        self.append('M2')
        self.add_EOL()

    def add_header(self):
        header = ('#<movefeedrate>=%s\n'
                  '#<cutfeedrate>=%s\n'
                  'G17 G20 G40 G49 S10\n'
                  'G80 G90\n'
                  'G92 X0 Y0 (SET CURRENT POSITION TO ZERO)\n'
                  'G64 P0.005\n'
                  'M64 P0 (VENTILATION ON)\n'
                  'M65 P1 (GAS LINE OFF)\n'
                  'M65 P2 (LASER OFF)\n\n') % (self.move_feed_rate, self.cut_feed_rate)
        self.append(header)

    def append(self, s):
        self.gcode_string = self.gcode_string + s

    def prepend(self, s):
        self.gcode_string = s + self.gcode_string

    def boolean(self, value):
        if value == "True":
            return True
        if value == "False":
            return false


if __name__ == '__main__':
    g = Gcode("polyline_dump.ini")
    tp=Toolpath("polyline_dump.ini")

    struct = tp.FindToolpath()

    if struct:

        if tp.showpaths:
            tp.ShowPaths(struct)

        p = g.MakePhrase()

        title = '(' + p + ')' + '\n\n'
        g.append(title)
        g.add_header()

        parts = struct['parts']
        for part in parts:
            cuts = struct[part]['cuts']
            for cut in cuts:
                g.write_polyline(cut)
            g.write_polyline(part)

        g.add_footer()

        g.write_gcode()

        tp.FlushObjects()
