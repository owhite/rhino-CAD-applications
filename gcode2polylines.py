#!/usr/bin/env python

import rhinoscriptsyntax as rs

class ProcessNCFile:
    def __init__(self, FileName):
        self.FileName = FileName
        return True

    def DumpCoords(self):
        # we're going to do two things
        # first check if the required layers exist
        for (name, coords) in self.coords_list:
            if (rs.IsLayer(name) == False):
                print "creating layer ", name
                rs.AddLayer(name)

        # now make all the polylines
        for (name, coords) in self.coords_list:
            points = []
            for (x,y) in coords:
                points.append((x, y, 0))
            p = rs.AddPolyline(points)
            rs.ObjectLayer(p, name)

    def ChowFile(self):
        coords = []
        self.coords_list = []
        line_type = ''

        for line in open(self.FileName,'r'):
            line = line.replace('\n', '')
            if line.find("(LAYER:") > -1:
                old_line = line_type

                line = line.replace('LAYER: ', '')
                line = line.replace('(', '')
                line = line.replace(')', '')
                line_type = line.replace('\n', '')

            if line.find('G01') > -1:
                (command, x, y, null) = line.split(' ')
                x = x.replace('X', '')
                y = y.replace('Y', '')
                coords.append((float(x),float(y)))
            if line.find('G00') > -1:
                if len(coords) > 0:
                    self.coords_list.append((old_line, coords))

                (command, x, y, null) = line.split(' ')
                x = x.replace('X', '')
                y = y.replace('Y', '')
                coords = [(float(x),float(y))]

        self.coords_list.append((line_type, coords))

if __name__ == '__main__':

    filename = rs.OpenFileName()

    if not filename:
        print "no file selected"
    else:
        nc = ProcessNCFile(filename)
        nc.ChowFile()
        nc.DumpCoords()

