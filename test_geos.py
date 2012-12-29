#!/usr/bin/env python

from shapely.geos import lgeos

print "hoping for: (1, 6, 2)\nand: 3.2.2-CAPI-1.6.2\n\nversions:\n"

print lgeos.geos_capi_version
print lgeos._lgeos.GEOSversion()
