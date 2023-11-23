# Copyright (c) 2018-2020 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import math


def mapMatplotlibData(f, *pointsOnAxis):
    """In plotting with numpy, the points on a given axis are supposed to be their own arrays,
    which is not helpful when wanting to transform points.  mapMatplotlibData
    allows the programmer to transform each x,y pair by function f

    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([0.0,0.0])
    >>> txs, tys = mapMatplotlibData(lambda point: (point[0]+1.0, point[1]+1.0),
    ...                              xs,
    ...                              ys)
    >>> txs
    (-4.0, 6.0)
    >>> tys
    (1.0, 1.0)
    >>> # regardless of the number of arguments, mapMatplotlibData works!
    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([0.0,0.0])
    >>> zs = np.array([2.0,3.0])
    >>> txs, tys, tzs =mapMatplotlibData(lambda point: (point[0]+1.0, point[1]+1.0, point[2]-1.0),
    ...                                  xs,
    ...                                  ys,
    ...                                  zs)
    >>> txs
    (-4.0, 6.0)
    >>> tys
    (1.0, 1.0)
    >>> tzs
    (1.0, 2.0)
    """
    return zip(*map(f, zip(*pointsOnAxis)))


def _rotatePoint(angle, x, y):
    """Rotate an X and Y value by an angle

    >>> x = 1.0
    >>> y = 0.0
    >>> _rotatePoint(math.radians(0.0),x,y)
    (1.0, 0.0)

    >>> x = 0.0
    >>> y = 1.0
    >>> _rotatePoint(math.radians(0.0),x,y)
    (0.0, 1.0)

    >>> x = 1.0
    >>> y = 0.0
    >>> _rotatePoint(math.radians(45.0),x,y)
    (0.7071067811865476, 0.7071067811865475)

    >>> x = 5.0
    >>> y = 0.0
    >>> _rotatePoint(math.radians(45.0),x,y)
    (3.5355339059327378, 3.5355339059327373)


    >>> x = 5.0
    >>> y = 0.0
    >>> _rotatePoint(math.radians(0.1),x,y)
    (4.999992384566438, 0.008726641829491543)
    """
    return (
        x * math.cos(angle) - y * math.sin(angle),
        x * math.sin(angle) + y * math.cos(angle),
    )


def rotate(angle):
    """Rotate the xs and ys by angle
    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([0.0,0.0])
    >>> for transformedAxis in rotate(math.radians(0.1))(xs,ys):
    ...      print(transformedAxis)
    (-4.999992384566438, 4.999992384566438)
    (-0.008726641829491543, 0.008726641829491543)
    """
    return lambda xs, ys: mapMatplotlibData(
        lambda point: _rotatePoint(angle, point[0], point[1]), xs, ys
    )


def scale(scaleX, scaleY):
    """Scale the xs and ys

    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([1.0,1.0])
    >>> for transformedAxis in scale(2,2)(xs,ys):
    ...      print(transformedAxis)
    (-10.0, 10.0)
    (2.0, 2.0)
    """
    return lambda xs, ys: mapMatplotlibData(
        lambda point: (point[0] * scaleX, point[1] * scaleY), xs, ys
    )


def translate(tx, ty):
    """translate the xs and ys

    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([1.0,1.0])
    >>> for transformedAxis in translate(1,2)(xs,ys):
    ...      print(transformedAxis)
    (-4.0, 6.0)
    (3.0, 3.0)
    """
    return lambda xs, ys: mapMatplotlibData(
        lambda point: (point[0] + tx, point[1] + ty), xs, ys
    )
