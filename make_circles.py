import rhinoscriptsyntax as rs

countX = 20
countY = 10
bump = .2
r = .02

x = 0
y = 0

for i in range(countY):
    for j in range(countX):
        c = rs.AddCircle((x,y,0), r)
        r += .0005
        x += bump
    x = 0
    y += bump
