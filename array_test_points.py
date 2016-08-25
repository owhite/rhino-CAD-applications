#!/opt/local/bin/python

from optparse import OptionParser
import textwrap
import sys

class Array:
    def __init__(self):
        parser = OptionParser(usage="usage: %prog [options]")

        parser.add_option("-m", 
                          action="store",
                          type="int",
                          dest="move_rate",
                          default=20,
                          help="move rate")

        parser.add_option("-c", 
                          action="store",
                          type="int",
                          dest="cut_rate",
                          default=20,
                          help="cut rate")

        parser.add_option("-d", 
                          action="store",
                          type="int",
                          dest="dwell",
                          default=.02,
                          help="length of time laser pulses")

        parser.add_option("-x", 
                          action="store", 
                          type="float",
                          dest="x_dist",
                          default=2.0,
                          help="width of array",)

        parser.add_option("-y", 
                          action="store", 
                          type="float",
                          dest="y_dist",
                          default=1.0,
                          help="height of array",)

        parser.add_option("-z", 
                          action="store", 
                          type="int",
                          dest="z_dist",
                          default=0,
                          help="change in z",)

        (options, args) = parser.parse_args()

        self.x_iter = 20
        self.y_iter = 10
        for opt, value in options.__dict__.items():
            setattr(self, opt, value)

    def generateArray(self):
        self.printHeader()
        self.startMachine()
        x_inc = float(self.x_dist / self.x_iter)
        y_inc = float(self.y_dist / self.y_iter)
        for y in range(self.x_iter):
            for x in range(self.x_iter):
                self.moveNoCut(x_inc * x, y_inc * y)
                self.pulseLaser()
        self.stopMachine()
                
    def printHeader(self):
        print textwrap.dedent("""\
        (A script generated this file.)
        (Width: %d :: Height: %d inches)

        #<movefeedrate>=%d
        #<cutfeedrate>=%d
        G17 G20 G40 G49 G80 G90
        G92 X0 Y0 (Set current position to zero)
        G64 P0.005 (Continuous mode with path tolerance)
        """) % (self.x_dist, self.y_dist, self.cut_rate, self.move_rate)

    def startMachine(self):
        print textwrap.dedent("""\
        M64 P00 (VENTILATION ON)
        M64 P01 (GAS LINE ON)
        M65 P03 (LASER OFF)
        """)

    def stopMachine(self):
        print textwrap.dedent("""\
        M65 P01 (GAS LINE OFF)
        M65 P03 (LASER OFF)
        M65 P00 (VENTILATION OFF)
        G1 X0.000 Y0.000 F#<movefeedrate> (HOME)
        M2 (LinuxCNC program end)
        """)


    def moveNoCut(self, x, y):
        print textwrap.dedent("""\
        G00 X%0.3lf Y%0.3lf F#<movefeedrate>""") % (x, y)

    def pulseLaser(self):
        print textwrap.dedent("""\
        M64 P03 (LASER ON)
        G4 P%0.2lf
        M65 P03 (LASER OFF)
        """) % (self.dwell)

if __name__ == "__main__":
    a = Array()
    a.generateArray()
