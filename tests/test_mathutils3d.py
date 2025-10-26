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

import modelviewprojection.mathutils3d as mu3d
from modelviewprojection.mathutils import InvertibleFunction


def test___add__():
    result = mu3d.Vector3D(x=1.0, y=2.0, z=6.0) + mu3d.Vector3D(
        x=3.0, y=4.0, z=5.0
    )
    assert result.isclose(mu3d.Vector3D(x=4.0, y=6.0, z=11.0))


def test___sub__():
    result = mu3d.Vector3D(x=5.0, y=8.0, z=1.0) - mu3d.Vector3D(
        x=1.0, y=2.0, z=3.0
    )
    assert result.isclose(mu3d.Vector3D(x=4.0, y=6.0, z=-2.0))


def test___mul__():
    result = mu3d.Vector3D(x=2.0, y=3.0, z=4.0) * 4.0
    assert result.isclose(mu3d.Vector3D(x=8.0, y=12.0, z=16.0))


def test___rmul__():
    result = 4.0 * mu3d.Vector3D(x=2.0, y=3.0, z=4.0)
    assert result.isclose(mu3d.Vector3D(x=8.0, y=12.0, z=16.0))


def test___neg__():
    result = -mu3d.Vector3D(x=2.0, y=3.0, z=4.0)
    assert result.isclose(mu3d.Vector3D(x=-2.0, y=-3.0, z=-4.0))


def wrap_vec3_test(
    fn: mu3d.InvertibleFunction, input_val: list[float], output_val: list[float]
):
    out: mu3d.Vector = fn(mu3d.Vector3D(*input_val))
    assert out.isclose(mu3d.Vector3D(*output_val))


# doc-region-begin translate test
def test_translate():
    fn: mu3d.InvertibleFunction = mu3d.translate(
        mu3d.Vector3D(x=2.0, y=3.0, z=4.0)
    )
    fn_inv: mu3d.InvertibleFunction = mu3d.inverse(fn)

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
    fn: mu3d.InvertibleFunction = mu3d.uniform_scale(4.0)
    fn_inv: mu3d.InvertibleFunction = mu3d.inverse(fn)

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
    fn: mu3d.InvertibleFunction = mu3d.scale(m_x=2.0, m_y=3.0, m_z=4.0)
    fn_inv: mu3d.InvertibleFunction = mu3d.inverse(fn)

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
    fn: mu3d.InvertibleFunction = mu3d.rotate_x(math.radians(53.130102))
    fn_inv: mu3d.InvertibleFunction = mu3d.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 5.0, 0.0], [0.0, 3.0, 4.0]],
        [[0.0, 0.0, 5.0], [0.0, -4.0, 3.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_rotate_y():
    fn: mu3d.InvertibleFunction = mu3d.rotate_y(math.radians(53.130102))
    fn_inv: mu3d.InvertibleFunction = mu3d.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 0.0, 5.0], [4.0, 0.0, 3.0]],
        [[5.0, 0.0, 0.0], [3.0, 0.0, -4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_rotate_z():
    fn: mu3d.InvertibleFunction = mu3d.rotate_z(math.radians(53.130102))
    fn_inv: mu3d.InvertibleFunction = mu3d.inverse(fn)

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
    identity: InvertibleFunction = mu3d.uniform_scale(1)

    mu3d.fn_stack.push(identity)
    assert 1 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)

    add_one: InvertibleFunction = mu3d.translate(1)

    mu3d.fn_stack.push(add_one)
    assert 2 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)  # x + 1 = 2

    multiply_by_2: InvertibleFunction = mu3d.uniform_scale(2)

    mu3d.fn_stack.push(multiply_by_2)  # (x * 2) + 1 = 3
    assert 3 == mu3d.fn_stack.modelspace_to_ndc_fn()(1)

    add_5: InvertibleFunction = mu3d.translate(5)

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
    failureCount, testCount = doctest.testmod(mu3d)
    assert 0 == failureCount
