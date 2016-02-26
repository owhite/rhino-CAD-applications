import rhinoscriptsyntax as rs
from System.Drawing import Color

def FindLargestCurve(objects):
    max_area = 0.0
    max_obj = ""
    for obj in objects:
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

if objects:
    if not rs.IsLayer("PARTS"):
        rs.AddLayer("PARTS", Color.Blue)

    if not rs.IsLayer("CUTS"):
        rs.AddLayer("CUTS", Color.Red)

    # not sure if this is reasonable. If i'm looking for all the objects inside of an object
    #  can I always start with the object with the greatest area? 
    max_obj = FindLargestCurve(objects)
    
    others = []
    for obj in objects:
        if obj != max_obj:
            others.append(obj)

    others = GetLinesInRegion(max_obj, others)

    rs.ObjectLayer(max_obj, "PARTS")

    for obj in others:
        rs.ObjectLayer(obj, "CUTS")

