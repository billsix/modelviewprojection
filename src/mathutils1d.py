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

from dataclasses import dataclass

from mathutils import InvertibleFunction


# doc-region-begin define vector class
@dataclass
class Vector1D:
    x: float
    # doc-region-end define vector class

    # doc-region-begin define add
    def __add__(self, rhs: Vector1D) -> Vector1D:
        return Vector1D(x=(self.x + rhs.x))

    # doc-region-end define add

    # doc-region-begin define subtract
    def __sub__(self, rhs: Vector1D) -> Vector1D:
        return Vector1D(x=(self.x - rhs.x))

    # doc-region-end define subtract

    # doc-region-begin define mul
    def __mul__(self, scalar: float) -> Vector1D:
        return Vector1D(x=(self.x * scalar))

    def __rmul__(self, scalar: float) -> Vector1D:
        return self * scalar

    # doc-region-end define mul

    def __neg__(self) -> Vector1D:
        return -1.0 * self


# doc-region-begin define translate
def translate(translate_amount: Vector1D) -> InvertibleFunction:
    def f(vector: Vector1D) -> Vector1D:
        return vector + translate_amount

    def f_inv(vector: Vector1D) -> Vector1D:
        return vector - translate_amount

    return InvertibleFunction(f, f_inv)


# doc-region-end define translate


# doc-region-begin define uniform scale
def uniform_scale(scalar: float) -> InvertibleFunction:
    if scalar == 0:
        raise ValueError("Scaling factor cannot be zero.")

    def f(vector: Vector1D) -> Vector1D:
        return vector * scalar

    def f_inv(vector: Vector1D) -> Vector1D:
        return vector * (1.0 / scalar)

    return InvertibleFunction(f, f_inv)


# doc-region-end define uniform scale
