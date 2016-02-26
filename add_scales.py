# I worked on this program long enough to realize I dont
#  like the strategy of adding scales along the edge of a
#  a part. It just makes dorky looking scales. A
#  different approach will have to be taken to
#  make something that looks real. 

import rhinoscriptsyntax as rs
import ConfigParser
import StringIO
import sys

class Shells:
    def __init__(self):
        self.delete_objs = []
        self.scale_layer = self.GetConfigOption('SHELLS', 'scale_layer')
        self.edge_layer = self.GetConfigOption('SHELLS', 'edge_layer')
        self.scaling = (.58, .70, .80, .98, .98, .98, .96, .90, .50)

    def FlowPartAlongLine(self, bump):
        (part, line) = self.GetFishNLine()

        part_dis = rs.Distance(rs.CurveStartPoint(part),
                               rs.CurveEndPoint(part))
        s = sum(self.scaling)
        interval = 0
        travel = 0
        line_len = rs.CurveLength(line)
        cur_pos = rs.CurveStartPoint(line)
        if bump:
            # this is to offset the part at the bottom.
            # This basically cuts the part in half, moves it
            # that distance up the line
            # s += self.scaling[0] / 2
            interval = ((self.scaling[0] / s) * line_len / 2)
            cur_pos = rs.CurveArcLengthPoint(line, interval)
            travel = interval

        count = 0
        parts = []
        for i in self.scaling:
            interval = (i / s) * line_len
            pt = rs.CurveArcLengthPoint(line, interval + travel)
            if pt is not None:
                travel += interval
                dis = rs.Distance(cur_pos, pt)
                f = dis / part_dis
                new = rs.ScaleObject(part, rs.CurveStartPoint(part),
                                     (f,f,f), True)
                rs.MoveObject(new, cur_pos - rs.CurveStartPoint(new))
                angle = rs.Angle2((cur_pos, rs.CurveEndPoint(new)),
                                  (cur_pos, pt))
                rs.RotateObject(new, cur_pos, angle[0])
                parts.append(new)
                if bump and count == 0:
                    p = rs.CopyObject(new, rs.CurveStartPoint(new)
                                      - rs.CurveEndPoint(new))
                    parts.append(p)

            else: # we're here because user selected bump
                  # part needs to be "grown" off end of line
                gl = rs.CopyObject(line, (0,0,0)) 
                interval = (i / s) * line_len
                rs.ExtendCurveLength(gl, 0, 1, interval)
                pt = rs.CurveArcLengthPoint(gl, interval + travel)
                dis = rs.Distance(cur_pos, pt)
                f = dis / part_dis
                new = rs.ScaleObject(part, rs.CurveStartPoint(part),
                                     (f,f,f), True)
                rs.MoveObject(new, cur_pos - rs.CurveStartPoint(new))
                angle = rs.Angle2((cur_pos, rs.CurveEndPoint(new)),
                                  (cur_pos, pt))
                rs.RotateObject(new, cur_pos, angle[0])
                parts.append(new)
                rs.DeleteObject(gl)
                
            count += 1
            cur_pos = pt
        return(parts)

    def GetFishNLine(self):
        obj = rs.ObjectsByLayer(self.scale_layer)
        if len(obj) == 1:
            s = obj[0]
        elif len(obj) > 1:
            print "got too many lines on scale layer"
        else:
            print "problem finding scale"
        obj = rs.ObjectsByLayer(self.edge_layer)
        if len(obj) == 1:
            l = obj[0]
        else:
            print "problem finding edge"
        return(s,l)

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

if __name__ == '__main__':
    shells = Shells()
    shells.FlowPartAlongLine(True)
