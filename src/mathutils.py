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
from typing import Callable


class InvertibleFunction:
    def __init__(self, func: Callable, inverse: Callable):
        self.func = func
        self.inverse = inverse

    def __call__(self, x):
        return self.func(x)

    def invert(self):
        return InvertibleFunction(self.inverse, self.func)


def inverse(f: InvertibleFunction) -> InvertibleFunction:
    return f.invert()


def compose(*functions: InvertibleFunction) -> InvertibleFunction:
    def inner(x):
        for f in reversed(functions):
            x = f(x)
        return x

    def inverse_inner(x):
        for f in functions:
            x = inverse(f)(x)
        return x

    return InvertibleFunction(inner, inverse_inner)


@dataclass
class Vertex2D:
    x: float
    y: float

    def __add__(self, rhs: Vertex2D) -> Vertex2D:
        return Vertex2D(x=(self.x + rhs.x), y=(self.y + rhs.y))

    def __sub__(self, rhs: Vertex2D) -> Vertex2D:
        return Vertex2D(x=(self.x - rhs.x), y=(self.y - rhs.y))

    def __mul__(self, scalar: float) -> Vertex2D:
        return Vertex2D(x=(self.x * scalar), y=(self.y * scalar))

    def __rmul__(self, scalar: float) -> Vertex2D:
        return self * scalar

    def __neg__(self) -> Vertex2D:
        return -1.0 * self


def translate(translate_amount: Vertex2D) -> InvertibleFunction:
    def forward(vertex: Vertex2D) -> Vertex2D:
        return vertex + translate_amount

    def inverse(vertex: Vertex2D) -> Vertex2D:
        return vertex - translate_amount

    return InvertibleFunction(forward, inverse)


def uniform_scale(scalar: float) -> InvertibleFunction:
    if scalar == 0:
        raise ValueError("Scaling factor cannot be zero.")

    def forward(vertex: Vertex2D) -> Vertex2D:
        return vertex * scalar

    def inverse(vertex: Vertex2D) -> Vertex2D:
        return vertex / scalar

    return InvertibleFunction(forward, inverse)


def scale(scale_x: float, scale_y: float) -> InvertibleFunction:
    """Returns an invertible scaling function."""
    if scale_x == 0 or scale_y == 0:
        raise ValueError("Scaling factors cannot be zero.")

    def forward(vertex: Vertex2D) -> Vertex2D:
        return Vertex2D(vertex.x * scale_x, vertex.y * scale_y)

    def inverse(vertex: Vertex2D) -> Vertex2D:
        return Vertex2D(vertex.x / scale_x, vertex.y / scale_y)

    return InvertibleFunction(forward, inverse)


def rotate_90_degrees(vertex: Vertex2D) -> Vertex2D:
    """90-degree counterclockwise rotation (not a full invertible function)."""
    return Vertex2D(-vertex.y, vertex.x)


def rotate(angle_in_radians: float) -> InvertibleFunction:
    """Returns an invertible rotation function."""
    cos_a = math.cos(angle_in_radians)
    sin_a = math.sin(angle_in_radians)

    def forward(vertex: Vertex2D) -> Vertex2D:
        return Vertex2D(
            cos_a * vertex.x - sin_a * vertex.y,
            sin_a * vertex.x + cos_a * vertex.y,
        )

    def inverse(vertex: Vertex2D) -> Vertex2D:
        return Vertex2D(
            cos_a * vertex.x + sin_a * vertex.y,
            -sin_a * vertex.x + cos_a * vertex.y,
        )

    return InvertibleFunction(forward, inverse)


def rotate_around(angle_in_radians: float, center: Vertex2D) -> InvertibleFunction:
    """Returns an invertible rotation function around a given center."""
    translation_to_origin = translate(-center)
    rotation = rotate(angle_in_radians)
    translation_back = translate(center)

    return compose(translation_back, rotation, translation_to_origin)
