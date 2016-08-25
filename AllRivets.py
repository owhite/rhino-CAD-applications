import rhinoscriptsyntax as rs

# Replaces all the selected objects with an content of a file chosen by the user

import glob
import os
import re

objectPath = "/Users/owhite/Documents/CAD/rivets"

old = rs.SelectedObjects()
rs.UnselectAllObjects()

if (len(old)> 0):
    if os.path.isdir(objectPath):
        files = []
        for file in glob.glob(objectPath + "/*.3dm"):
            files.append(re.sub(r'.*\/','',file))

        if files:
            print "replacing objects"
            choice = rs.ListBox(files, "objectPath")
            if choice:
                cmd = "_Import " + objectPath + "/" + choice
                rs.Command(cmd)
                new = rs.LastCreatedObjects()
                for id in old:
                    props = rs.CurveAreaCentroid(id)
                    tmp = rs.CopyObject(new, props[0]) 
                    rs.SelectObject(tmp)
                    rs.DeleteObjects(id)
                rs.DeleteObjects(new)
else:
    print "no objects selected"

