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
import dataclasses

from pytest import approx

import modelviewprojection.mathutils as mathutils

from modelviewprojection.mathutils1d import Vector1D

import typing


# doc-region-begin define vector class
@dataclasses.dataclass
class Vector2D(Vector1D):
    y: float  #: The y-component of the 2D Vector
    # doc-region-end define vector class

    # doc-region-begin define add
    def __add__(self, rhs: typing.Self) -> typing.Self:
        """
        Add together two Vector2Ds.

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\\\ a_y \\end{pmatrix}`
        and :math:`\\vec{b} = \\begin{pmatrix} b_x \\\\ b_y \\end{pmatrix}`:

        .. math::

             \\vec{a} + \\vec{b} = \\begin{pmatrix} a_x + b_x \\\\ a_y + b_y \\end{pmatrix}

        Args:
            rhs (Vector2D): The vector on the right hand side of the addition
                            symbol
        Returns:
            Vector2D: The Vector2D that represents the additon of the two
                      input Vector2Ds
        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils2d import Vector2D
            >>> a = Vector2D(x=2.0, y=3.0)
            >>> b = Vector2D(x=5.0, y=6.0)
            >>> a + b
            Vector2D(x=7.0, y=9.0)
        """

        return Vector2D(x=(self.x + rhs.x), y=(self.y + rhs.y))

    # doc-region-end define add

    # doc-region-begin define mul
    def __mul__(self, scalar: float) -> typing.Self:
        """
        Multiply the Vector2D by a scalar number

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\\\ a_y \\end{pmatrix}` and constant scalar :math:`s`:

        .. math::

             s*\\vec{a} = \\begin{pmatrix} s*a_x \\\\ s*a_y \\end{pmatrix}

        Args:
            rhs (Vector2D): The scalar to be multiplied to the Vector's component
                            subtraction symbol
        Returns:
            Vector2D: The Vector2D that represents scalar times the amount of the input Vector2D

        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils2d import Vector2D
            >>> a = Vector2D(x=2.0, y=3.0)
            >>> a * 4
            Vector2D(x=8.0, y=12.0)
        """
        return Vector2D(x=(self.x * scalar), y=(self.y * scalar))

    # doc-region-end define mul


def scale(m_x: float, m_y: float) -> mathutils.InvertibleFunction[Vector2D]:
    def f(vector: Vector2D) -> Vector2D:
        return Vector2D(vector.x * m_x, vector.y * m_y)

    def f_inv(vector: Vector2D) -> Vector2D:
        if m_x == 0.0 or m_y == 0.0:
            raise ValueError(
                "Note invertible.  Scaling factors cannot be zero."
            )

        return Vector2D(vector.x / m_x, vector.y / m_y)

    return mathutils.InvertibleFunction[Vector2D](f, f_inv)


# doc-region-begin define rotate
def rotate_90_degrees() -> mathutils.InvertibleFunction[Vector2D]:
    def f(vector: Vector2D) -> Vector2D:
        return Vector2D(-vector.y, vector.x)

    def f_inv(vector: Vector2D) -> Vector2D:
        return -f(vector)

    return mathutils.InvertibleFunction[Vector2D](f, f_inv)


def rotate(angle_in_radians: float) -> typing.Callable[[Vector2D], Vector2D]:
    r90: mathutils.InvertibleFunction[Vector2D] = rotate_90_degrees()

    def create_rotate_function(
        perp: mathutils.InvertibleFunction[Vector2D],
    ) -> typing.Callable[[Vector2D], Vector2D]:
        def f(vector: Vector2D) -> Vector2D:
            parallel: Vector2D = math.cos(angle_in_radians) * vector
            perpendicular: Vector2D = math.sin(angle_in_radians) * perp(vector)
            return parallel + perpendicular

        return f

    return mathutils.InvertibleFunction[Vector2D](
        create_rotate_function(r90),
        create_rotate_function(mathutils.inverse(r90)),
    )
    # doc-region-end define rotate


# doc-region-begin define rotate around
def rotate_around(
    angle_in_radians: float, center: Vector2D
) -> mathutils.InvertibleFunction[Vector2D]:
    return mathutils.compose(
        mathutils.translate(center),
        rotate(angle_in_radians),
        mathutils.translate(-center),
    )
    # doc-region-end define rotate around


def cosine(v1: Vector2D, v2: Vector2D) -> bool:
    return v1.dot(v2) / (abs(v1) * (abs(v2)))


def sine(v1: Vector2D, v2: Vector2D) -> bool:
    return rotate_90_degrees()(v1).dot(v2) / (abs(v1) * (abs(v2)))


# doc-region-begin clockwise
def is_clockwise(v1: Vector2D, v2: Vector2D) -> bool:
    return sine(v1, v2) > 0.0
    # doc-region-end clockwise


# doc-region-begin parallel
def is_parallel(v1: Vector2D, v2: Vector2D) -> bool:
    return cosine(v1, v2) == approx(1.0, abs=0.01)
    # doc-region-end parallel
