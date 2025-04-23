# Copyright (c) 2018-2025 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


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
