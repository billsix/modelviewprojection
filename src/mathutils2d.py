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

from mathutils import InvertibleFunction, compose, inverse


# doc-region-begin define vector class
@dataclass
class Vector2D:
    x: float
    y: float
    # doc-region-end define vector class

    # doc-region-begin define add
    def __add__(self, rhs: Vector2D) -> Vector2D:
        return Vector2D(x=(self.x + rhs.x), y=(self.y + rhs.y))

    # doc-region-end define add

    # doc-region-begin define subtract
    def __sub__(self, rhs: Vector2D) -> Vector2D:
        return Vector2D(x=(self.x - rhs.x), y=(self.y - rhs.y))

    # doc-region-end define subtract

    # doc-region-begin define mul
    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(x=(self.x * scalar), y=(self.y * scalar))

    def __rmul__(self, scalar: float) -> Vector2D:
        return self * scalar

    # doc-region-end define mul

    def __neg__(self) -> Vector2D:
        return -1.0 * self


# doc-region-begin define translate
def translate(translate_amount: Vector2D) -> InvertibleFunction:
    def f(vector: Vector2D) -> Vector2D:
        return vector + translate_amount

    def f_inv(vector: Vector2D) -> Vector2D:
        return vector - translate_amount

    return InvertibleFunction(f, f_inv)


# doc-region-end define translate


# doc-region-begin define uniform scale
def uniform_scale(scalar: float) -> InvertibleFunction:
    def f(vector: Vector2D) -> Vector2D:
        return vector * scalar

    def f_inv(vector: Vector2D) -> Vector2D:
        if scalar == 0:
            raise ValueError("Note invertible.  Scaling factor cannot be zero.")

        return vector * (1.0 / scalar)

    return InvertibleFunction(f, f_inv)


# doc-region-end define uniform scale


def scale(scale_x: float, scale_y: float) -> InvertibleFunction:
    def f(vector: Vector2D) -> Vector2D:
        return Vector2D(vector.x * scale_x, vector.y * scale_y)

    def f_inv(vector: Vector2D) -> Vector2D:
        if scale_x == 0 or scale_y == 0:
            raise ValueError(
                "Note invertible.  Scaling factors cannot be zero."
            )

        return Vector2D(vector.x / scale_x, vector.y / scale_y)

    return InvertibleFunction(f, f_inv)


# doc-region-begin define rotate
def rotate_90_degrees() -> InvertibleFunction[Vector2D]:
    # fmt: off
    def f(vector: Vector2D) -> Vector2D:
        return Vector2D(-vector.y, vector.x)

    def f_inv(vector: Vector2D) -> Vector2D:
        return Vector2D(vector.y, -vector.x)
    # fmt: on

    return InvertibleFunction(f, f_inv)


def rotate(angle_in_radians: float) -> InvertibleFunction:
    r90: InvertibleFunction[Vector2D] = rotate_90_degrees()

    # fmt: off
    def f(vector: Vector2D) -> Vector2D:
        return math.cos(angle_in_radians) * vector + math.sin(angle_in_radians) * r90(vector)

    def f_inv(vector: Vector2D) -> Vector2D:
        return math.cos(angle_in_radians) * vector + math.sin(angle_in_radians) * inverse(r90)(vector)
    # fmt: on

    return InvertibleFunction(f, f_inv)


# doc-region-end define rotate


# doc-region-begin define rotate around
def rotate_around(
    angle_in_radians: float, center: Vector2D
) -> InvertibleFunction:
    translation_to_origin: InvertibleFunction[Vector2D] = translate(-center)
    rotation: InvertibleFunction[Vector2D] = rotate(angle_in_radians)
    translation_back: InvertibleFunction[Vector2D] = translate(center)

    return compose(translation_back, rotation, translation_to_origin)


# doc-region-end define rotate around
