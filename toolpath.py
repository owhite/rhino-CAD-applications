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
        self.showpaths = self._boolean(rs.GetSettings(file_name, 'LAYERS', 'showpaths'))

        self.iterations = int(rs.GetSettings(file_name, 'TSP', 'iterations'))
        self.start_temp = float(rs.GetSettings(file_name, 'TSP', 'start_temp'))
        self.alpha = float(rs.GetSettings(file_name, 'TSP', 'alpha'))

        self.layer_colors = {}
        self.layer_colors[self.parts_layer] = self.Str2Array(rs.GetSettings(file_name, 'LAYERS', 'parts_color'))
        self.layer_colors[self.cuts_layer] = self.Str2Array(rs.GetSettings(file_name, 'LAYERS', 'cuts_color'))
        self.layer_colors[self.path_layer] = self.Str2Array(rs.GetSettings(file_name, 'LAYERS', 'path_color'))
        self.layer_colors[self.cutspath_layer] = self.Str2Array(rs.GetSettings(file_name, 'LAYERS', 'cutspath_color'))

        self.tmp_layer_extension = ".tmp"

        self.backup_dir = rs.GetSettings(file_name, 'BACKUP', 'backup_dir')
        self.backup_file_ext = "3dm"
        self.backup_file_count = int(rs.GetSettings(file_name, 'BACKUP', 'backup_file_count'))
        self.backup_file_count -= 1

        for layer in (self.parts_layer, self.cuts_layer, self.path_layer, self.cutspath_layer):
            
            if (not rs.IsLayer(layer)):
                rs.AddLayer(layer)
                rs.LayerColor(layer, self.layer_colors[layer])
                

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
    

    # Gets selected curves and polylines from parts, cuts, paths layers
    #  makes sure they're flat. 
    def EverythingIsFlat(self): 
        objects = rs.SelectedObjects()  
        for object_id in objects:
            if rs.IsCurve(object_id):
                if not rs.IsCurveInPlane(object_id):
                    return False
        return True
            

    # Gets selected curves and polylines from parts, cuts, paths layers
    #  converts them to simple polylines
    def CopyLinesToNewLayers(self): 
        objects = rs.SelectedObjects()  
        count = 1
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


    def FindToolpath(self, make_backup_file):
        if not self.EverythingIsFlat():
            print "found a curve that is not in the active construction plane"
            return

        if make_backup_file:
            self.AddNewBackupFile()

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

        # GetLinesInRegion() takes long time because it does an all v all pts search
        #  going to reduce the number of the polylines
        reduced_list = []
        r_lookup = {}
        for c in cuts:
            r = self.ReduceCurve(c)
            # print "reduced cut: %d %d" % (len(rs.PolylineVertices(c)), len(rs.PolylineVertices(r)))
            r_lookup[r] = c
            reduced_list.append(r)

        for part in part_tour:
            r_part = self.ReduceCurve(part)
            # print "reduced part: %d %d" % (len(rs.PolylineVertices(part)), len(rs.PolylineVertices(r_part)))

            cut_groups[part] = {}
            # this finds cuts that are fully contained in the ROI
            results = self.GetLinesInRegion(r_part, reduced_list)
            cuts_in_part = []
            for r in results:
                cuts_in_part.append(r_lookup[r])

            p = self.GetLinesInRegion(part, cuts_path)


            if p:
                # this assumes length of list p is 1
                cuts_tour = self.OrderLinesUsingPath(cuts_in_part,p[0])
            else:
                cuts_tour = self.OrderLines(cuts_in_part)


            rs.DeleteObject(r_part)
            cut_groups[part]['cuts'] = cuts_tour

        # whack these
        rs.DeleteObjects(reduced_list)

        # cut_groups = self.OptimizeAllFromTour(cut_groups)

        return cut_groups

    def ReduceCurve(self, c):
        distance = 0.02
        coords = rs.PolylineVertices(c)
        length = len(coords)

        # who cares if it's not that long?
        if length < 20: 
            return rs.AddPolyline(coords)

        thing = []
        count = 0
        travel = 0
        for i in range(length-1):
            if i == 0:
                thing.append(coords[i])

            travel += rs.Distance(coords[i], coords[i+1])

            if travel > distance:
                thing.append(coords[i+1])
                travel = 0
                count += 1

        return rs.AddPolyline(thing)

    def GetLinesInRegion(self, region, lines):
        list = [] 
        coords = rs.PolylineVertices(region)
        if len(coords) == 2:
            return list

        for line in lines:
            # print "all v all: %d %d" % (len(rs.PolylineVertices(region)), len(rs.PolylineVertices(line)))
            success = True
            for pt in rs.PolylineVertices(line):
                if not self.PointInRegion(pt, region):
                    success = False
                    break
            if success:
                list.append(line)

        return list

    def GetRawPoints(self, line):
        c = []
        # print rs.ObjectType(line)
        for pt in rs.PolylineVertices(line):
            c.append((pt[0],pt[1]))
        return c

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
        # order = self.OptimizeLinearPartsFromOrder(order, start)

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
                print pos
            else: 
                d1 = rs.Distance(pos, rs.CurveStartPoint(line))
                d2 = rs.Distance(pos, rs.CurveEndPoint(line))
                if d2 < d1:
                    rs.ReverseCurve(line)
                pos = rs.CurveEndPoint(line)
                print pos

        rs.DeleteObject(pos)
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
            tour = tsp.Anneal(coords, locked)

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


    def _boolean(self, value):
        if value == "True":
            return True
        if value == "False":
            return False


# see: 
# http://www.codeproject.com/Articles/26758/Simulated-Annealing-Solving-the-Travelling-Salesma
# http://www.psychicorigami.com/2007/06/28/tackling-the-travelling-salesman-problem-simmulated-annealing/

class TSP:

    def __init__(self,parent):
        self.Reset()
        self.parent = parent
        self.start_temp = parent.start_temp
        self.alpha = parent.alpha
        self.iterations = parent.iterations

    # Not tested. It's meant to be called when the user
    #   lots of new parameters.
    def Reset(self):
        self.best=None
        self.best_score=None
        self.start_temp = None
        self.locked_points = None
        self.alpha=None
        self.coords = None
        self.current=None
        self.iterations=None
        self.matrix = None

    def Check(self):
        if self.coords is None:
            print 'tsp cant run without coords, call tsp.SetCoords'

        if self.start_temp is None:
            print 'tsp cant run without self.start_temp = int'

        if self.alpha is None:
            print 'tsp cant run without self.alpha = int'

        if self.iterations is None:
            print 'tsp cant run without self.iterations = int'

        if self.locked_points is None:
            print 'tsp cant run with self.locked_points = None'

    def SetCoords(self, coords):
        self.coords = coords
        self.current=range(len(coords)) # the current tour of points
        self.matrix = self.CartesianMatrix(coords)
    
    # Total up the total length of the tour based on the distance matrix
    def ObjectiveFunction(self,solution):
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

    def KirkpatrickCooling(self):
        T=self.start_temp
        while True:
            yield T
            T=self.alpha*T

    def PChoice(self, prev_score,next_score,temperature):
        if next_score > prev_score:
            return 1.0
        else:
            return math.exp( -abs(next_score-prev_score)/temperature )

    def RandSeq(self,size,positions):
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
    
    # generates all i,j pairs for i,j from 0-size
    def AllPairs(self,size,positions):
        for i in self.RandSeq(size, positions):
            for j in self.RandSeq(size,positions):
                yield (i,j)
    
    # Return all variations where the 
    #  section between two cities are swappedd
    def ReversedSections(self):
        positions = self.FindLockedPoints()
        for i,j in self.AllPairs(len(self.current), positions):
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

    def FindLockedPoints(self):
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
    def CartesianMatrix(self, coords):
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
    def ReadCoords(self,coord_file):
        coords=[]
        for line in coord_file:
            x,y=line.strip().split(',')
            coords.append((float(x),float(y)))
        return coords

    def WriteTourToImg(self,coords,tour,locked_points,title,img_file):
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
    
    def ReportStats(self):
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
    def Anneal(self, coords, locked_points):
        self.SetCoords(coords)
        self.locked_points = locked_points

        current_score=self.ObjectiveFunction(self.current)
        num_evaluations=1
    
        self.Check()

        cooling_schedule=self.KirkpatrickCooling()
        
        for temperature in cooling_schedule:
            done = False
            # examine moves around our current position
            for next in self.ReversedSections():
                if num_evaluations >= self.iterations:
                    done=True
                    break
                
                next_score=self.ObjectiveFunction(next)
                num_evaluations+=1
                
                # print (current_score,next_score,temperature)
                # probablistically accept this solution
                # always accepting better solutions
                p=self.PChoice(current_score,next_score,temperature)
                if random.random() < p:
                    self.current=next
                    current_score=next_score
                    break
            # see if completely finished
            if done: break
        
        # self.ReportStats()

        self.iterations = num_evaluations
        # starts with a list of coordinates
        #  returns a path - the list of numbers that point to the original
        #  list of coordinates, giving the order of coordinates that
        #  compose the shortest path between all coordinates
        return self.best


class Gcode:
    def __init__(self, FileName):

        self.ini_file = FileName
        self.gcode_string = ""

        self.dictionary_file = rs.GetSettings(FileName, 'GCODE', 'dictionary')
        self.move_feed_rate = int(rs.GetSettings(FileName, 'GCODE', 'move_feed_rate'))
        self.cut_feed_rate = int(rs.GetSettings(FileName, 'GCODE', 'cut_feed_rate'))
        self.dwell_time = float(rs.GetSettings(FileName, 'GCODE', 'dwell_time'))

        from os.path import join as pjoin
        path = rs.GetSettings(FileName, 'GCODE', 'ncfile_dir')

        self.output_file = pjoin(path, rs.GetSettings(FileName, 'GCODE', 'output_file'))

        self.cut_speed_variable = '#<cutfeedrate>'
        self.move_speed_variable = '#<movefeedrate>'
        self.dwell_time_variable = '#<dwelltime>'

        return True

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
            print 'wrote (%s) in %s' % (p, g.output_file)
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
        self.Append('G1 X0.000 Y0.000 F30 (HOME AGAIN HOME AGAIN)\n')
        self.Append('M2 (LinuxCNC program end)')
        self.AddEOL()


    def Append(self, s):
        self.gcode_string = self.gcode_string + s

    def Prepend(self, s):
        self.gcode_string = s + self.gcode_string

if __name__ == '__main__':
    g = Gcode("polyline_dump.ini")
 
    t2 = time.time()

    if g.TestIfOK():
        tp=Toolpath("polyline_dump.ini")

        t1 = time.time()
        struct = tp.FindToolpath(True)
        # print " toolpath time: %lf" % (time.time() - t1)
        if struct:

            if tp.showpaths:
                tp.ShowPaths(struct)

            p = g.MakePhrase()

            title = '(' + p + ')' + '\n'
            g.Append(title)
            g.AddHeader()

            parts = struct['parts']
            for part in parts:
                cuts = struct[part]['cuts']
                for cut in cuts:
                    g.WritePolyline(cut, "LAYER: CUTS")

                t1 = time.time()
                g.WritePolyline(part, "LAYER: PARTS")
                l = len(rs.PolylineVertices(part))
                # print " part: %d :: %lf" % (l, time.time() - t1)

            g.AddFooter()

            g.WriteGcode()

            tp.FlushObjects()

        # print "close: %lf" % (time.time() - t1)
        t1 = time.time()

    # print "total: %lf" % (time.time() - t2)
