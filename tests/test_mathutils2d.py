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

from pytest import approx

from mathutils import InvertibleFunction
from mathutils2d import (
    Vector2D,
    compose,
    inverse,
    rotate,
    rotate_90_degrees,
    scale,
    translate,
    uniform_scale,
)


def test___add__():
    result = Vector2D(x=1.0, y=2.0) + Vector2D(x=3.0, y=4.0)
    assert result == Vector2D(x=approx(4.0), y=approx(6.0))


def test___sub__():
    result = Vector2D(x=5.0, y=8.0) - Vector2D(x=1.0, y=2.0)
    assert result == Vector2D(x=approx(4.0), y=approx(6.0))


def test___mul__():
    result = Vector2D(x=2.0, y=3.0) * 4.0
    assert result == Vector2D(x=approx(8.0), y=approx(12.0))


def test___rmul__():
    result = 4.0 * Vector2D(x=2.0, y=3.0)
    assert result == Vector2D(x=approx(8.0), y=approx(12.0))


def test___neg__():
    result = -Vector2D(x=2.0, y=3.0)
    assert result == Vector2D(x=approx(-2.0), y=approx(-3.0))


def wrap_vec2_test(fn, input_val, output_val):
    return fn(Vector2D(*input_val)) == Vector2D(*(map(approx, output_val)))


# doc-region-begin translate test
def test_translate():
    fn: InvertibleFunction[Vector2D] = translate(Vector2D(x=2.0, y=3.0))
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [2.0, 3.0]],
        [[1.0, 0.0], [3.0, 3.0]],
        [[0.0, 1.0], [2.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, input_val, output_val)


# doc-region-end translate test


def test_compose():
    fn: InvertibleFunction[Vector2D] = translate(Vector2D(x=2.0, y=3.0))
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    identity_fn: InvertibleFunction[Vector2D] = compose(fn_inv, fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.0], [1.0, 0.0]],
        [[0.0, 1.0], [0.0, 1.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(identity_fn, input_val, output_val)


def test_uniform_scale():
    fn: InvertibleFunction[Vector2D] = uniform_scale(4.0)
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.0], [4.0, 0.0]],
        [[0.0, 1.0], [0.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, input_val, output_val)


def test_scale():
    fn: InvertibleFunction[Vector2D] = scale(scale_x=2.0, scale_y=3.0)
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.0], [2.0, 0.0]],
        [[0.0, 1.0], [0.0, 3.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, input_val, output_val)


def test_rotate_90():
    fn: InvertibleFunction[Vector2D] = rotate_90_degrees()
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.0], [0.0, 1.0]],
        [[0.0, 1.0], [-1.0, 0.0]],
        [[-1.0, 0.0], [0.0, -1.0]],
        [[0.0, -1.0], [1.0, 0.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, input_val, output_val)


def test_rotate():
    fn: InvertibleFunction[Vector2D] = rotate(math.radians(53.130102))
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[5.0, 0.0], [3.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, input_val, output_val)
