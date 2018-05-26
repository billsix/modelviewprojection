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

import plotaxes


N = 50
x = np.random.rand(N) * 10
y = np.random.rand(N) * 10

plt.scatter(x, y)

graphBounds = (10,10)

axes = plt.gca()
axes.set_xlim([-2.0,graphBounds[0]])
axes.set_ylim([-2.0,graphBounds[1]])


def rotatePoint(angle, x, y):
    """Rotate an X and Y value by an angle

    >>> x = 1.0
    >>> y = 0.0
    >>> rotatePoint(math.radians(0.0),x,y)
    (1.0, 0.0)

    >>> x = 0.0
    >>> y = 1.0
    >>> rotatePoint(math.radians(0.0),x,y)
    (0.0, 1.0)

    >>> x = 1.0
    >>> y = 0.0
    >>> rotatePoint(math.radians(45.0),x,y)
    (0.7071067811865476, 0.7071067811865475)

    >>> x = 5.0
    >>> y = 0.0
    >>> rotatePoint(math.radians(45.0),x,y)
    (3.5355339059327378, 3.5355339059327373)


    >>> x = 5.0
    >>> y = 0.0
    >>> rotatePoint(math.radians(0.1),x,y)
    (4.999992384566438, 0.008726641829491543)
    """
    return x*math.cos(angle) - y*math.sin(angle), x*math.sin(angle) + y*math.cos(angle)


def rotate(angle, xs,ys):
    """Rotate the xs and ys by angle
    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([0.0,0.0])
    >>> for z in rotate(math.radians(0.1), xs,ys):
    ...      print(z)
    (-4.999992384566438, 4.999992384566438)
    (-0.008726641829491543, 0.008726641829491543)
    """
    return zip(*map(lambda point: rotatePoint(angle,point[0],point[1]),
                    zip(xs,ys)))


def scale(scaleX, scaleY, xs,ys):
    """Scale the xs and ys

    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([1.0,1.0])
    >>> for z in scale(2,2, xs,ys):
    ...      print(z)
    (-10.0, 10.0)
    (2.0, 2.0)
    """
    return zip(*map(lambda point: (point[0] * scaleX , point[1] * scaleY),
                    zip(xs,ys)))

if __name__ == "__main__":
    import doctest
    try:
        doctest.testmod(raise_on_error=True)
    except Exception:
        print(doctest.testmod())
        sys.exit(1)

    #plot natural basis
    for xs, ys, thickness in plotaxes.plotaxis(graphBounds):
        plt.plot(xs, ys, 'k-', lw=thickness)

    #plot different basis
    for xs, ys, thickness in plotaxes.plotaxis(graphBounds):
        transformedXs, transformedYs = list(scale(math.sqrt(8),math.sqrt(8),*rotate(math.radians(45.0), xs, ys)))
        plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color='green')

    # make sure the x and y axis are equally proportional in screen space
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
