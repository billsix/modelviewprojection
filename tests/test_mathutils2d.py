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
import modelviewprojection.mathutils2d as mu2d


def wrap_vec2_test(fn, input_val, output_val):
    out = fn(mu2d.Vector2D(*input_val))
    assert out.x == approx(output_val[0], abs=0.001)
    assert out.y == approx(output_val[1], abs=0.001)


def test___add__():
    input_output_pairs = [
        [[(0.0, 0.0), (0.0, 0.0)], (approx(0.0), approx(0.0))],
        [[(1.0, 0.0), (0.0, 1.0)], (approx(1.0), approx(1.0))],
        [[(1.0, 2.0), (3.0, 4.0)], (approx(4.0), approx(6.0))],
        [[(0.0, 2.0), (3.0, 0.0)], (approx(3.0), approx(2.0))],
    ]

    for input_val, output_val in input_output_pairs:
        assert mu2d.Vector2D(*output_val) == mu2d.Vector2D(
            *input_val[0]
        ) + mu2d.Vector2D(*input_val[1])


def test___sub__():
    input_output_pairs = [
        [[(0.0, 0.0), (0.0, 0.0)], (approx(0.0), approx(0.0))],
        [[(1.0, 0.0), (0.0, 1.0)], (approx(1.0), approx(-1.0))],
        [[(5.0, 8.0), (1.0, 2.0)], (approx(4.0), approx(6.0))],
    ]

    for input_val, output_val in input_output_pairs:
        assert mu2d.Vector2D(*output_val) == mu2d.Vector2D(
            *input_val[0]
        ) - mu2d.Vector2D(*input_val[1])


def test___mul__():
    input_output_pairs = [
        [[(0.0, 0.0), 2], (approx(0.0), approx(0.0))],
        [[(1.0, 0.0), 2], (approx(2.0), approx(0.0))],
        [[(0.0, 1.0), 2], (approx(0.0), approx(2.0))],
        [[(1.0, 1.0), 2], (approx(2.0), approx(2.0))],
    ]

    for input_val, output_val in input_output_pairs:
        assert mu2d.Vector2D(*output_val) == input_val[1] * mu2d.Vector2D(
            *input_val[0]
        )


def test___rmul__():
    input_output_pairs = [
        [[(0.0, 0.0), 2], (approx(0.0), approx(0.0))],
        [[(1.0, 0.0), 2], (approx(2.0), approx(0.0))],
        [[(0.0, 1.0), 2], (approx(0.0), approx(2.0))],
        [[(1.0, 1.0), 2], (approx(2.0), approx(2.0))],
    ]

    for input_val, output_val in input_output_pairs:
        assert (
            mu2d.Vector2D(*output_val)
            == mu2d.Vector2D(*input_val[0]) * input_val[1]
        )


def test___neg__():
    input_output_pairs = [
        [(0.0, 0.0), (0.0, 0.0)],
        [(1.0, 0.0), (-1.0, 0.0)],
        [(0.0, 1.0), (0.0, -1.0)],
        [(1.0, 1.0), (-1.0, -1.0)],
    ]

    for input_val, output_val in input_output_pairs:
        assert mu2d.Vector2D(*output_val) == -mu2d.Vector2D(*input_val)


def test___abs__():
    input_output_pairs = [
        [(3.0, 4.0), 5.0],
        [(-3.0, 4.0), 5.0],
        [(3.0, -4.0), 5.0],
        [(-3.0, -4.0), 5.0],
    ]

    for input_val, output_val in input_output_pairs:
        assert output_val == abs(mu2d.Vector2D(*input_val))


def test___dot__():
    input_output_pairs = [
        [[(1.0, 0.0), (0.0, 1.0)], 0.0],
        [[(1.0, 0.0), (1.0, 0.0)], 1.0],
        [[(0.0, 1.0), (0.0, 1.0)], 1.0],
        [[(3.0, 0.0), (1.0, 0.0)], 3.0],
        [[(0.0, 1.0), (0.0, 4.0)], 4.0],
    ]

    for input_val, output_val in input_output_pairs:
        assert approx(output_val) == mu2d.Vector2D(*input_val[0]).dot(
            mu2d.Vector2D(*input_val[1])
        )


def test_is_parallel():
    input_output_pairs = [
        [[(1.0, 0.0), (2.0, 0.0)], True],
        [[(0.0, 5.0), (0.0, 1.0)], True],
        [[(1.0, 5.0), (0.0, 1.0)], False],
        [[(0.0, 5.0), (0.2, 1.0)], False],
        [[(0.0, 5.0), (1.2, 0.0)], False],
    ]

    for input_val, output_val in input_output_pairs:
        assert output_val == mu2d.is_parallel(
            mu2d.Vector2D(*input_val[0]), mu2d.Vector2D(*input_val[1])
        )


def test_is_counter_clockwise():
    input_output_pairs = [
        [[(1.0, 0.0), (0.0, 1.0)], True],
        [[(1.0, 0.0), (0.0, -0.1)], False],
        [[(0.0, 1.0), (-0.1, 1.0)], True],
        [[(0.0, 1.0), (10.1, 1.0)], False],
        [[(-1.0, 0.0), (-1.0, 0.1)], False],
        [[(-1.0, 0.0), (-1.0, -0.1)], True],
        [[(0.0, -1.0), (-0.1, -1.0)], False],
        [[(0.0, -1.0), (0.1, -1.0)], True],
    ]

    for input_val, output_val in input_output_pairs:
        assert output_val == mu2d.is_counter_clockwise(
            mu2d.Vector2D(*input_val[0]), mu2d.Vector2D(*input_val[1])
        )


# doc-region-begin translate test
def test_translate():
    fn: mu2d.InvertibleFunction = mu2d.translate(mu2d.Vector2D(x=2.0, y=3.0))
    fn_inv: mu2d.InvertibleFunction = mu2d.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [2.0, 3.0]],
        [[1.0, 0.0], [3.0, 3.0]],
        [[0.0, 1.0], [2.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


# doc-region-end translate test


def test_compose():
    fn: mu2d.InvertibleFunction = mu2d.translate(mu2d.Vector2D(x=2.0, y=3.0))
    fn_inv: mu2d.InvertibleFunction = mu2d.inverse(fn)

    identity_fn: mu2d.InvertibleFunction = mu2d.compose([fn_inv, fn])

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.0], [1.0, 0.0]],
        [[0.0, 1.0], [0.0, 1.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(identity_fn, input_val, output_val)


def test_uniform_scale():
    fn: mu2d.InvertibleFunction = mu2d.uniform_scale(4.0)
    fn_inv: mu2d.InvertibleFunction = mu2d.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.0], [4.0, 0.0]],
        [[0.0, 1.0], [0.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_scale():
    fn: mu2d.InvertibleFunction = mu2d.scale(m_x=2.0, m_y=3.0)
    fn_inv: mu2d.InvertibleFunction = mu2d.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.0], [2.0, 0.0]],
        [[0.0, 1.0], [0.0, 3.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_rotate_90():
    fn: mu2d.InvertibleFunction = mu2d.rotate_90_degrees()
    fn_inv: mu2d.InvertibleFunction = mu2d.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.0], [0.0, 1.0]],
        [[0.0, 1.0], [-1.0, 0.0]],
        [[-1.0, 0.0], [0.0, -1.0]],
        [[0.0, -1.0], [1.0, 0.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_rotate():
    fn: mu2d.InvertibleFunction = mu2d.rotate(math.radians(53.130102))
    fn_inv: mu2d.InvertibleFunction = mu2d.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[5.0, 0.0], [3.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_doctest():
    failureCount, testCount = doctest.testmod(modelviewprojection.mathutils2d)
    assert 0 == failureCount
