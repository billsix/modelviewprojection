# Copyright (c) 2018-2025 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import math

import numpy as np


def mapMatplotlibData(f, *pointsOnAxis):
    """In plotting with numpy, the points on a given axis are supposed
    to be their own arrays, which is not helpful when wanting to transform
    points.  mapMatplotlibData
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
    >>> ys = np.array([.0,.0])
    >>> zs = np.array([2.0,3.0])
    >>> txs, tys, tzs =mapMatplotlibData(lambda point: (point[0]+1.0,
    ...                                                 point[1]+1.0,
    ...                                                 point[2]-1.0),
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


if __name__ == "__main__":
    # np is need for doctest and don't want autoflake to remove it
    ignore = np.eye()
