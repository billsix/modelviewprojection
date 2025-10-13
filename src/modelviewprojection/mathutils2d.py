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


import dataclasses
import math
import typing

import pytest

import modelviewprojection.mathutils as mu
import modelviewprojection.mathutils1d as mu1d

# for ease of use in importing and using
from modelviewprojection.mathutils import (
    InvertibleFunction,
    compose,
    inverse,
    translate,
    uniform_scale,
    Vector
)

__all__ = [
    "Vector2D",
    "scale",
    "rotate_90_degrees",
    "rotate",
    "rotate_around",
    "sine",
    "is_counter_clockwise",
    "is_clockwise",
    "is_parallel",
    "translate",
    "uniform_scale",
    "InvertibleFunction",
    "inverse",
    "compose",
    "Vector",
]


# doc-region-begin define vector class
@dataclasses.dataclass
class Vector2D(mu1d.Vector1D):
    y: float  #: The y-component of the 2D Vector
    # doc-region-end define vector class

    # doc-region-begin define add
    def __add__(self, rhs: "mu.Vector") -> "Vector2D":
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

        assert isinstance(rhs, Vector2D)
        return Vector2D(x=(self.x + rhs.x), y=(self.y + rhs.y))

    # doc-region-end define add

    # doc-region-begin define mul
    def __mul__(self, scalar: float) -> "Vector2D":
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


def scale(m_x: float, m_y: float) -> mu.InvertibleFunction:
    def f(vector: Vector2D) -> Vector2D:
        return Vector2D(vector.x * m_x, vector.y * m_y)

    def f_inv(vector: Vector2D) -> Vector2D:
        if m_x == 0.0 or m_y == 0.0:
            raise ValueError(
                "Note invertible.  Scaling factors cannot be zero."
            )

        return Vector2D(vector.x / m_x, vector.y / m_y)

    return mu.InvertibleFunction(f, f_inv)


# doc-region-begin define rotate
def rotate_90_degrees() -> mu.InvertibleFunction:
    def f(vector: mu.Vector) -> mu.Vector:
        assert isinstance(vector, Vector2D)
        return Vector2D(-vector.y, vector.x)

    def f_inv(vector: mu.Vector) -> mu.Vector:
        return -f(vector)

    return mu.InvertibleFunction(f, f_inv)


def rotate(angle_in_radians: float) -> mu.InvertibleFunction:
    r90: mu.InvertibleFunction = rotate_90_degrees()

    def create_rotate_function(
        perp: mu.InvertibleFunction,
    ) -> typing.Callable[[mu.Vector], mu.Vector]:
        def f(vector: mu.Vector) -> mu.Vector:
            parallel: mu.Vector = math.cos(angle_in_radians) * vector
            perpendicular: mu.Vector = math.sin(angle_in_radians) * perp(vector)
            return parallel + perpendicular

        return f

    return mu.InvertibleFunction(
        create_rotate_function(r90),
        create_rotate_function(mu.inverse(r90)),
    )
    # doc-region-end define rotate


# doc-region-begin define rotate around
def rotate_around(
    angle_in_radians: float, center: Vector2D
) -> mu.InvertibleFunction:
    return mu.compose(
        [mu.translate(center), rotate(angle_in_radians), mu.translate(-center)]
    )
    # doc-region-end define rotate around


def cosine(v1: mu.Vector, v2: mu.Vector) -> float:
    assert isinstance(v1, Vector2D)
    assert isinstance(v2, Vector2D)
    return v1.dot(v2) / (abs(v1) * (abs(v2)))


def sine(v1: mu.Vector, v2: mu.Vector) -> float:
    assert isinstance(v1, Vector2D)
    assert isinstance(v2, Vector2D)
    return rotate_90_degrees()(v1).dot(v2) / (abs(v1) * (abs(v2)))


# doc-region-begin counter clockwise
def is_counter_clockwise(v1: Vector2D, v2: Vector2D) -> bool:
    return sine(v1, v2) >= 0.000000
    # doc-region-end counter clockwise


# doc-region-begin clockwise
def is_clockwise(v1: Vector2D, v2: Vector2D) -> bool:
    return not is_clockwise(v1, v2)
    # doc-region-end clockwise


# doc-region-begin parallel
def is_parallel(v1: Vector2D, v2: Vector2D) -> bool:
    return cosine(v1, v2) == pytest.approx(1.0, abs=0.01)
    # doc-region-end parallel
