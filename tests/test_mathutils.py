# Copyright (c) 2018-2026 William Emerison Six
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

import doctest
import math

import modelviewprojection.mathutils as mu
from modelviewprojection.mathutils import (
    InvertibleFunction,
    Vector,
    Vector1D,
    Vector2D,
    Vector3D,
    compose,
    fn_stack,
    inverse,
    is_counter_clockwise,
    is_parallel,
    rotate,
    rotate_90_degrees,
    rotate_x,
    rotate_y,
    rotate_z,
    scale_non_uniform_2d,
    scale_non_uniform_3d,
    translate,
    uniform_scale,
)


# doc-region-begin test add
def test__vec1__add__():
    e_1: Vector1D = Vector1D.e_1()

    result: Vector = 1 * e_1 + 3 * e_1
    assert result.isclose(4 * e_1)
    # doc-region-end test add


# doc-region-begin test substract
def test__vec1__sub__():
    e_1: Vector1D = Vector1D.e_1()

    result: Vector = 5 * e_1 - (1 * e_1)
    assert result.isclose(4 * e_1)
    # doc-region-end test substract


def test__vec1__mul__():
    e_1: Vector1D = Vector1D.e_1()
    result = (2 * e_1) * 4
    assert result.isclose(8 * e_1)


def test__vec1__rmul__():
    e_1: Vector1D = Vector1D.e_1()
    result = 4 * (2 * e_1)
    assert result.isclose(8 * e_1)


def test__vec1__neg__():
    e_1: Vector1D = Vector1D.e_1()
    result = -(2 * e_1)
    assert result.isclose(-2 * e_1)


def wrap_vec1_test(
    fn: InvertibleFunction[Vector1D], input_val: Vector1D, output_val: Vector1D
):
    out: Vector = fn(input_val)
    assert out.isclose(output_val)


# doc-region-begin translate test
def test__vec1_translate():
    e_1: Vector1D = Vector1D.e_1()

    fn: InvertibleFunction[Vector1D] = translate(2 * e_1)
    fn_inv: InvertibleFunction[Vector1D] = inverse(fn)

    input_output_pairs: list[tuple[Vector1D, Vector1D]] = [
        [(-3 * e_1), (-1 * e_1)],
        [(-2 * e_1), (0 * e_1)],
        [(-1 * e_1), (1 * e_1)],
        [(0 * e_1), (2 * e_1)],
        [(1 * e_1), (3 * e_1)],
        [(2 * e_1), (4 * e_1)],
        [(3 * e_1), (5 * e_1)],
        [(4 * e_1), (6 * e_1)],
    ]
    for input_val, output_val in input_output_pairs:
        wrap_vec1_test(fn, input_val, output_val)
        wrap_vec1_test(fn_inv, output_val, input_val)


# doc-region-end translate test


def test__vec1_mx_plus_b():
    e_1: Vector1D = Vector1D.e_1()

    m: int = 5
    b: int = 2

    fn: InvertibleFunction[Vector1D] = compose(
        [translate(b * e_1), uniform_scale(m)]
    )
    fn_inv: InvertibleFunction[Vector1D] = inverse(fn)

    input_output_pairs: list[tuple[Vector1D, Vector1D]] = [
        [(-3 * e_1), (-13 * e_1)],
        [(-2 * e_1), (-8 * e_1)],
        [(-1 * e_1), (-3 * e_1)],
        [(-0 * e_1), (2 * e_1)],
        [(1 * e_1), (7 * e_1)],
        [(2 * e_1), (12 * e_1)],
        [(3 * e_1), (17 * e_1)],
        [(4 * e_1), (22 * e_1)],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec1_test(fn, input_val, output_val)
        wrap_vec1_test(fn_inv, output_val, input_val)


def test_vec1_uniform_scale():
    e_1: Vector1D = Vector1D.e_1()

    fn: InvertibleFunction[Vector1D] = uniform_scale(4)
    fn_inv: InvertibleFunction[Vector1D] = inverse(fn)

    input_output_pairs: list[tuple[Vector1D, Vector1D]] = [
        [(-3 * e_1), (-12 * e_1)],
        [(-2 * e_1), (-8 * e_1)],
        [(-1 * e_1), (-4 * e_1)],
        [(0 * e_1), (0 * e_1)],
        [(1 * e_1), (4 * e_1)],
        [(2 * e_1), (8 * e_1)],
        [(3 * e_1), (12 * e_1)],
        [(4 * e_1), (16 * e_1)],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec1_test(fn, input_val, output_val)
        wrap_vec1_test(fn_inv, output_val, input_val)


def test_vec1_tempature_conversion():
    e_1: Vector1D = Vector1D.e_1()

    def test_vec1_vector1d_function(
        fn: InvertibleFunction[Vector1D],
        input_output_pairs: list[list[float]],
    ):
        for input_val, output_val in input_output_pairs:
            assert fn(input_val * e_1).isclose(output_val * e_1)
            assert inverse(fn)(output_val * e_1).isclose(input_val * e_1)

    # doc-region-begin temperature functions
    celsius_to_kelvin: InvertibleFunction[Vector1D] = translate(273.15 * e_1)
    fahrenheit_to_celsius: InvertibleFunction[Vector1D] = compose(
        [uniform_scale(5.0 / 9.0), translate(-32.0 * e_1)]
    )
    fahrenheit_to_kelvin: InvertibleFunction[Vector1D] = compose(
        [celsius_to_kelvin, fahrenheit_to_celsius]
    )
    kelvin_to_celsius: InvertibleFunction[Vector1D] = inverse(celsius_to_kelvin)
    celsius_to_fahrenheit: InvertibleFunction[Vector1D] = inverse(
        fahrenheit_to_celsius
    )
    kelvin_to_fahrenheit: InvertibleFunction[Vector1D] = compose(
        [celsius_to_fahrenheit, kelvin_to_celsius]
    )

    # doc-region-end temperature functions

    test_vec1_vector1d_function(
        celsius_to_kelvin,
        [
            [0.0, 273.15],
            [100.0, 373.15],
        ],
    )
    test_vec1_vector1d_function(
        fahrenheit_to_celsius,
        [
            [32.0, 0.0],
            [212.0, 100.0],
        ],
    )
    test_vec1_vector1d_function(
        fahrenheit_to_kelvin,
        [
            [32.0, 273.15],
            [212.0, 373.15],
        ],
    )
    test_vec1_vector1d_function(
        kelvin_to_celsius,
        [
            [273.15, 0.0],
            [373.15, 100.0],
        ],
    )
    test_vec1_vector1d_function(
        celsius_to_fahrenheit,
        [
            [0.0, 32.0],
            [100.0, 212.0],
        ],
    )
    test_vec1_vector1d_function(
        kelvin_to_fahrenheit,
        [
            [273.15, 32.0],
            [373.15, 212.0],
        ],
    )


def wrap_vec2_test(
    fn: InvertibleFunction[Vector2D], input_val: Vector2D, output_val: Vector2D
):
    out: Vector = fn(input_val)
    assert out.isclose(output_val)


# doc-region-begin test add
def test_vec2___add__():
    e_1: Vector2D = Vector2D.e_1()
    e_2: Vector2D = Vector2D.e_2()
    zero: Vector2D = Vector2D.zero()

    result: Vector = 1 * e_1 + 2 * e_2 + 3 * e_1 + 4 * e_2
    assert result.isclose(4 * e_1 + 6 * e_2)
    # doc-region-end test add

    input_output_pairs: list[tuple[tuple[Vector2D, Vector2D], Vector2D]] = [
        ((zero, zero), zero),
        ((e_1, e_2), e_1 + e_2),
        (
            (e_1 + 2 * e_2, 3 * e_1 + 4 * e_2),
            4 * e_1 + 6 * e_2,
        ),
        ((2 * e_2, 3 * e_1), 3 * e_1 + 2 * e_2),
    ]

    for input_val, output_val in input_output_pairs:
        assert output_val.isclose(input_val[0] + input_val[1])


# doc-region-begin test substract
def test_vec2___sub__():
    e_1: Vector2D = Vector2D.e_1()
    e_2: Vector2D = Vector2D.e_2()
    zero: Vector2D = Vector2D.zero()

    result: Vector = (4 * e_1 + 6 * e_2) - (3 * e_1 + 4 * e_2)
    assert result.isclose(1 * e_1 + 2 * e_2)
    # doc-region-end test substract

    input_output_pairs: list[tuple[tuple[Vector2D, Vector2D], Vector2D]] = [
        ((zero, zero), zero),
        ((e_1, e_2), e_1 - e_2),
        (
            (5 * e_1 + 8 * e_2, e_1 + 2 * e_2),
            4 * e_1 + 6 * e_2,
        ),
    ]

    for input_val, output_val in input_output_pairs:
        assert Vector2D(*output_val).isclose(
            Vector2D(*input_val[0]) - Vector2D(*input_val[1])
        )


def test_vec2___mul__():
    input_output_pairs: list[list[tuple[int, int]]] = [
        [[(0.0, 0.0), 2], [0.0, 0.0]],
        [[(1.0, 0.0), 2], [2.0, 0.0]],
        [[(0.0, 1.0), 2], [0.0, 2.0]],
        [[(1.0, 1.0), 2], [2.0, 2.0]],
    ]

    for input_val, output_val in input_output_pairs:
        assert Vector2D(*output_val).isclose(
            input_val[1] * Vector2D(*input_val[0])
        )


def test_vec2___rmul__():
    input_output_pairs = [
        [[(0.0, 0.0), 2], [0.0, 0.0]],
        [[(1.0, 0.0), 2], [2.0, 0.0]],
        [[(0.0, 1.0), 2], [0.0, 2.0]],
        [[(1.0, 1.0), 2], [2.0, 2.0]],
    ]

    for input_val, output_val in input_output_pairs:
        assert Vector2D(*output_val).isclose(
            Vector2D(*input_val[0]) * input_val[1]
        )


def test_vec2___neg__():
    input_output_pairs = [
        [(0.0, 0.0), (0.0, 0.0)],
        [(1.0, 0.0), (-1.0, 0.0)],
        [(0.0, 1.0), (0.0, -1.0)],
        [(1.0, 1.0), (-1.0, -1.0)],
    ]

    for input_val, output_val in input_output_pairs:
        assert Vector2D(*output_val).isclose(-Vector2D(*input_val))


def test_vec2___abs__():
    input_output_pairs = [
        [(3.0, 4.0), 5.0],
        [(-3.0, 4.0), 5.0],
        [(3.0, -4.0), 5.0],
        [(-3.0, -4.0), 5.0],
    ]

    for input_val, output_val in input_output_pairs:
        assert output_val == abs(Vector2D(*input_val))


def test_vec2___dot__():
    input_output_pairs = [
        [[(1.0, 0.0), (0.0, 1.0)], 0.0],
        [[(1.0, 0.0), (1.0, 0.0)], 1.0],
        [[(0.0, 1.0), (0.0, 1.0)], 1.0],
        [[(3.0, 0.0), (1.0, 0.0)], 3.0],
        [[(0.0, 1.0), (0.0, 4.0)], 4.0],
    ]

    for input_val, output_val in input_output_pairs:
        assert output_val == Vector2D(*input_val[0]).dot(
            Vector2D(*input_val[1])
        )


def test_vec2_is_parallel():
    input_output_pairs = [
        [[(1.0, 0.0), (2.0, 0.0)], True],
        [[(0.0, 5.0), (0.0, 1.0)], True],
        [[(1.0, 5.0), (0.0, 1.0)], False],
        [[(0.0, 5.0), (0.2, 1.0)], False],
        [[(0.0, 5.0), (1.2, 0.0)], False],
    ]

    for input_val, output_val in input_output_pairs:
        assert output_val == is_parallel(
            Vector2D(*input_val[0]), Vector2D(*input_val[1])
        )


def test_vec2_is_counter_clockwise():
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
        assert output_val == is_counter_clockwise(
            Vector2D(*input_val[0]), Vector2D(*input_val[1])
        )


# doc-region-begin translate test
def test_vec2_translate():
    e_1: Vector2D = Vector2D.e_1()
    e_2: Vector2D = Vector2D.e_2()
    zero: Vector2D = Vector2D.zero()

    fn: InvertibleFunction[Vector2D] = translate(2 * e_1 + 3 * e_2)
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs: list[tuple[Vector2D, Vector2D]] = [
        (zero, 2 * e_1 + 3 * e_2),
        (e_1, 3 * e_1 + 3 * e_2),
        (e_2, 2 * e_1 + 4 * e_2),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


# doc-region-end translate test


def test_vec2_compose():
    e_1: Vector2D = Vector2D.e_1()
    e_2: Vector2D = Vector2D.e_2()
    zero: Vector2D = Vector2D.zero()

    fn: InvertibleFunction[Vector2D] = translate(Vector2D(x=2, y=3))
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    identity_fn: InvertibleFunction[Vector2D] = compose([fn_inv, fn])

    input_output_pairs: list[tuple[Vector2D, Vector2D]] = [
        (zero, zero),
        (e_1, e_1),
        (e_2, e_2),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(identity_fn, input_val, output_val)


def test_vec2_uniform_scale():
    e_1: Vector2D = Vector2D.e_1()
    e_2: Vector2D = Vector2D.e_2()
    zero: Vector2D = Vector2D.zero()

    fn: InvertibleFunction[Vector2D] = uniform_scale(4)
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs: list[tuple[Vector2D, Vector2D]] = [
        (zero, zero),
        (e_1, 4 * e_1),
        (e_2, 4 * e_2),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_vec2_scale():

    e_1: Vector2D = Vector2D.e_1()
    e_2: Vector2D = Vector2D.e_2()
    zero: Vector2D = Vector2D.zero()

    fn: InvertibleFunction[Vector2D] = scale_non_uniform_2d(m_x=2, m_y=3)
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs: list[tuple[Vector2D, Vector2D]] = [
        (zero, zero),
        (e_1, 2 * e_1),
        (e_2, 3 * e_2),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_vec2_rotate_90():

    e_1: Vector2D = Vector2D.e_1()
    e_2: Vector2D = Vector2D.e_2()
    zero: Vector2D = Vector2D.zero()

    fn: InvertibleFunction[Vector2D] = rotate_90_degrees()
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs: list[tuple[Vector2D, Vector2D]] = [
        (zero, zero),
        (e_1, e_2),
        (e_2, -1 * e_1),
        (-1 * e_1, -1 * e_2),
        (-1 * e_2, 1 * e_1),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_vec2_rotate():

    e_1: Vector2D = Vector2D.e_1()
    e_2: Vector2D = Vector2D.e_2()
    zero: Vector2D = Vector2D.zero()

    fn: InvertibleFunction[Vector2D] = rotate(math.radians(53.130102))
    fn_inv: InvertibleFunction[Vector2D] = inverse(fn)

    input_output_pairs: list[tuple[Vector2D, Vector2D]] = [
        (zero, zero),
        (5 * e_1, 3 * e_1 + 4 * e_2),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


# doc-region-begin test add
def test_vec3___add__():

    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()

    result: Vector = (1 * e_1 + 3 * e_2 + 5 * e_3) + (
        2 * e_1 + 4 * e_2 + 6 * e_3
    )
    assert result.isclose((3 * e_1 + 7 * e_2 + 11 * e_3))
    # doc-region-end test add


# doc-region-begin test substract
def test_vec3___sub__():
    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()

    result: Vector = (3 * e_1 + 7 * e_2 + 11 * e_3) - (
        2 * e_1 + 4 * e_2 + 6 * e_3
    )
    assert result.isclose(1 * e_1 + 3 * e_2 + 5 * e_3)
    # doc-region-end test substract


def test_vec3___mul__():
    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()

    result = (2 * e_1 + 3 * e_2 + 4 * e_3) * 4
    assert result.isclose(8 * e_1 + 12 * e_2 + 16 * e_3)


def test_vec3___rmul__():
    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()

    result = 4 * (2 * e_1 + 3 * e_2 + 4 * e_3)
    assert result.isclose(8 * e_1 + 12 * e_2 + 16 * e_3)


def test_vec3___neg__():
    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()

    result = -((2 * e_1) + (3 * e_2) + (4 * e_3))
    assert result.isclose((-2 * e_1) + (-3 * e_2) + (-4 * e_3))


def wrap_vec3_test(
    fn: InvertibleFunction[Vector3D],
    input_val: Vector3D,
    output_val: Vector3D,
):
    out: Vector = fn(input_val)
    assert out.isclose(output_val)


# doc-region-begin translate test
def test_vec3_translate():

    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()
    zero: Vector3D = Vector3D.zero()

    fn: InvertibleFunction[Vector3D] = translate(2 * e_1 + 3 * e_2 + 4 * e_3)
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs: list[tuple[Vector3D, Vector3D]] = [
        (zero, 2 * e_1 + 3 * e_2 + 4 * e_3),
        (e_1, 3 * e_1 + 3 * e_2 + 4 * e_3),
        (e_2, 2 * e_1 + 4 * e_2 + 4 * e_3),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


# doc-region-end translate test


def test_vec3_uniform_scale():

    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()
    zero: Vector3D = Vector3D.zero()

    fn: InvertibleFunction[Vector3D] = uniform_scale(4)
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs: list[tuple[Vector3D, Vector3D]] = [
        (zero, zero),
        (e_1, 4 * e_1),
        (e_2, 4 * e_2),
        (e_3, 4 * e_3),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_scale():

    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()
    zero: Vector3D = Vector3D.zero()

    fn: InvertibleFunction[Vector3D] = scale_non_uniform_3d(m_x=2, m_y=3, m_z=4)
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs: list[tuple[Vector3D, Vector3D]] = [
        (zero, zero),
        (e_1, 2 * e_1),
        (e_2, 3 * e_2),
        (e_3, 4 * e_3),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_rotate_x():

    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()
    zero: Vector3D = Vector3D.zero()

    fn: InvertibleFunction[Vector3D] = rotate_x(math.radians(53.130102))
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    orthogonal_component: Vector3D = 1 * e_1

    input_output_pairs: list[tuple[Vector3D, Vector3D]] = [
        (zero, zero),
        (orthogonal_component, orthogonal_component),
        (
            orthogonal_component + 5 * e_2,
            orthogonal_component + 3 * e_2 + 4 * e_3,
        ),
        (
            orthogonal_component + 5 * e_3,
            orthogonal_component + -4 * e_2 + 3 * e_3,
        ),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_rotate_y():

    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()
    zero: Vector3D = Vector3D.zero()

    orthogonal_component: Vector3D = 1 * e_2

    fn: InvertibleFunction[Vector3D] = rotate_y(math.radians(53.130102))
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    input_output_pairs: list[tuple[Vector3D, Vector3D]] = [
        (zero, zero),
        (orthogonal_component, orthogonal_component),
        (
            orthogonal_component + 5 * e_3,
            orthogonal_component + 3 * e_3 + 4 * e_1,
        ),
        (
            orthogonal_component + 5 * e_1,
            orthogonal_component + -4 * e_3 + 3 * e_1,
        ),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_rotate_z():

    e_1: Vector3D = Vector3D.e_1()
    e_2: Vector3D = Vector3D.e_2()
    e_3: Vector3D = Vector3D.e_3()
    zero: Vector3D = Vector3D.zero()

    fn: InvertibleFunction[Vector3D] = rotate_z(math.radians(53.130102))
    fn_inv: InvertibleFunction[Vector3D] = inverse(fn)

    orthogonal_component: Vector3D = 1 * e_3

    input_output_pairs: list[tuple[Vector3D, Vector3D]] = [
        (zero, zero),
        (orthogonal_component, orthogonal_component),
        (
            orthogonal_component + 5 * e_1,
            orthogonal_component + 3 * e_1 + 4 * e_2,
        ),
        (
            orthogonal_component + 5 * e_2,
            orthogonal_component + -4 * e_1 + 3 * e_2,
        ),
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


# doc-region-begin function stack examples definitions
def test_vec3_fn_stack():
    e_1: Vector1D = Vector1D.e_1()

    identity: InvertibleFunction[Vector1D] = uniform_scale(1)

    fn_stack.push(identity)
    assert 1 * e_1 == fn_stack.modelspace_to_ndc_fn()(1 * e_1)

    add_one: InvertibleFunction[Vector1D] = translate(1 * e_1)

    fn_stack.push(add_one)
    assert 2 * e_1 == fn_stack.modelspace_to_ndc_fn()(1 * e_1)  # x + 1 = 2

    multiply_by_2: InvertibleFunction[Vector1D] = uniform_scale(2)

    fn_stack.push(multiply_by_2)  # (x * 2) + 1 = 3
    assert 3 * e_1 == fn_stack.modelspace_to_ndc_fn()(1 * e_1)

    add_5: InvertibleFunction[Vector1D] = translate(5 * e_1)

    fn_stack.push(add_5)  # ((x + 5) * 2) + 1 = 13
    assert 13 * e_1 == fn_stack.modelspace_to_ndc_fn()(1 * e_1)

    fn_stack.pop()
    assert 3 * e_1 == fn_stack.modelspace_to_ndc_fn()(
        1 * e_1
    )  # (x * 2) + 1 = 3

    fn_stack.pop()
    assert 2 * e_1 == fn_stack.modelspace_to_ndc_fn()(1 * e_1)  # x + 1 = 2

    fn_stack.pop()
    assert 1 * e_1 == fn_stack.modelspace_to_ndc_fn()(1 * e_1)  # x = 1
    # doc-region-end function stack examples definitions


def test__find_normal__xy_plane():
    p1 = Vector3D(0.0, 0.0, 0.0)
    p2 = Vector3D(1.0, 0.0, 0.0)
    p3 = Vector3D(0.0, 1.0, 0.0)
    # CCW winding looking down -Z gives a normal along +Z
    assert mu.find_normal(p1, p2, p3).isclose(Vector3D(0.0, 0.0, 1.0))


def test__find_normal__cw_flips_sign():
    p1 = Vector3D(0.0, 0.0, 0.0)
    p2 = Vector3D(1.0, 0.0, 0.0)
    p3 = Vector3D(0.0, 1.0, 0.0)
    n_ccw = mu.find_normal(p1, p2, p3)
    n_cw = mu.find_normal(p1, p3, p2)
    assert n_ccw.isclose(-n_cw)


def test__find_normal__unnormalized_magnitude():
    # |cross| = 2 * triangle area; for a 1x1 right triangle area = 0.5
    # so |normal| = 1.0
    p1 = Vector3D(0.0, 0.0, 0.0)
    p2 = Vector3D(1.0, 0.0, 0.0)
    p3 = Vector3D(0.0, 1.0, 0.0)
    assert math.isclose(abs(mu.find_normal(p1, p2, p3)), 1.0)
    # Scale up: 2x2 right triangle area = 2.0, |normal| = 4.0
    p2 = Vector3D(2.0, 0.0, 0.0)
    p3 = Vector3D(0.0, 2.0, 0.0)
    assert math.isclose(abs(mu.find_normal(p1, p2, p3)), 4.0)


def test__plane_equation__xy_plane_through_origin():
    p1 = Vector3D(0.0, 0.0, 0.0)
    p2 = Vector3D(1.0, 0.0, 0.0)
    p3 = Vector3D(0.0, 1.0, 0.0)
    normal, d = mu.plane_equation(p1, p2, p3)
    assert normal.isclose(Vector3D(0.0, 0.0, 1.0))
    assert math.isclose(d, 0.0, abs_tol=1e-7)


def test__plane_equation__xy_plane_offset():
    # Plane y = 5
    p1 = Vector3D(0.0, 5.0, 0.0)
    p2 = Vector3D(1.0, 5.0, 0.0)
    p3 = Vector3D(0.0, 5.0, 1.0)
    normal, d = mu.plane_equation(p1, p2, p3)
    # Normal should be along ±Y; back-substitution: y_normal * 5 + d == 0
    assert math.isclose(normal.dot(p1) + d, 0.0, abs_tol=1e-7)
    assert math.isclose(normal.dot(p2) + d, 0.0, abs_tol=1e-7)
    assert math.isclose(normal.dot(p3) + d, 0.0, abs_tol=1e-7)


def test__plane_equation__diagonal():
    # Plane x + y + z = 1, so points (1,0,0), (0,1,0), (0,0,1) lie on it
    p1 = Vector3D(1.0, 0.0, 0.0)
    p2 = Vector3D(0.0, 1.0, 0.0)
    p3 = Vector3D(0.0, 0.0, 1.0)
    normal, d = mu.plane_equation(p1, p2, p3)
    expected_n = 1.0 / math.sqrt(3.0)
    # Normal must be parallel to (1,1,1)/sqrt(3) (up to sign)
    assert math.isclose(abs(normal.x), expected_n, abs_tol=1e-6)
    assert math.isclose(abs(normal.y), expected_n, abs_tol=1e-6)
    assert math.isclose(abs(normal.z), expected_n, abs_tol=1e-6)
    # And all three points satisfy the equation
    for p in (p1, p2, p3):
        assert math.isclose(normal.dot(p) + d, 0.0, abs_tol=1e-6)


def test__distance_to_plane__signed():
    p1 = Vector3D(0.0, 0.0, 0.0)
    p2 = Vector3D(1.0, 0.0, 0.0)
    p3 = Vector3D(0.0, 1.0, 0.0)
    plane = mu.plane_equation(p1, p2, p3)  # XY plane, normal = +Z

    assert math.isclose(
        mu.distance_to_plane(Vector3D(0.0, 0.0, 0.0), plane), 0.0,
        abs_tol=1e-7,
    )
    assert math.isclose(
        mu.distance_to_plane(Vector3D(0.0, 0.0, 5.0), plane), 5.0
    )
    assert math.isclose(
        mu.distance_to_plane(Vector3D(0.0, 0.0, -3.0), plane), -3.0
    )
    # Tangential motion shouldn't change the distance
    assert math.isclose(
        mu.distance_to_plane(Vector3D(7.0, -2.0, 4.0), plane), 4.0
    )


def test__doctest():
    failureCount, testCount = doctest.testmod(mu)
    assert 0 == failureCount
