#!/usr/bin/env python

from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geos import lgeos

print "hoping for a minimum of: (1, 6, 2)\nand: 3.2.2-CAPI-1.6.2\n\nversions:\n"

print lgeos.geos_capi_version
print lgeos._lgeos.GEOSversion()

print '\ntesting interpolate() and project()'

ip = LineString([(0, 0), (0, 1), (1, 1)]).interpolate(1.5)
x = LineString([(0, 0), (0, 1), (1, 1)]).project(ip)

if x == 1.5:
    print "looks like it's working"
else:
    print 'fail'
