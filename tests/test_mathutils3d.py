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
import doctest
import math

from pytest import approx

import modelviewprojection
import modelviewprojection.mathutils as mu
import modelviewprojection.mathutils3d as mu3d


def test___add__():
    result = mu3d.Vector3D(x=1.0, y=2.0, z=6.0) + mu3d.Vector3D(
        x=3.0, y=4.0, z=5.0
    )
    assert result == mu3d.Vector3D(x=approx(4.0), y=approx(6.0), z=approx(11.0))


def test___sub__():
    result = mu3d.Vector3D(x=5.0, y=8.0, z=1.0) - mu3d.Vector3D(
        x=1.0, y=2.0, z=3.0
    )
    assert result == mu3d.Vector3D(x=approx(4.0), y=approx(6.0), z=approx(-2.0))


def test___mul__():
    result = mu3d.Vector3D(x=2.0, y=3.0, z=4.0) * 4.0
    assert result == mu3d.Vector3D(
        x=approx(8.0), y=approx(12.0), z=approx(16.0)
    )


def test___rmul__():
    result = 4.0 * mu3d.Vector3D(x=2.0, y=3.0, z=4.0)
    assert result == mu3d.Vector3D(
        x=approx(8.0), y=approx(12.0), z=approx(16.0)
    )


def test___neg__():
    result = -mu3d.Vector3D(x=2.0, y=3.0, z=4.0)
    assert result == mu3d.Vector3D(
        x=approx(-2.0), y=approx(-3.0), z=approx(-4.0)
    )


def wrap_vec3_test(fn, input_val, output_val):
    print(mu3d.Vector3D(*input_val))
    out = fn(mu3d.Vector3D(*input_val))
    print(out)
    assert out.x == approx(output_val[0], abs=0.001)
    assert out.y == approx(output_val[1], abs=0.001)
    assert out.z == approx(output_val[2], abs=0.001)


# doc-region-begin translate test
def test_translate():
    fn: mu.InvertibleFunction = mu.translate(mu3d.Vector3D(x=2.0, y=3.0, z=4.0))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [2.0, 3.0, 4.0]],
        [[1.0, 0.0, 0.0], [3.0, 3.0, 4.0]],
        [[0.0, 1.0, 0.0], [2.0, 4.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


# doc-region-end translate test


def test_uniform_scale():
    fn: mu.InvertibleFunction = mu.uniform_scale(4.0)
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[1.0, 0.0, 0.0], [4.0, 0.0, 0.0]],
        [[0.0, 1.0, 0.0], [0.0, 4.0, 0.0]],
        [[0.0, 0.0, 1.0], [0.0, 0.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_scale():
    fn: mu.InvertibleFunction = mu3d.scale(m_x=2.0, m_y=3.0, m_z=4.0)
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
        [[0.0, 1.0, 0.0], [0.0, 3.0, 0.0]],
        [[0.0, 0.0, 1.0], [0.0, 0.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_rotate_x():
    fn: mu.InvertibleFunction = mu3d.rotate_x(math.radians(53.130102))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 5.0, 0.0], [0.0, 3.0, 4.0]],
        [[0.0, 0.0, 5.0], [0.0, -4.0, 3.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_rotate_y():
    fn: mu.InvertibleFunction = mu3d.rotate_y(math.radians(53.130102))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 0.0, 5.0], [4.0, 0.0, 3.0]],
        [[5.0, 0.0, 0.0], [3.0, 0.0, -4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_rotate_z():
    fn: mu.InvertibleFunction = mu3d.rotate_z(math.radians(53.130102))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[5.0, 0.0, 0.0], [3.0, 4.0, 0.0]],
        [[0.0, 5.0, 0.0], [-4.0, 3.0, 0.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


# doc-region-begin function stack examples definitions
def test_fn_stack():
    def identity(x):
        return x

    mu3d.fn_stack.push(identity)
    assert 1 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)

    def add_one(x):
        return x + 1

    mu3d.fn_stack.push(add_one)
    assert 2 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)  # x + 1 = 2

    def multiply_by_2(x):
        return x * 2

    mu3d.fn_stack.push(multiply_by_2)  # (x * 2) + 1 = 3
    assert 3 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)

    def add_5(x):
        return x + 5

    mu3d.fn_stack.push(add_5)  # ((x + 5) * 2) + 1 = 13
    assert 13 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)

    mu3d.fn_stack.pop()
    assert 3 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)  # (x * 2) + 1 = 3

    mu3d.fn_stack.pop()
    assert 2 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)  # x + 1 = 2

    mu3d.fn_stack.pop()
    assert 1 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)  # x = 1
    # doc-region-end function stack examples definitions


def test_doctest():
    failureCount, testCount = doctest.testmod(modelviewprojection.mathutils3d)
    assert 0 == failureCount
