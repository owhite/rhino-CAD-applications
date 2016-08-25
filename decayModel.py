#!/usr/bin/env python2.7

import math
import matplotlib.pyplot as plt

class Decay:
    def __init__(self):
        # Using radioactive decay for acceleration
        #  where the count of atoms is used as the length of delay between
        #  each loop moving a motor. Decay of the atoms over the loops
        #  speeds up the motor
        self.accelTime = 600    # Number of loops to arrive at velocity
        self.startDelay = 40000	# Number of atoms at t = 0, starting velocity
        self.finalDelay = 100   # Number of atoms to decay to, ending velocity
        self.decayConstant = .01

        # find final decay point using the above parameters
        N = float(self.startDelay)
        L = self.decayConstant
        t = 0
        while t < self.accelTime:
	    N = N - (L * N)
            t += 1
        self.endPoint = N

        # The issue is the decay of our atoms may be much larger or smaller
        #  than what we want. But presumably we love the rate. So
        # Scale our final end point to our desired endpoint
        #  do this by getting ranges
        self.leftSpan = self.startDelay - self.endPoint
        self.rightSpan = self.startDelay - self.finalDelay

    def calcDecay(self, N):
        # this is the loss of atoms
        N = N - (d.decayConstant * N)
        # now scale our current value to our desired endpoint
        s = float(N - self.endPoint) / float(self.leftSpan)
        return (N, self.finalDelay + (s * self.rightSpan))

if __name__ == "__main__":
    x = []    # each loop number
    y = []    # decay results

    d = Decay()
    N = d.startDelay

    t = 0
    while t < d.accelTime:
        (N, s) = d.calcDecay(N)
	x.append(t)
	y.append(s)
	t += 1

    plt.plot(x, y)
    plt.show()

