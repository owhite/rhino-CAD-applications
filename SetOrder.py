import rhinoscriptsyntax as rs

# user clicks on objects in the parts layer,
#  order of clicks assigns order of cuts.

objs = rs.ObjectsByType(8192)
if (objs):
    for obj in objs:
        item = rs.TextDotText( obj )
        if item.isdigit(): rs.DeleteObject( obj )

objs = rs.ObjectsByLayer("PARTS")
if (objs):
    for obj in objs:
        type = rs.IsUserText(obj)
        # remove old ones
        if type==1: rs.GetUserText( obj, "toolpath_order")

objs = rs.GetObjects("Select objects in order")

if (objs):
    count = 1;
    for obj in objs:
        if (rs.ObjectLayer(obj) == "PARTS"):
            rs.SetUserText( obj, "toolpath_order", str(count) )
            print "SET: %d" % count
            rs.AddTextDot(str(count),(rs.CurveStartPoint(obj)))
            count += 1

    # rs.SelectObjects(objs)
