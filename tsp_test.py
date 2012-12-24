#!/usr/bin/python

import TSP
import getopt
import sys
import random

def read_coords(coord_file):
  ''' read the coordinates file return the distance matrix.
  coords should be stored as comma separated floats, (no spaces)
  one x,y pair per line. '''
  coords=[]
  for line in coord_file:
      x,y=line.strip().split(',')
      coords.append((float(x),float(y)))
  return coords

def usage():
    print "usage: python %s -o thing.png -n 500000 --cooling 10:1 <city file>" % sys.argv[0]

def main():
    try:
        options, args = getopt.getopt(sys.argv[1:], "ho:n:", ["cooling="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    out_file_name=None
    max_iterations=None
    
    # random.seed(10)

    for option,arg in options:
        if option == '-h':
            usage()
            sys.exit()
        elif option == '-o':
            out_file_name=arg
        elif option == '-n':
            max_iterations=int(arg)
        elif option == '--cooling':
            start_temp,alpha=arg.split(':')
            start_temp,alpha=float(start_temp),float(alpha)
    
    if max_iterations is None:
        usage();
        sys.exit(2)
    
    if out_file_name and not out_file_name.endswith(".png"):
        usage()
        print "output image file name must end in .png"
        sys.exit(1)
    
    if len(args) != 1:
        usage()
        print "no city file specified"
        sys.exit(1)
    
    city_file=args[0]
    
    # locked_points = ([2,3], [5,6])
    locked_points = ()

    coords=read_coords(file(city_file))

    coords = [(192.49811427526637, 437.82539146188503), (37.38476905682632, 303.3252337906583), (324.8259036627504, 313.04541667430453), (48.109913505075994, 357.2441760340979), (185.38198582598403, 148.82859113751616), (212.38162951867002, 154.65258946790118), (40.092065136406156, 275.83759540497977), (328.6012055342977, 285.6840056751803), (326.9660195563546, 258.1118116583475), (157.76492700636965, 148.38386848430832), (40.09206513640614, 330.8128721763362), (315.78519667542366, 339.1445609754807), (104.9067377594574, 163.4932326544132), (301.8265138717525, 362.97846309978337), (219.9932508035354, 435.1953375886427), (114.28696895044655, 413.8601247375605), (138.6095191030235, 426.94879427115706), (165.01819102861234, 435.0408745482511), (48.10991350507606, 249.40629154721796), (130.59176114243957, 153.33551195043728)]

    tsp = TSP.TSP()

    # this is meant to show there are few ways of setting these variables
    #  but they do all have to be set
    tsp.set_coords(coords)
    tsp.start_temp = start_temp
    tsp.alpha = alpha
    thing = tsp.anneal(locked_points=locked_points, iterations = max_iterations)
    print thing


    # output results
    # print tsp.iterations,tsp.best_score
    # print tsp.best
    
    if out_file_name:
        title = '%s: %lf' % (city_file, tsp.best_score)
        tsp.write_tour_to_img(coords,thing,locked_points, title ,file(out_file_name,'w'))

if __name__ == "__main__":
    main()
