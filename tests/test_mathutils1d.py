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

from pytest import approx

from mathutils import InvertibleFunction, compose, inverse
from mathutils1d import Vector1D, translate, uniform_scale


def test___add__():
    result = Vector1D(x=1.0) + Vector1D(x=3.0)
    assert result == Vector1D(x=approx(4.0))


def test___sub__():
    result = Vector1D(x=5.0) - Vector1D(x=1.0)
    assert result == Vector1D(x=approx(4.0))


def test___mul__():
    result = Vector1D(x=2.0) * 4.0
    assert result == Vector1D(x=approx(8.0))


def test___rmul__():
    result = 4.0 * Vector1D(x=2.0)
    assert result == Vector1D(x=approx(8.0))


def test___neg__():
    result = -Vector1D(x=2.0)
    assert result == Vector1D(x=approx(-2.0))


# doc-region-begin translate test
def test_translate():
    fn: InvertibleFunction[Vector1D] = translate(2.0)
    fn_inv: InvertibleFunction[Vector1D] = inverse(fn)

    input_output_pairs = [
        [-3.0, -1.0],
        [-2.0, 0.0],
        [-1.0, 1.0],
        [0.0, 2.0],
        [1.0, 3.0],
        [2.0, 4.0],
        [3.0, 5.0],
        [4.0, 6.0],
    ]
    for input_val, output_val in input_output_pairs:
        assert fn(Vector1D(input_val)) == Vector1D(approx(output_val))
        assert fn_inv(Vector1D(output_val)) == Vector1D(approx(input_val))


# doc-region-end translate test


def test_mx_plus_b():
    m = 5.0
    b = 2.0

    fn: InvertibleFunction[Vector1D] = compose(translate(b), uniform_scale(m))
    fn_inv: InvertibleFunction[Vector1D] = inverse(fn)

    input_output_pairs = [
        [-3.0, -13.0],
        [-2.0, -8.0],
        [-1.0, -3.0],
        [0.0, 2.0],
        [1.0, 7.0],
        [2.0, 12.0],
        [3.0, 17.0],
        [4.0, 22.0],
    ]
    for input_val, output_val in input_output_pairs:
        assert fn(Vector1D(input_val)) == Vector1D(approx(output_val))
        assert fn_inv(Vector1D(output_val)) == Vector1D(approx(input_val))


def test_uniform_scale():
    fn: InvertibleFunction[Vector1D] = uniform_scale(4.0)
    fn_inv: InvertibleFunction[Vector1D] = inverse(fn)

    input_output_pairs = [
        [-3.0, -12.0],
        [-2.0, -8.0],
        [-1.0, -4.0],
        [0.0, 0.0],
        [1.0, 4.0],
        [2.0, 8.0],
        [3.0, 12.0],
        [4.0, 16.0],
    ]
    for input_val, output_val in input_output_pairs:
        assert fn(Vector1D(input_val)) == Vector1D(approx(output_val))
        assert fn_inv(Vector1D(output_val)) == Vector1D(approx(input_val))
