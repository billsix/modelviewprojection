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


def compose(*functions):
    def inner(arg):
        for f in reversed(functions):
            arg = f(arg)
        return arg

    return inner


@dataclass
class Vertex2D:
    x: float
    y: float

    def __add__(self, rhs: Vertex2D) -> Vertex2D:
        return Vertex2D(x=(self.x + rhs.x), y=(self.y + rhs.y))

    def __mul__(self, scalar: float) -> Vertex2D:
        return Vertex2D(x=(self.x * scalar), y=(self.y * scalar))

    def __rmul__(self, scalar: float) -> Vertex2D:
        return self * scalar

    def __neg__(self) -> Vertex2D:
        return -1.0 * self


def translate(translate_amount: Vertex2D) -> Callable[Vertex2D, Vertex2D]:
    def inner(vertex: Vertex2D) -> Vertex2D:
        return vertex + translate_amount

    return inner


def uniform_scale(scalar: float) -> Callable[Vertex2D, Vertex2D]:
    def inner(vertex: Vertex2D) -> Vertex2D:
        return vertex * scalar

    return inner


def scale(scale_x: float, scale_y: float) -> Callable[Vertex2D, Vertex2D]:
    def inner(vertex: Vertex2D) -> Vertex2D:
        return Vertex2D(x=(vertex.x * scale_x), y=(vertex.y * scale_y))

    return inner


def rotate_90_degrees(vertex: Vertex2D) -> Vertex2D:
    return Vertex2D(x=-vertex.y, y=vertex.x)


def rotate(angle_in_radians: float) -> Callable[Vertex2D, Vertex2D]:
    a = angle_in_radians

    def inner(vertex: Vertex2D) -> Vertex2D:
        return math.cos(a) * vertex + math.sin(a) * rotate_90_degrees(vertex)

    return inner


def rotate_around(
    angle_in_radians: float, center: Vertex2D
) -> Callable[Vertex2D, Vertex2D]:
    def inner(vertex: Vertex2D) -> Vertex2D:
        return compose(
            translate(center), rotate(angle_in_radians), translate(-center)
        )

    return inner
