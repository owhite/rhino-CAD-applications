#!/usr/bin/python

import random
import sys
import math
import getopt
from PIL import Image, ImageDraw, ImageFont
from math import sqrt

# TSP is passed a set of coordinate positions and attempts to find
#  the shortest path between them. TSP specifies the path by returning 
#  a list that orders the points. 
#
# This is a fork of John Montgomery's algorithm described here:
#   http://www.psychicorigami.com/category/tsp/
#   which performs recombinations between points and uses simulated annealing 
#   test the success of those recombinations over a series of iterations.
#
# This implementation is different in that it
#  -strips away a lot of alternative methods originally created 
#     by John for hill climbing and recombinations. It also has a
#     lot less logging
#  -is now a boni fide module that can be called by other programs
#    see tsp_test.py for an example
#  -supports locked points
#
# What are the locked points? John's TSP algorithm performed 
#   recombination on all the coordinate positions that are tested. But
#   in this case I do not want the algorithm to do recombination on
#   those points - using the traveling salesman analogy locked points
#   would occur when the salesman wanted to travel from one particular
#   city to another - even if it took longer. To constrain the tour
#   of cities you can pass the algorithm pairs of points that are not 
#   allowed to be recombined.
# 
# Note: there are several functions that have the same name as John's
#  original code that operate somewhat differently as his.
#
# TSP Licensing: John Montgomery uses:
#   http://creativecommons.org/licenses/by/3.0/ Which is
#   super-awesome. This means This means you can use the code 
#   for more or less any purpose you want, but must provide 
#   some form of attribution.

class TSP:
    def __init__(self, *args, **kwargs):
        self.reset()
        self.handle_opts(kwargs)

    def handle_opts(self, kwargs):

        if kwargs.get('coords', None) != None:
            self.set_coords(kwargs.get('coords'))

        if kwargs.get('start_temp', None) != None:
            self.start_temp = kwargs.get('start_temp')

        if kwargs.get('alpha', None) != None:
            self.alpha = kwargs.get('alpha')

        if kwargs.get('locked_points') != None:
            self.locked_points = kwargs.get('locked_points', None)

        if kwargs.get('iterations', None) != None:
            self.iterations = kwargs.get('iterations')

    def reset(self):
        self.best=None
        self.best_score=None
        self.start_temp = None
        self.locked_points = None
        self.alpha=None
        self.coords = None
        self.current=None
        self.iterations=None
        self.matrix = None
        

    def check(self):
        if self.coords is None:
            print 'tsp cant run without coords, call tsp.set_coords'

        if self.start_temp is None:
            print 'tsp cant run without self.start_temp = int'

        if self.alpha is None:
            print 'tsp cant run without self.alpha = int'

        if self.iterations is None:
            print 'tsp cant run without self.iterations = int'

        if self.locked_points is None:
            print 'tsp cant run with self.locked_points = None'

    def set_coords(self, coords):
        self.coords = coords
        self.current=range(len(coords)) # the current tour of points
        self.matrix = self.cartesian_matrix(coords)
    
    def objective_function(self,solution):
        '''total up the total length of the tour based on the distance matrix'''
        score=0
        num_cities=len(solution)
        for i in range(num_cities):
            j=(i+1)%num_cities
            city_i=solution[i]
            city_j=solution[j]
            score+=self.matrix[city_i,city_j]
        score *= -1
        if self.best is None or score > self.best_score:
            self.best_score=score
            self.best=solution
        return score

    def kirkpatrick_cooling(self):
        T=self.start_temp
        while True:
            yield T
            T=self.alpha*T

    def p_choice(self, prev_score,next_score,temperature):
        if next_score > prev_score:
            return 1.0
        else:
            return math.exp( -abs(next_score-prev_score)/temperature )

    def rand_seq(self,size,positions):
        values=range(size)
        inc = 0
        for i in positions:
            del values[i-inc]
            inc += 1
    
        size -= len(positions)
    
        for i in xrange(size):
            # pick a random index into remaining values
            j=i+int(random.random()*(size-i))
            # swap the values
            values[j],values[i]=values[i],values[j]
            # restore the value if it is in our special list
            yield values[i] 
    
    def all_pairs(self,size,positions):
        '''generates all i,j pairs for i,j from 0-size'''
        for i in self.rand_seq(size, positions):
            for j in self.rand_seq(size,positions):
                yield (i,j)
    
    def reversed_sections(self):
        '''return all variations where the 
        section between two cities are swappedd'''
        positions = self.find_locked_points()
        for i,j in self.all_pairs(len(self.current), positions):
            # print 'ij %d %d' % (i, j)
            if i != j and abs(i-j) != 1:
                copy=self.current[:]
                if i < j:
                    copy[i:j]=reversed(self.current[i:j])
                else:
                    copy[j:i]=reversed(self.current[j:i])
                    copy.reverse()
                if copy != self.current: # no point returning the same tour
                    # print 'copy %s' % (copy)
                    yield copy

    def find_locked_points(self):
        # points is a list of positions that are linked to 
        #  each element in the array. For this list:
        #  [pos1, pos2, pos3]
        #  The locked_points refer the comma's separating the positions
        #  [,pos1, pos2, pos3,]. 
        # there was not a strong logical reason for doing this, it
        #  just was a winner over a couple other attempts. 
        l = []
        list = self.current
        for i in self.locked_points:
            (e1, e2) = i
            p1 = list.index(e1)
            p2 = list.index(e2)
            if p1 < p2:
                if (p2 - p1) != 1:
                    print "p1 and p2 not next to each other"
                    # sys.exit(1)
                l.append(p2)
            else:
                if (p1 - p2) != 1:
                    print "p2 and p1 not next to each other"
                    # sys.exit(1)
                l.append(p1)
        return sorted(l)

    def cartesian_matrix(self,coords):
        '''create a distance matrix for the city coords 
        that uses straight line distance'''
        matrix={}
        for i,(x1,y1) in enumerate(coords):
            for j,(x2,y2) in enumerate(coords):
                dx,dy=x1-x2,y1-y2
                dist=sqrt(dx*dx + dy*dy)
                matrix[i,j]=dist
        return matrix

    def read_coords(self,coord_file):
        ''' read coordinates file return the distance matrix.
        coords should be stored as comma separated floats, 
        one x,y pair per line. '''
        coords=[]
        for line in coord_file:
            x,y=line.strip().split(',')
            coords.append((float(x),float(y)))
        return coords

    def write_tour_to_img(self,coords,tour,locked_points,title,img_file):
        # a cheezebag display of the tour, doesnt even scale small routes
        padding=20
        # shift all coords in a bit
        coords=[(x+padding,y+padding) for (x,y) in coords]
        maxx,maxy=0,0
        for x,y in coords:
            maxx=max(x,maxx)
            maxy=max(y,maxy)
        maxx+=padding
        maxy+=padding
        img=Image.new("RGB",(int(maxx),int(maxy)),color=(255,255,255))
        
        font=ImageFont.load_default()
        d=ImageDraw.Draw(img);
        num_cities=len(tour)
        for x,y in coords:
            x,y=int(x),int(y)
            d.ellipse((x-5,y-5,x+5,y+5),outline=(0,0,0),fill=(196,196,196))
    
        inc = 0
        for i in range(num_cities):
            j=(i+1)%num_cities
            city_i=tour[i]
            city_j=tour[j]
            x1,y1=coords[city_i]
            x2,y2=coords[city_j]
            d.line((int(x1),int(y1),int(x2),int(y2)),fill=(0,0,0))
            d.text((int(x1)+7,int(y1)-5),str(i),font=font,fill=(32,32,32))
            inc += 1
        
        for i in locked_points:
            (x, y) = i
            (x1, y1) = coords[x]
            (x2, y2) = coords[y]
            x,y=int(x1),int(y1)
            d.ellipse((x-5,y-5,x+5,y+5),outline=(0,0,0),fill=(255,0,0))
    
            x,y=int(x2),int(y2)
            d.ellipse((x-5,y-5,x+5,y+5),outline=(0,0,0),fill=(255,0,0))
    
        d.text((1,1),title,font=font,fill=(0,0,0))
        
        del d
        img.save(img_file, "PNG")
    
    def report_stats(self):
        print self.matrix
        print self.coords 
        print self.current
        print self.best
        print self.best_score
        print self.start_temp 
        print self.locked_points 
        print self.alpha
        print self.iterations

    def anneal(self, *args, **kwargs):
        self.handle_opts(kwargs)
        current_score=self.objective_function(self.current)
        num_evaluations=1
    
        self.check()

        cooling_schedule=self.kirkpatrick_cooling()
        
        for temperature in cooling_schedule:
            done = False
            # examine moves around our current position
            for next in self.reversed_sections():
                if num_evaluations >= self.iterations:
                    done=True
                    break
                
                next_score=self.objective_function(next)
                num_evaluations+=1
                
                # probablistically accept this solution
                # always accepting better solutions
                p=self.p_choice(current_score,next_score,temperature)
                if random.random() < p:
                    self.current=next
                    current_score=next_score
                    break
            # see if completely finished
            if done: break
        
        # self.report_stats()

        self.iterations = num_evaluations
        return self.best
