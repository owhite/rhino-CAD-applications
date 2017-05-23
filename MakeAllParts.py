# Turn all selected items into parts. 

import rhinoscriptsyntax as rs
import Rhino.RhinoApp as app
from System.Drawing import Color
import sys
import time

def FindLargestCurve(objects):
    max_area = 0.0
    max_obj = ""
    for obj in objects:
        if rs.IsCurveClosed(obj):
            props = rs.CurveArea(obj)
            if max_area < props[0]:
                max_area = props[0]
                max_obj = obj
    return(max_obj)
    
def GetLinesInRegion(region, lines):
    list = [] 
    delete_list = []
    if rs.IsCurve(region):
        region = rs.ConvertCurveToPolyline(region)
        delete_list.append(region)

    for line in lines:
        success = True
        if rs.IsCurve(line):
            tmp = rs.ConvertCurveToPolyline(line)
            delete_list.append(tmp)

        for pt in rs.PolylineVertices(tmp):
            if not PointInRegion(pt, region):
                success = False
                break

        if success:
            list.append(line)

    for kill_me in delete_list:
        rs.DeleteObject(kill_me)

    return list

def EverythingIsFlat(): 
    objects = rs.SelectedObjects()  
    for object_id in objects:
        if rs.IsCurve(object_id):
            if not rs.IsCurveInPlane(object_id):
                return False
    return True

def PointInRegion(pt, line):
    poly = rs.PolylineVertices(line)
    n = len(poly)
    inside = False
        
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

objects = rs.SelectedObjects()  

if not objects: 
    objects = rs.GetObjects("Select objects")

if not EverythingIsFlat():
    sys.exit("found a curve that is not in the active construction plane")

success = False

if objects:

    if not rs.IsLayer("PARTS"):
        rs.AddLayer("PARTS", Color.Blue)

    others = []
    for obj in objects:
        rs.ObjectLayer(obj, "PARTS")

    rs.FlashObject(objects, style=True)
    rs.UnselectObjects(objects)
    app.Wait()
    time.sleep(1)
    rs.SelectObjects(objects)

    success = True

if success:
    print "conversion successful"
else:
    print "no part created"

