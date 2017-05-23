#!/opt/local/bin/python

from dxfwrite import DXFEngine as dxf
import sys

def dump_coords(name, coords):
    drawing.add(dxf.polyline(coords, layer = name))

def chow_file(f, drawing):
    coords = []
    line_type = ''

    for line in open(f,'r'):
        line = line.replace('\n', '')
        if line.find("(LAYER:") > -1:
            line = line.replace('LAYER: ', '')
            line = line.replace('(', '')
            line = line.replace(')', '')

            old_line = line
            line_type = line.replace('\n', '')

        if line.find('G01') > -1:
            (command, x, y, null) = line.split(' ')
            x = x.replace('X', '')
            y = y.replace('Y', '')
            coords.append((float(x),float(y)))
        if line.find('G00') > -1:
            if len(coords) > 0:
                dump_coords(old_line, coords)
            (command, x, y, null) = line.split(' ')
            x = x.replace('X', '')
            y = y.replace('Y', '')
            coords = [(float(x),float(y))]

    dump_coords(line_type, coords)

if __name__ == "__main__":

    if len(sys.argv) != 3:
        sys.exit("provide an input and output file")

    drawing = dxf.drawing(sys.argv[2])
    drawing.add_layer("CUTS",  color=1)
    drawing.add_layer("PARTS", color=5)
    chow_file(sys.argv[1], drawing)
    drawing.save()
