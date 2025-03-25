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


# doc-region-begin define invertible function
class InvertibleFunction:
    def __init__(self, func: Callable, inverse: Callable):
        self.func = func
        self.inverse = inverse

    def __call__(self, x):
        return self.func(x)


def inverse(f: InvertibleFunction) -> InvertibleFunction:
    return InvertibleFunction(f.inverse, f.func)


# doc-region-end define invertible function


def compose(*functions: InvertibleFunction) -> InvertibleFunction:
    def inner(x):
        for f in reversed(functions):
            x = f(x)
        return x

    def f_inv(x):
        for f in functions:
            x = inverse(f)(x)
        return x

    return InvertibleFunction(inner, f_inv)


# doc-region-begin define vertex class
@dataclass
class Vertex2D:
    x: float
    y: float
    # doc-region-end define vertex class

    # doc-region-begin define add
    def __add__(self, rhs: Vertex2D) -> Vertex2D:
        return Vertex2D(x=(self.x + rhs.x), y=(self.y + rhs.y))

    # doc-region-end define add

    # doc-region-begin define subtract
    def __sub__(self, rhs: Vertex2D) -> Vertex2D:
        return Vertex2D(x=(self.x - rhs.x), y=(self.y - rhs.y))

    # doc-region-end define subtract

    # doc-region-begin define mul
    def __mul__(self, scalar: float) -> Vertex2D:
        return Vertex2D(x=(self.x * scalar), y=(self.y * scalar))

    def __rmul__(self, scalar: float) -> Vertex2D:
        return self * scalar

    # doc-region-end define mul

    def __neg__(self) -> Vertex2D:
        return -1.0 * self


# doc-region-begin define translate
def translate(translate_amount: Vertex2D) -> InvertibleFunction:
    def f(vertex: Vertex2D) -> Vertex2D:
        return vertex + translate_amount

    def f_inv(vertex: Vertex2D) -> Vertex2D:
        return vertex - translate_amount

    return InvertibleFunction(f, f_inv)


# doc-region-end define translate


# doc-region-begin define uniform scale
def uniform_scale(scalar: float) -> InvertibleFunction:
    if scalar == 0:
        raise ValueError("Scaling factor cannot be zero.")

    def f(vertex: Vertex2D) -> Vertex2D:
        return vertex * scalar

    def f_inv(vertex: Vertex2D) -> Vertex2D:
        return vertex * (1.0 / scalar)

    return InvertibleFunction(f, f_inv)


# doc-region-end define uniform scale


def scale(scale_x: float, scale_y: float) -> InvertibleFunction:
    """Returns an invertible scaling function."""
    if scale_x == 0 or scale_y == 0:
        raise ValueError("Scaling factors cannot be zero.")

    def f(vertex: Vertex2D) -> Vertex2D:
        return Vertex2D(vertex.x * scale_x, vertex.y * scale_y)

    def f_inv(vertex: Vertex2D) -> Vertex2D:
        return Vertex2D(vertex.x / scale_x, vertex.y / scale_y)

    return InvertibleFunction(f, f_inv)


# doc-region-begin define rotate
def rotate_90_degrees() -> Callable[Vertex2D, Vertex2D]:
    """90-degree counterclockwise rotation (not a full invertible function)."""

    # fmt: off
    def f(vertex: Vertex2D) -> Vertex2D:
        return Vertex2D(-vertex.y, vertex.x)

    def f_inv(vertex: Vertex2D) -> Vertex2D:
        return Vertex2D(vertex.y, -vertex.x)
    # fmt: on

    return InvertibleFunction(f, f_inv)


def rotate(angle_in_radians: float) -> InvertibleFunction:
    """Returns an invertible rotation function."""

    r90: Callable[Vertex2D, Vertex2D] = rotate_90_degrees()

    # fmt: off
    def f(vertex: Vertex2D) -> Vertex2D:
        return math.cos(angle_in_radians) * vertex + math.sin(angle_in_radians) * r90(vertex)

    def f_inv(vertex: Vertex2D) -> Vertex2D:
        return math.cos(angle_in_radians) * vertex + math.sin(angle_in_radians) * inverse(r90)(vertex)
    # fmt: on

    return InvertibleFunction(f, f_inv)


# doc-region-end define rotate


def rotate_around(angle_in_radians: float, center: Vertex2D) -> InvertibleFunction:
    """Returns an invertible rotation function around a given center."""
    translation_to_origin: Callable[Vertex2D, Vertex2D] = translate(-center)
    rotation: Callable[Vertex2D, Vertex2D] = rotate(angle_in_radians)
    translation_back: Callable[Vertex2D, Vertex2D] = translate(center)

    return compose(translation_back, rotation, translation_to_origin)
