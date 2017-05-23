import rhinoscriptsyntax as rs

# Asks user for where they'd like a hole from a template,
# then asks user the row from my template
# then asks user the colum
# then places that hole

# these numbers are what was used to make the template
countX = 20
countY = 6
r = .02
inc = .0005

rs.UnselectAllObjects()

pt = rs.GetPoint("Select point")

if pt:
    row = rs.GetInteger("Enter row (start:bottom) ", minimum=0, maximum=countY)
    if row:
        col = rs.GetInteger("Enter column (start:left) ", minimum=0, maximum=countX)
        if col:
            for i in range(countX * (row - 1)):
                r += .0005
            for i in range(col - 1):
                r += .0005

            print "%d %d" % (row, col)
            c = rs.AddCircle(pt, r)
