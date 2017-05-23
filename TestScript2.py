import rhinoscriptsyntax as rs
import clr
import time
import Rhino.RhinoApp as app

objs = rs.ObjectsByLayer("Default")

if objs: rs.FlashObject(objs)

app.Wait()
time.sleep(2)
if objs: rs.FlashObject(objs)

