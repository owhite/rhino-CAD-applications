import rhinoscriptsyntax as rs

# Asks user for where they'd like an object, then asks user to select a file and put content of the file there. 

import glob
import os
import re

objectPath = "/Users/owhite/Documents/CAD/rivets"

rs.UnselectAllObjects()

pt = rs.GetPoint("Select point")

if os.path.isdir(objectPath):
    files = []
    for file in glob.glob(objectPath + "/*.3dm"):
        files.append(re.sub(r'.*\/','',file))

    if files:
        choice = rs.ListBox(files, "objectPath")
        if choice:
            cmd = "_Import " + objectPath + "/" + choice
            rs.Command(cmd)
            objs = rs.LastCreatedObjects()
            rs.MoveObjects(objs, pt)
            rs.UnselectAllObjects()

