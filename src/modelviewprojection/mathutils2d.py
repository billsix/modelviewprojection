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


from __future__ import annotations  # to appease Python 3.7-3.9

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
from pytest import approx

from modelviewprojection.mathutils import InvertibleFunction, compose, inverse


# doc-region-begin define vector class
@dataclass
class Vector2D:
    x: float  #: The x-component of the 2D Vector
    y: float  #: The y-component of the 2D Vector
    # doc-region-end define vector class

    # doc-region-begin define add
    def __add__(self, rhs: Vector2D) -> Vector2D:
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

    # doc-region-begin define subtract
    def __sub__(self, rhs: Vector2D) -> Vector2D:
        """
        Subtract the right hand side Vector2D from the left hand side Vector2D.

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\\\ a_y \\end{pmatrix}`
        and :math:`\\vec{b} = \\begin{pmatrix} b_x \\\\ b_y \\end{pmatrix}`:

        .. math::

             \\vec{a} - \\vec{b} = \\vec{a} + \\vec{b} = \\begin{pmatrix} a_x - b_x \\\\ a_y - b_y \\end{pmatrix}

        Args:
            rhs (Vector2D): The vector on the right hand side of the
                            subtraction symbol
        Returns:
            Vector2D: The Vector2D that represents the subtraction of the
                      right hand side Vector2D from the left hand side
                      Vector2D
        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils2d import Vector2D
            >>> a = Vector2D(x=2.0, y=3.0)
            >>> b = Vector2D(x=5.0, y=2.0)
            >>> a - b
            Vector2D(x=-3.0, y=1.0)
        """
        return Vector2D(x=(self.x - rhs.x), y=(self.y - rhs.y))

    # doc-region-end define subtract

    # doc-region-begin define mul
    def __mul__(self, scalar: float) -> Vector2D:
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

    def __rmul__(self, scalar: float) -> Vector2D:
        return self * scalar

    # doc-region-end define mul

    def __neg__(self) -> Vector2D:
        """
        Multiply the Vector2D by -1

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\\\ a_y \\end{pmatrix}` and constant :math:`-1`:

        .. math::

             -1 * \\vec{a}

        Returns:
            Vector2D: The Vector2D with the opposite orientation

        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils2d import Vector2D
            >>> a = Vector2D(x=2.0, y=3.0)
            >>> -a
            Vector2D(x=-2.0, y=-3.0)
        """
        return -1.0 * self

    def __abs__(self) -> float:
        return np.sqrt(self.dot(self))

    def dot(self, rhs: Vector2D) -> float:
        return self.x * rhs.x + self.y * rhs.y


# doc-region-begin define translate
def translate(b: Vector2D) -> InvertibleFunction[Vector2D]:
    def f(vector: Vector2D) -> Vector2D:
        return vector + b

    def f_inv(vector: Vector2D) -> Vector2D:
        return vector - b

    return InvertibleFunction[Vector2D](f, f_inv)
    # doc-region-end define translate


# doc-region-begin define uniform scale
def uniform_scale(m: float) -> InvertibleFunction[Vector2D]:
    def f(vector: Vector2D) -> Vector2D:
        return vector * m

    def f_inv(vector: Vector2D) -> Vector2D:
        if m == 0.0:
            raise ValueError("Note invertible.  Scaling factor cannot be zero.")

        return vector * (1.0 / m)

    return InvertibleFunction[Vector2D](f, f_inv)
    # doc-region-end define uniform scale


def scale(m_x: float, m_y: float) -> InvertibleFunction[Vector2D]:
    def f(vector: Vector2D) -> Vector2D:
        return Vector2D(vector.x * m_x, vector.y * m_y)

    def f_inv(vector: Vector2D) -> Vector2D:
        if m_x == 0.0 or m_y == 0.0:
            raise ValueError(
                "Note invertible.  Scaling factors cannot be zero."
            )

        return Vector2D(vector.x / m_x, vector.y / m_y)

    return InvertibleFunction[Vector2D](f, f_inv)


# doc-region-begin define rotate
def rotate_90_degrees() -> InvertibleFunction[Vector2D]:
    def f(vector: Vector2D) -> Vector2D:
        return Vector2D(-vector.y, vector.x)

    def f_inv(vector: Vector2D) -> Vector2D:
        return -f(vector)

    return InvertibleFunction[Vector2D](f, f_inv)


def rotate(angle_in_radians: float) -> Callable[[Vector2D], Vector2D]:
    r90: InvertibleFunction[Vector2D] = rotate_90_degrees()

    def create_rotate_function(
        perp: InvertibleFunction[Vector2D],
    ) -> Callable[[Vector2D], Vector2D]:
        def f(vector: Vector2D) -> Vector2D:
            parallel: Vector2D = math.cos(angle_in_radians) * vector
            perpendicular: Vector2D = math.sin(angle_in_radians) * perp(vector)
            return parallel + perpendicular

        return f

    return InvertibleFunction[Vector2D](
        create_rotate_function(r90), create_rotate_function(inverse(r90))
    )
    # doc-region-end define rotate


# doc-region-begin define rotate around
def rotate_around(
    angle_in_radians: float, center: Vector2D
) -> InvertibleFunction[Vector2D]:
    return compose(
        translate(center), rotate(angle_in_radians), translate(-center)
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
