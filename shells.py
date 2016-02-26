# Program to loft shells over lines that form the body of an
#  object, like a fish. If you create lines in the layer
#  that the program can follow, it will:
#    1) bisect across the lines
#    2) find the intersections of the bisecting surface with the lines
#    3) create a polyline along those insection points,
#    4) proceed to the next bisection
#    5) repeat steps 2 and 3
#    6) then loft from the two newly made polylines
#         note: the lofted part is a "shell"
#    7) unfold the shell
#
# This executable should be in:
#  ~/Library/Application Support/McNeel/Rhinoceros/Scripts/laser_code
# And and example rhino file is:
#  ~/Documents/CAD/script_examples/shells_demo.3dm
#
# The notes of the rhino file sets various parameters
#
# This works fairly well but I never got the scales on the sides of shells to
#  work yet to use this make a life-like fish. My ship will come in. 

import rhinoscriptsyntax as rs
from System.Drawing import Color
import ConfigParser
import StringIO
import sys

class Shells:
    def DecorateEdges(self): 
        count = 0
        bump = 1
        p = rs.ObjectsByLayer(self.right_edge_part)
        right_edge_part = p[0]
        for (e1, e2) in self.flat_edges:
            d = self.edge2_isx_dis[count]
            l2 = rs.AddPolyline(e2)
            self.FlowPartAlongLine(right_edge_part, l2, d, bump)
            rs.DeleteObjects(l2)
            bump = not bump
            count += 1
            break

    def _PlaceRotatePart(self, part, start, end):
        part_dis = rs.Distance(rs.CurveStartPoint(part), rs.CurveEndPoint(part))
        f = rs.Distance(start,end) / part_dis
        new = rs.ScaleObject(part, rs.CurveStartPoint(part),
                             (f,f,1), True)
        rs.MoveObject(new, start - rs.CurveStartPoint(new))
        angle = rs.Angle2((start, rs.CurveEndPoint(new)),
                          (start, end))
        rs.RotateObject(new, start, angle[0])
        return(new)

    # part is the thing that will be decorated on to the line
    # line is what the part gets decorated on to. 
    # distances are how far the part will be scaled along the line.
    # bump controls if we offset the part at the bottom.
    #  This basically cuts the part in half, moves it
    #  that distance up the line
    def FlowPartAlongLine(self, part, line, distances, bump):
        line_dis = rs.Distance(rs.CurveStartPoint(line), rs.CurveEndPoint(line))
        travel = 0
        parts = []
        if bump:
            # got to do some stuff
            tmp = rs.CopyObject(line, (0,0,0)) 
            rs.ExtendCurveLength(tmp, 0, 0, distances[0] / 2)
            start_pt = rs.CurveStartPoint(tmp)
            rs.DeleteObjects(tmp)
            end_pt = rs.CurveArcLengthPoint(line, distances[0] / 2)
            p = self._PlaceRotatePart(part, start_pt, end_pt)
            parts.append(p)

        for i,d1 in enumerate(distances[0:-1]):
            d2 = distances[i+1]
            if bump:
                start_pt = rs.CurveArcLengthPoint(line, travel + (d1 / 2))
                end_pt = rs.CurveArcLengthPoint(line, travel + d1 + (d2 / 2))
            else:
                start_pt = rs.CurveArcLengthPoint(line, travel)
                end_pt = rs.CurveArcLengthPoint(line, travel + d1)

            if end_pt is None:
                end_pt = rs.CurveEndPoint(line)
            p = self._PlaceRotatePart(part, start_pt, end_pt)
            parts.append(p)
            start_pt = end_pt
            travel += d1

        # last one
        if bump:
            tmp = rs.CopyObject(line, (0,0,0)) 
            rs.ExtendCurveLength(tmp, 0, 1, distances[-1] / 2)
            end_pt = rs.CurveEndPoint(tmp)
            rs.DeleteObjects(tmp)
        else:
            end_pt = rs.CurveEndPoint(line)
        p = self._PlaceRotatePart(part, start_pt, end_pt)
        parts.append(p)
        return(parts)

    def DecorateEdgesByGroup(self): 
        return()
        try:
            group_l = rs.ObjectsByGroup(self.right_edge_group)
        except AttributeError:
            group_l = []
        try:
            group_r = rs.ObjectsByGroup(self.right_edge_group)
        except AttributeError:
            group_r = []
        for (e1, e2) in self.flat_edges:
            if len(group_l) != 0:
                self.TransformEdgeGroup(e1, group_l)
                self.AlignEdgeGroup(e1, group_l)
            if len(group_r) != 0:
                print "here2"

    def GetPointAlongLineByIntersection(self, line, plane):
        isx = rs.CurveSurfaceIntersection(line, plane)
        if isx is None:
            # that's okay, return nothing
            pass
        # but if we get an intersection, there should only be one. 
        elif isx[0][0]==1:
            if (rs.Distance(isx[0][1], rs.CurveStartPoint(line)) < self.min_decoration_size) or (rs.Distance(isx[0][1], rs.CurveEndPoint(line)) < self.min_decoration_size):
                return(None) # dont want short little things
            return(isx[0][1])
        # did you know if you do not specify something to return
        # python functions return None? 
        elif len(isx) != 1:
            print "not sure why we're getting " + len(isx) + " intersections (GetPointAlongLineByIntersection)"

    def FindLocationsOnEdges(self):
        self.edge1_isx_dis = []
        self.edge2_isx_dis = []
        planes = []
        for eisx in self.edge_intersections:
            p = rs.ExtrudeCurveStraight( eisx, (0,0,0), (0, 0, self.maxZ ) )
            planes.append(p)
        for edges in self.surface_edges:
            (e1, e2) = edges
            d1 = []
            d2 = []
            t1 = 0
            t2 = 0
            for p in planes:
                pt = self.GetPointAlongLineByIntersection(e1, p)
                if pt is not None:
                    d = self.TravelDistance(e1, pt) - t1
                    d1.append(d)
                    t1 += d
                pt = self.GetPointAlongLineByIntersection(e2, p)
                if pt is not None:
                    d = self.TravelDistance(e2, pt) - t2
                    d2.append(d)
                    t2 += d
            # add the last distance. If, its longer than minimum
            #  decoration distance. Else, make the last distance go
            #  all the way to end of line
            if (rs.CurveLength(e1) - t1 > self.min_decoration_size):
                d1.append(rs.CurveLength(e1) - t1)
            else:
                d1[-1] = rs.CurveLength(e1) - t1
            if (rs.CurveLength(e2) - t2 > self.min_decoration_size):
                d2.append(rs.CurveLength(e2) - t2)
            else:
                d2[-1] = rs.CurveLength(e2) - t2
            self.edge1_isx_dis.append(d1)
            self.edge2_isx_dis.append(d2)
        rs.DeleteObjects(planes)


    def DisplayUnrolledEdges(self):
        self.pause("unrolling")
        for edges in self.flat_edges:
            (e1, e2) = edges
            rs.AddPolyline(e1)
            rs.AddPolyline(e2)
            break

    def UnrollBySurfaceEdges(self):
        self.pause("unrolling")
        self.flat_edges = []
        for edges in self.surface_edges:
            segment = ((0,0,0), (1,0,0))
            (e1, e2) = edges
            p1 = rs.PolylineVertices(e1)
            p2 = rs.PolylineVertices(e2)
            plates = []
            kill_list = []
            for i in range(len(p1) - 1):
                p = Plate((p1[i], p2[i], p2[i+1], p1[i+1]))
                # self.delete_objs.append(p.id)
                kill_list.append(p.id)
                self.delete_objs.append(p.id)
                p.OrientPlateToSegment(segment)
                segment = p.Top()
                plates.append(p)
            self.flat_edges.append(self.GetPlateEdges(plates))
            rs.DeleteObjects(kill_list)


    def GetPlateEdges(self, plates):
        e1 = []
        e2 = []
        for plt in plates:
            p = plt.Points()
            e1.append(p[0])
            e2.append(p[1])
        e1.append(p[3])
        e2.append(p[2])
        return((e1, e2))

    def GetLineMidPoint(self, line, s):
        p1 = rs.CurveEndPoint(line)
        p2 = rs.CurveStartPoint(line)
        # Rhino point math is fun!
        return(rs.PointAdd(rs.PointDivide(rs.PointSubtract(p1, p2),(1/s)), p2))

    def GetPointMidPoint(self, p1, p2, s):
        return(rs.PointAdd(rs.PointDivide(rs.PointSubtract(p1, p2),(1/s)), p2))

    def LoftAcrossLines(self):
        self.pause("lofting across intersecting points")
        scale_var = self.internal_scale
        r = self.internal_portion
        self.surfaces = []
        self.surface_edges = []
        for i in range(len(self.intersectlines) - 2):
            l1 = self.intersectlines[i]
            l2 = self.intersectlines[i+1]
            l3 = self.intersectlines[i+2]

            p1 = self.GetPointMidPoint(rs.CurveStartPoint(l1),
                                       rs.CurveStartPoint(l2), r)
            p2 = self.GetPointMidPoint(rs.CurveEndPoint(l1),
                                       rs.CurveEndPoint(l2), r)

            new = rs.OrientObject(l3,
                                  (rs.CurveStartPoint(l3),
                                   rs.CurveEndPoint(l3)),
                                  (p1, p2), flags = 3)

            rs.ScaleObject(new, self.GetLineMidPoint(new, .5),
                           (scale_var, scale_var, scale_var),
                           False)

            sfc = rs.AddLoftSrf((new, l3))
            self.surfaces.append(sfc)
            self.surface_edges.append((new, l3))
            self.delete_objs.append((l1, l2, l3, new))

        self.delete_objs.append(self.surfaces)

    def CreateLineSections(self):
        self.pause("creating bisections")
        if len(self.sections) > 0:
            self.CreateSections()
        else:
            self.CreateSerialSections()

        self.CreateLinesFromIntersections()

    def CreateLinesFromIntersections(self):
        self.intersectlines = []
        line_num = len(self.lines)
        for plane in self.sections:
            points = []
            count = 0
            for line in self.lines:
                isx = rs.CurveSurfaceIntersection(line, plane)
                # so this should only get one intersection
                if len(isx) != 1:
                    print "not sure why we're getting " + len(isx) + " intersections (CreateLinesFromIntersections)"
                if isx[0][0]==1:
                    points.append(isx[0][1])
                    count += 1
            if count != line_num:
                print "should get %d intersections but got: %d." % (line_num, count)

            line = rs.AddPolyline(points)
            self.intersectlines.append(line)
            rs.DeleteObject(plane)
            # self._tagsections(self.intersectlines)


    # send this a line and a point that is along the line
    # returns the distance you have to travel to get to that point. 
    def TravelDistance(self, line, pt):
        pts = rs.PolylineVertices(line)
        count = len(pts) - 1
        t = 0
        hit = False
        c = rs.AddCurve((pt,pt)) # stupid that a curve has to be made
                                 # but points dont work. 
        for i in range(count):
            l = rs.AddCurve((pts[i], pts[i+1]))
            r = rs.CurveClosestObject (l, c)
            rs.DeleteObject(l)
            if rs.Distance(r[2], pt) < .001:
                t += rs.Distance(pts[i], pt)
                hit = True
                break
            else:
                t += rs.Distance(pts[i], pts[i+1])
        rs.DeleteObject(c)
        if not hit:
            t = -1
        return t

    def MyCurveCurveIntersect(self,c1, c2):
        id = rs.CopyObject(c1, (0,0,0))
        rs.ExtendCurveLength(id, 0, 2, rs.CurveLength(id) * .1)
        isx = rs.CurveCurveIntersection(id, c2)
        if isx is None:
            rs.DeleteObject(id)
            rs.SelectObjects((c1, c2))
            sys.exit("These highlighted objects must intersect.")
        rs.DeleteObject(id)
        return(isx[0][1])

    def OrderSections(self, line):
        thing = {}
        # now figure out where they are on the line
        i = 0
        for s in self.sections:
            pt = self.MyCurveCurveIntersect(s,line)
            dis = self.TravelDistance(line, pt)
            if dis == -1:
                rs.SelectObjects((s, line))
                sys.exit("something went wrong getting travel distance on these objects")
            thing[s] = dis

        # get an order, reassign to existing sections
        order = []
        for x in sorted(thing, key=thing.get):
            order.append(x)
        self.sections = order

    def _tagsections(self, lines):
        count = 1
        for s in lines:
            rs.AddTextDot(str(count), rs.CurveStartPoint(s))
            count+=1

    # looks for lines in the drawing that can serve as planes to
    #  bisect up the body, and trudges from left to right to
    #  make bisecting planes
    def CreateSections(self):
        line = self.lines[0] # just pick the bottom one
        # this is sort of a problem in that it really constrains how
        #  the thing getting sectioned up as to be sitting on the page
        #
        # it's also basing everything on the "start" of this line
        self.OrderSections(line)
        q = []
        for s in self.sections:
            p1 = rs.CurveStartPoint(s)
            path = rs.AddLine(p1, (p1[0],p1[1],self.maxZ))
            q.append(rs.ExtrudeCurve(s, path))
            rs.DeleteObject(path)
        self.sections = q

    # divides the body up in equal amounts and trudges left to right
    #  to make bisecting planes 
    # to do - make order of sections based on user-defined start
    #  of the lines, rather than just tropping left to right
    def CreateSerialSections(self):
        inc = (self.endPt[0] - self.startPt[0]) / (self.shell_num + 1)
        pos = self.startPt[0] + inc
        q = []
        for i in range(self.shell_num):
            l = []
            l.append(rs.AddPoint((pos,self.maxY, self.minZ)))
            l.append(rs.AddPoint((pos,self.minY, self.minZ)))
            l.append(rs.AddPoint((pos,self.minY, self.maxZ)))
            l.append(rs.AddPoint((pos,self.maxY, self.maxZ)))
            l.append(rs.AddPoint((pos,self.maxY, self.minZ)))
            pl = rs.AddPolyline(l)
            q.append(rs.AddPlanarSrf(pl))
            rs.DeleteObjects(pl)
            rs.DeleteObjects(l)
            pos += inc
        self.sections = q

    def DefineBoundingArea(self):
        thing1 = {}
        thing2 = {}
        for line in self.lines:
            pt1 = self.MinimumPointXY(line)
            pt2 = self.MaximumPointXY(line)
            thing1[line] = pt1[0]
            thing2[line] = pt2[0]

        l = []
        l = sorted(thing1, key=thing1.get, reverse=True)
        self.startPt = self.MinimumPointXY(l[0])

        l = []
        l = sorted(thing2, key=thing2.get)
        self.endPt = self.MaximumPointXY(l[0])

        self.minX = 99999.0
        self.maxX = -99999.0

        self.minY = 99999.0
        self.maxY = -99999.0

        self.minZ = 99999.0
        self.maxZ = -99999.0

        for line in self.lines:
            bb = rs.BoundingBox(line)
            if bb:
                for pt in bb:
                    if float(pt[0]) < self.minX:
                        self.minX = float(pt[0])
                    if float(pt[0]) > self.maxX:
                        self.maxX = float(pt[0])

                    if float(pt[1]) < self.minY:
                        self.minY = float(pt[1])
                    if float(pt[1]) > self.maxY:
                        self.maxY = float(pt[1])

                    if float(pt[2]) < self.minZ:
                        self.minZ = float(pt[2])
                    if float(pt[2]) > self.maxZ:
                        self.maxZ = float(pt[2])


    # we should have some lines from the drawing
    #  reorder them based on height in the y-axis
    #  orders them from bottom to top
    # this is based on the start of the line
    def OrderLines(self, lines):
        thing = {}
        for line in lines:
            pt = rs.CurveStartPoint(line)
            thing[line] = pt[1]

        order = []
        for x in sorted(thing, key=thing.get):
            order.append(x)

        return(order)

    def MinimumPointXY(self, line):
        p1 = rs.CurveEndPoint(line)
        p2 = rs.CurveStartPoint(line)

        if p1[0] < p2[0]:
            return p1 
        if p1[0] > p2[0]:
            return p2


    def MaximumPointXY(self, line):
        p1 = rs.CurveEndPoint(line)
        p2 = rs.CurveStartPoint(line)

        if p1[0] < p2[0]:
            return p2 
        if p1[0] > p2[0]:
            return p1

    def CurvesToPolylines(self, curves):
        l = []
        for id in curves:
            if rs.IsCurve(id) and not (rs.IsPolyline(id)):
                id = rs.ConvertCurveToPolyline(id, angle_tolerance=1, 
                                               tolerance=0.01, delete_input=False)
            l.append(id)
        return(l)
    
    def GetCurvesFromLayer(self, layer):
        l = []
        if rs.IsLayer(layer):
            for obj in rs.ObjectsByLayer(layer):
                if rs.IsCurve(obj):
                    l.append(obj)

        return(l)

    def GetConfigOption(self, section, item):
        notes = rs.Notes()
        if notes: 
            buf = StringIO.StringIO(notes)
            cp = ConfigParser.ConfigParser()
            cp.readfp(buf)
        if cp.has_option(section, item):
            thing = cp.get(section, item)
        else:
            rs.Command("!_Notes")
            print "no notes"
            sys.exit("Specify " + item + " = FOO under " + section + " in notes")

        return thing


    def CurveSurfaceIntersect(self, curve, surface):
        if curve is None: return
        if surface is None: return
        intersection_list = rs.CurveSurfaceIntersection(curve, surface)

        if intersection_list is None:
            print "Curve and surface do not intersect."
            return

        if len(intersection_list) != 1:
            print "Curve and surface intersect more than once."
    
        for intersection in intersection_list:
            if intersection[0]==1:
                return intersection[1]

        return False

    def CleanUp(self):
        for objs in self.delete_objs:
            rs.DeleteObjects(objs)


    def pause(self, string):
        if self.pause_between_steps == "True":
            rc = rs.GetString(string)
            if not rc is None:
                return
        else:
            return

    def __init__(self):
        # hope it's okay to do this
        rs.Command("_SetActiveViewport Top")

        self.delete_objs = []
        self.shell_num = int(self.GetConfigOption('SHELLS', 'shell_num'))
        self.internal_scale = float(self.GetConfigOption('SHELLS', 'internal_scale'))
        self.internal_portion = float(self.GetConfigOption('SHELLS', 'internal_portion'))
        self.pause_between_steps = self.GetConfigOption('SHELLS', 'pause_between_steps')
        self.edge_decorate_line = self.GetConfigOption('SHELLS', 'edge_decorate_line')
        self.right_edge_part = self.GetConfigOption('SHELLS', 'right_edge_part')

        self.shell_num = self.shell_num
        self.min_decoration_size = .1

        l = self.GetConfigOption('SHELLS', 'line_layer')
        if len(l) > 0:
            self.curves = self.GetCurvesFromLayer(l)
            self.lines = self.CurvesToPolylines(self.curves)
            self.lines = self.OrderLines(self.lines)
            self.delete_objs.append(self.lines)
        else:
            sys.exit("Didnt find curves in: " + l)

        l = self.GetConfigOption('SHELLS', 'edge_decorate_line')
        if len(l) > 0:
            self.curves = self.GetCurvesFromLayer(l)
            self.edge_intersections = self.CurvesToPolylines(self.curves)
            self.edge_intersections = self.OrderLines(self.edge_intersections)
            self.delete_objs.append(self.edge_intersections)
        else:
            sys.exit("Didnt find the edge intersection lines with: " + l)
        self.edge_decorate_line = l

        s = self.GetConfigOption('SHELLS', 'sections_layer')
        self.sections = self.GetCurvesFromLayer(s)

        self.DefineBoundingArea()

class Plate:
    def __init__(self, pts):
        self.id = rs.AddPolyline((pts[0], pts[1], pts[2], pts[3], pts[0]))

    def Points(self):
        pts = rs.PolylineVertices(self.id)
        return((pts[0], pts[1], pts[2], pts[3]))

    def Bottom (self):
        # each segment gets a name
        pts = self.Points()
        return((pts[0],pts[1]))
        
    def Right(self):
        pts = self.Points()
        return((pts[1], pts[2]))

    def Top(self):
        pts = self.Points()
        return((pts[3], pts[2])) # reversed

    def Left(self):
        pts = self.Points()
        return((pts[3], pts[0]))

    def OrientPlateToSegment(self, segment):
        p = rs.AddPoint(segment[1])
        rs.RotateObject(p, segment[0], 45.0)
        rs.OrientObject(self.id, self.Points(), 
                        (segment[0], segment[1],
                         rs.PointCoordinates(p)))
        rs.DeleteObject(p)        

if __name__ == '__main__':
    shells = Shells()
    shells.CreateLineSections()
    shells.LoftAcrossLines()
    shells.FindLocationsOnEdges()
    shells.UnrollBySurfaceEdges()
    shells.DisplayUnrolledEdges()
    shells.DecorateEdges()
    # shells.CleanUp()
