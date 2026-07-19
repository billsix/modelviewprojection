# Copyright (c) 2018-2026 William Emerison Six
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
import typing

import numpy as np

#: One axis of plot data.  matplotlib takes parallel arrays, so a 2-D point set
#: is the pair ``(xs, ys)``.
Axis = typing.Sequence[float]
#: A 2-D transform over that pair.  The result is ``Iterable``, not ``tuple``,
#: because ``map_matplotlib_data`` hands back a ``zip`` object while
#: :func:`compose` hands back a tuple -- callers unpack either as ``xs, ys``.
PlotTransform = typing.Callable[[Axis, Axis], typing.Iterable[Axis]]


def map_matplotlib_data(
    f: typing.Callable[[typing.Sequence[float]], typing.Sequence[float]],
    *points_on_axis: Axis,
) -> typing.Iterable[Axis]:
    """In plotting with numpy, the points on a given axis are supposed
    to be their own arrays, which is not helpful when wanting to transform
    points.  map_matplotlib_data
    allows the programmer to transform each x,y pair by function f

    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([0.0,0.0])
    >>> txs, tys = map_matplotlib_data(
    ...     lambda point: (point[0]+1.0, point[1]+1.0), xs, ys
    ... )
    >>> tuple(float(v) for v in txs)
    (-4.0, 6.0)
    >>> tuple(float(v) for v in tys)
    (1.0, 1.0)
    >>> # regardless of the number of arguments, map_matplotlib_data works!
    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([.0,.0])
    >>> zs = np.array([2.0,3.0])
    >>> txs, tys, tzs =map_matplotlib_data(lambda point: (point[0]+1.0,
    ...                                                 point[1]+1.0,
    ...                                                 point[2]-1.0),
    ...                                  xs,
    ...                                  ys,
    ...                                  zs)
    >>> tuple(float(v) for v in txs)
    (-4.0, 6.0)
    >>> tuple(float(v) for v in tys)
    (1.0, 1.0)
    >>> tuple(float(v) for v in tzs)
    (1.0, 2.0)
    """
    return zip(*map(f, zip(*points_on_axis)))


def _rotate_point(angle: float, x: float, y: float) -> tuple[float, float]:
    """Rotate an X and Y value by an angle

    >>> x = 1.0
    >>> y = 0.0
    >>> _rotate_point(math.radians(0.0),x,y)
    (1.0, 0.0)

    >>> x = 0.0
    >>> y = 1.0
    >>> _rotate_point(math.radians(0.0),x,y)
    (0.0, 1.0)

    >>> x = 1.0
    >>> y = 0.0
    >>> _rotate_point(math.radians(45.0),x,y)
    (0.7071067811865476, 0.7071067811865475)

    >>> x = 5.0
    >>> y = 0.0
    >>> _rotate_point(math.radians(45.0),x,y)
    (3.5355339059327378, 3.5355339059327373)


    >>> x = 5.0
    >>> y = 0.0
    >>> _rotate_point(math.radians(0.1),x,y)
    (4.999992384566438, 0.008726641829491543)
    """
    return (
        x * math.cos(angle) - y * math.sin(angle),
        x * math.sin(angle) + y * math.cos(angle),
    )


def rotate(angle: float) -> PlotTransform:
    """Rotate the xs and ys by angle
    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([0.0,0.0])
    >>> for transformed_axis in rotate(math.radians(0.1))(xs,ys):
    ...      print(tuple(float(v) for v in transformed_axis))
    (-4.999992384566438, 4.999992384566438)
    (-0.008726641829491543, 0.008726641829491543)
    """
    return lambda xs, ys: map_matplotlib_data(
        lambda point: _rotate_point(angle, point[0], point[1]), xs, ys
    )


def scale(scale_x: float, scale_y: float) -> PlotTransform:
    """Scale the xs and ys

    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([1.0,1.0])
    >>> for transformed_axis in scale(2,2)(xs,ys):
    ...      print(tuple(float(v) for v in transformed_axis))
    (-10.0, 10.0)
    (2.0, 2.0)
    """
    return lambda xs, ys: map_matplotlib_data(
        lambda point: (point[0] * scale_x, point[1] * scale_y), xs, ys
    )


def translate(tx: float, ty: float) -> PlotTransform:
    """translate the xs and ys

    >>> xs = np.array([-5.0,5.0])
    >>> ys = np.array([1.0,1.0])
    >>> for transformed_axis in translate(1,2)(xs,ys):
    ...      print(tuple(float(v) for v in transformed_axis))
    (-4.0, 6.0)
    (3.0, 3.0)
    """
    return lambda xs, ys: map_matplotlib_data(
        lambda point: (point[0] + tx, point[1] + ty), xs, ys
    )


if __name__ == "__main__":
    # np is need for doctest and don't want autoflake to remove it
    ignore = np.eye(1)


def compose(*transforms: PlotTransform) -> PlotTransform:
    """Apply ``transforms`` right-to-left, like function composition.

    ``compose(translate(...), scale(...), rotate(...))`` rotates first, then
    scales, then translates -- the same order the maths is written in, and the
    same order the ``procedures=[...]`` lists elsewhere in this package use.
    Without it a chained transform has to be written inside-out, re-splatting
    each stage's ``(xs, ys)`` into the next.

    >>> xs = np.array([1.0, 2.0])
    >>> ys = np.array([0.0, 0.0])
    >>> shift_then_double = compose(scale(2, 2), translate(1, 0))
    >>> for axis in shift_then_double(xs, ys):
    ...     print(tuple(float(v) for v in axis))
    (4.0, 6.0)
    (0.0, 0.0)
    """

    def composed(xs: Axis, ys: Axis) -> typing.Iterable[Axis]:
        for transform in reversed(transforms):
            xs, ys = transform(xs, ys)
        return xs, ys

    return composed
