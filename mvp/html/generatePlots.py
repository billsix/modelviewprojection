#Copyright (c) 2018 William Emerison Six
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import numpy as np
import matplotlib.pyplot as plt
import math
import sys
import itertools

import generategridlines
import mpltransformations as mplt


if __name__ != "__main__":
    sys.exit(0)


# TODO, generalize to any number of dimensions
def accumulate_transformation(procedures, backwards=False):
    """Given a pipeline of functions, provide all intermediate results via a function.

    >>> fs = [lambda x,y: mplt.translate(5,0,x,y),
    ...       lambda x,y: mplt.translate(0,10,x,y)]
    >>> f = accumulate_transformation(fs)
    >>> f1 = next(f)
    >>> f1((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (4, 5, 6))
    >>> f2 = next(f)
    >>> f2((1, 2, 3), (4, 5, 6))
    ((6, 7, 8), (4, 5, 6))
    >>> f3 = next(f)
    >>> f3((1, 2, 3), (4, 5, 6))
    ((6, 7, 8), (14, 15, 16))
    """

    def id(x,y):
        return x,y
    yield id

    if not backwards:
        for index1 in range(len(procedures)):
            def process(x,y):
                resultx, resulty = x,y
                for index2 in range(index1+1):
                    resultx,resulty = procedures[index2](resultx,resulty)
                return resultx, resulty
            yield process
    else:
        reversedProcs = list(range(len(procedures)))
        reversedProcs.reverse()
        for index1 in reversedProcs:
            def process(x,y):
                resultx, resulty = x,y
                for index2 in range(index1, len(procedures)):
                    resultx,resulty = procedures[index2](resultx,resulty)
                return resultx, resulty
            yield process



import doctest
modules = [mplt,sys.modules[__name__]]
for m in modules:
    try:
        doctest.testmod(m,
                        raise_on_error=True)
        print(doctest.testmod(m))
    except Exception:
        print(doctest.testmod(m))
        sys.exit(1)


## Translation Plots


## Translation Plots - reading the transformations forward

### Step 1
graphBounds = (100,100)

fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])



paddleData = list(zip(*np.array([[-10.0,-30.0],
                                 [10.0,-30.0],
                                 [10.0,30.0],
                                 [-10.0,30.0],
                                 [-10.0,-30.0]])))

def createGraphs(filename, points, procedures, color, backwards=False):

    procs = procedures.copy()

    count = 0
    lastTransform = None
    for t in accumulate_transformation(procs, backwards):
        lastTransform = t

        fig, axes = plt.subplots()
        axes.set_xlim([-graphBounds[0],graphBounds[0]])
        axes.set_ylim([-graphBounds[1],graphBounds[1]])

        #plot transformed basis
        for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
            transformedXs, transformedYs = t(xs,ys)
            plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))


        # make sure the x and y axis are equally proportional in screen space
        plt.gca().set_aspect('equal', adjustable='box')
        fig.savefig(str.format("{}-{}.png",filename, count))
        plt.close(fig)

        count += 1
    #
    fig, axes = plt.subplots()
    axes.set_xlim([-graphBounds[0],graphBounds[0]])
    axes.set_ylim([-graphBounds[1],graphBounds[1]])

    #plot transformed basis
    for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
        transformedXs, transformedYs = lastTransform(xs,ys)
        plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

    #plot the points
    transformedXs, transformedYs = lastTransform(*points)
    plt.plot(transformedXs, transformedYs, 'k-', lw=2, color=color)



    # make sure the x and y axis are equally proportional in screen space
    plt.gca().set_aspect('equal', adjustable='box')
    fig.savefig(str.format("{}-{}.png",filename, count ))
    plt.close(fig)



createGraphs(filename="translation",
             points = paddleData,
             procedures= [lambda x,y: mplt.translate(0.0,
                                                     20.0,
                                                     x,
                                                     y),
                          lambda x,y: mplt.translate(-90.0,
                                                     0.0,
                                                     x,
                                                     y)],
             color=(0.578123, 0.0, 1.0))
createGraphs(filename="translation-backwards",
             points = paddleData,
             procedures= [lambda x,y: mplt.translate(0.0,
                                                     20.0,
                                                     x,
                                                     y),
                          lambda x,y: mplt.translate(-90.0,
                                                     0.0,
                                                     x,
                                                     y)],
             color=(0.578123, 0.0, 1.0),
             backwards=True)
createGraphs(filename="translation2",
             points = paddleData,
             procedures= [lambda x,y: mplt.translate(0.0,
                                                     -40.0,
                                                     x,
                                                     y),
                          lambda x,y: mplt.translate(90.0,
                                                     0.0,
                                                     x,
                                                     y)],
             color=(1.0, 0.0, 0.0, 1.0))

createGraphs(filename="translation2-backwards",
             points = paddleData,
             procedures= [lambda x,y: mplt.translate(0.0,
                                                     -40.0,
                                                     x,
                                                     y),
                          lambda x,y: mplt.translate(90.0,
                                                     0.0,
                                                     x,
                                                     y)],
             color=(1.0, 0.0, 0.0, 1.0),
             backwards=True)



createGraphs(filename="rotate1",
             points = paddleData,
             procedures= [lambda x,y: mplt.rotate(math.radians(45.0), x, y),
                          lambda x,y: mplt.translate(0.0,
                                                     20.0,
                                                     x,
                                                     y),
                          lambda x,y: mplt.translate(-90.0,
                                                     0.0,
                                                     x,
                                                     y)],
             color=(0.578123, 0.0, 1.0))
createGraphs(filename="rotate1-backwards",
             points = paddleData,
             procedures= [lambda x,y: mplt.rotate(math.radians(45.0), x, y),
                          lambda x,y: mplt.translate(0.0,
                                                     20.0,
                                                     x,
                                                     y),
                          lambda x,y: mplt.translate(-90.0,
                                                     0.0,
                                                     x,
                                                     y)],
             color=(0.578123, 0.0, 1.0),
             backwards=True)


createGraphs(filename="rotate2",
             points = paddleData,
             procedures= [lambda x,y: mplt.rotate(math.radians(-10.0), x, y),
                          lambda x,y: mplt.translate(90.0,
                                                     0.0,
                                                     x,
                                                     y),
                          lambda x,y: mplt.translate(0.0,
                                                     -40.0,
                                                     x,
                                                     y)],
             color=(1.0, 0.0, 0.0))
createGraphs(filename="rotate2-backwards",
             points = paddleData,
             procedures= [lambda x,y: mplt.rotate(math.radians(-10.0), x, y),
                          lambda x,y: mplt.translate(90.0,
                                                     0.0,
                                                     x,
                                                     y),
                          lambda x,y: mplt.translate(0.0,
                                                     -40.0,
                                                     x,
                                                     y)],
             color=(1.0, 0.0, 0.0),
             backwards=True)
