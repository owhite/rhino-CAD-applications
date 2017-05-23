import rhinoscriptsyntax as rs

def DoSomething():
    "using custom options callable from buttons"
    myoptions = ["Sphere", "Point", "Line"]
    str = rs.GetString("Choose an option", "Sphere", myoptions)
    if str is not None:
        print "STRING: %s" % str
    return None

if __name__=="__main__":
    DoSomething()
