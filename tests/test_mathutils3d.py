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

from modelviewprojection.mathutils import InvertibleFunction
from modelviewprojection.mathutils3d import (
    Vector3D,
    fn_stack,
    inverse,
    rotate_x,
    rotate_y,
    rotate_z,
    scale,
    translate,
    uniform_scale,
)


def test___add__():
    result = Vector3D(x=1.0, y=2.0, z=6.0) + Vector3D(x=3.0, y=4.0, z=5.0)
    assert result == Vector3D(x=approx(4.0), y=approx(6.0), z=approx(11.0))


def test___sub__():
    result = Vector3D(x=5.0, y=8.0, z=1.0) - Vector3D(x=1.0, y=2.0, z=3.0)
    assert result == Vector3D(x=approx(4.0), y=approx(6.0), z=approx(-2.0))


def test___mul__():
    result = Vector3D(x=2.0, y=3.0, z=4.0) * 4.0
    assert result == Vector3D(x=approx(8.0), y=approx(12.0), z=approx(16.0))


def test___rmul__():
    result = 4.0 * Vector3D(x=2.0, y=3.0, z=4.0)
    assert result == Vector3D(x=approx(8.0), y=approx(12.0), z=approx(16.0))


def test___neg__():
    result = -Vector3D(x=2.0, y=3.0, z=4.0)
    assert result == Vector3D(x=approx(-2.0), y=approx(-3.0), z=approx(-4.0))


def wrap_vec3_test(fn, input_val, output_val):
    return fn(Vector3D(*input_val)) == Vector3D(*(map(approx, output_val)))


# doc-region-begin translate test
def test_translate():
    fn: InvertibleFunction[Vector3D] = translate(Vector3D(x=2.0, y=3.0, z=4.0))
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [2.0, 3.0, 4.0]],
        [[1.0, 0.0, 0.0], [3.0, 3.0, 4.0]],
        [[0.0, 1.0, 0.0], [2.0, 4.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, input_val, output_val)


# doc-region-end translate test


def test_uniform_scale():
    fn: InvertibleFunction[Vector3D] = uniform_scale(4.0)
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[1.0, 0.0, 0.0], [4.0, 0.0, 0.0]],
        [[0.0, 1.0, 0.0], [0.0, 4.0, 0.0]],
        [[0.0, 0.0, 1.0], [0.0, 0.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, input_val, output_val)


def test_scale():
    fn: InvertibleFunction[Vector3D] = scale(
        scale_x=2.0, scale_y=3.0, scale_z=4.0
    )
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
        [[0.0, 1.0, 0.0], [0.0, 3.0, 0.0]],
        [[0.0, 0.0, 1.0], [0.0, 0.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, input_val, output_val)


def test_rotate_x():
    fn: InvertibleFunction[Vector3D] = rotate_x(math.radians(53.130102))
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 5.0, 0.0], [0.0, 3.0, 4.0]],
        [[0.0, 0.0, 5.0], [0.0, -4.0, 3.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, input_val, output_val)


def test_rotate_y():
    fn: InvertibleFunction[Vector3D] = rotate_y(math.radians(53.130102))
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 0.0, 5.0], [4.0, 0.0, 3.0]],
        [[5.0, 0.0, 0.0], [3.0, 0.0, -4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, input_val, output_val)


def test_rotate_z():
    fn: InvertibleFunction[Vector3D] = rotate_z(math.radians(53.130102))
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[5.0, 0.0, 0.0], [3.0, 4.0, 0.0]],
        [[0.0, 5.0, 0.0], [-4.0, 3.0, 0.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, input_val, output_val)


# doc-region-begin function stack examples definitions
def test_fn_stack():
    def identity(x):
        return x

    fn_stack.push(identity)
    assert 1 == fn_stack.modelspace_to_ndc_fn()(1)

    def add_one(x):
        return x + 1

    fn_stack.push(add_one)
    assert 2 == fn_stack.modelspace_to_ndc_fn()(1)  # x + 1 = 2

    def multiply_by_2(x):
        return x * 2

    fn_stack.push(multiply_by_2)  # (x * 2) + 1 = 3
    assert 3 == fn_stack.modelspace_to_ndc_fn()(1)

    def add_5(x):
        return x + 5

    fn_stack.push(add_5)  # ((x + 5) * 2) + 1 = 13
    assert 13 == fn_stack.modelspace_to_ndc_fn()(1)

    fn_stack.pop()
    assert 3 == fn_stack.modelspace_to_ndc_fn()(1)  # (x * 2) + 1 = 3

    fn_stack.pop()
    assert 2 == fn_stack.modelspace_to_ndc_fn()(1)  # x + 1 = 2

    fn_stack.pop()
    assert 1 == fn_stack.modelspace_to_ndc_fn()(1)  # x = 1
    # doc-region-end function stack examples definitions
