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
    Vector,
    Vector1D,
    InvertibleFunction,
    identity,
    inverse,
    compose,
    compose_intermediate_fns,
    compose_intermediate_fns_and_fn,
    translate,
    uniform_scale,
    Vector2D,
    scale_non_uniform_2d,
    rotate_90_degrees,
    rotate,
    rotate_around,
    sine,
    is_counter_clockwise,
    is_clockwise,
    is_parallel,
    Vector3D,
    abs_sin,
    scale_non_uniform_3d,
    rotate_x,
    rotate_y,
    rotate_z,
    ortho,
    perspective,
    cs_to_ndc_space_fn,
    FunctionStack,
    push_transformation,
    fn_stack,
)

e_1_1d = Vector1D.e_1()

e_1_2d = Vector2D.e_1()
e_2_2d = Vector2D.e_2()

e_1_3d = Vector3D.e_1()
e_2_3d = Vector3D.e_2()
e_3_3d = Vector3D.e_3()






# doc-region-begin test add
def test__vec1__add__():
    result: Vector = 1 * e_1_1d + 3 * e_1_1d
    assert result.isclose(4 * e_1_1d)
    # doc-region-end test add


# doc-region-begin test substract
def test__vec1__sub__():
    result: Vector = 5 * e_1_1d - (1 * e_1_1d)
    assert result.isclose(4 * e_1_1d)
    # doc-region-end test substract


def test__vec1__mul__():
    result = (2 * e_1_1d) * 4
    assert result.isclose(8 * e_1_1d)


def test__vec1__rmul__():
    result = 4 * (2 * e_1_1d)
    assert result.isclose(8 * e_1_1d)


def test__vec1__neg__():
    result = -(2 * e_1_1d)
    assert result.isclose(-2 * e_1_1d)


def wrap_vec1_test(
    fn: InvertibleFunction, input_val: Vector1D, output_val: Vector1D
):
    out: Vector = fn(input_val)
    assert out.isclose(output_val)


# doc-region-begin translate test
def test__vec1_translate():
    fn: InvertibleFunction = translate(2 * e_1_1d)
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs: list[tuple[Vector1D, Vector1D]] = [
        [(-3 * e_1_1d), (-1 * e_1_1d)],
        [(-2 * e_1_1d), (0 * e_1_1d)],
        [(-1 * e_1_1d), (1 * e_1_1d)],
        [(0 * e_1_1d), (2 * e_1_1d)],
        [(1 * e_1_1d), (3 * e_1_1d)],
        [(2 * e_1_1d), (4 * e_1_1d)],
        [(3 * e_1_1d), (5 * e_1_1d)],
        [(4 * e_1_1d), (6 * e_1_1d)],
    ]
    for input_val, output_val in input_output_pairs:
        wrap_vec1_test(fn, input_val, output_val)
        wrap_vec1_test(fn_inv, output_val, input_val)


# doc-region-end translate test


def test__vec1_mx_plus_b():
    m = 5
    b = 2

    fn: InvertibleFunction = compose(
        [translate(Vector1D(b)), uniform_scale(m)]
    )
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs: list[tuple[Vector1D, Vector1D]] = [
        [(-3 * e_1_1d), (-13 * e_1_1d)],
        [(-2 * e_1_1d), (-8 * e_1_1d)],
        [(-1 * e_1_1d), (-3 * e_1_1d)],
        [(-0 * e_1_1d), (2 * e_1_1d)],
        [(1 * e_1_1d), (7 * e_1_1d)],
        [(2 * e_1_1d), (12 * e_1_1d)],
        [(3 * e_1_1d), (17 * e_1_1d)],
        [(4 * e_1_1d), (22 * e_1_1d)],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec1_test(fn, input_val, output_val)
        wrap_vec1_test(fn_inv, output_val, input_val)


def test_vec1_uniform_scale():
    fn: InvertibleFunction = uniform_scale(4)
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs: list[tuple[Vector1D, Vector1D]] = [
        [(-3 * e_1_1d), (-12 * e_1_1d)],
        [(-2 * e_1_1d), (-8 * e_1_1d)],
        [(-1 * e_1_1d), (-4 * e_1_1d)],
        [(0 * e_1_1d), (0 * e_1_1d)],
        [(1 * e_1_1d), (4 * e_1_1d)],
        [(2 * e_1_1d), (8 * e_1_1d)],
        [(3 * e_1_1d), (12 * e_1_1d)],
        [(4 * e_1_1d), (16 * e_1_1d)],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec1_test(fn, input_val, output_val)
        wrap_vec1_test(fn_inv, output_val, input_val)


def test_vec1_tempature_conversion():
    def test_vec1_vector1d_function(
        fn: InvertibleFunction,
        input_output_pairs: list[list[float]],
    ):
        for input_val, output_val in input_output_pairs:
            assert fn(Vector1D(input_val)).isclose(Vector1D(output_val))
            assert inverse(fn)(Vector1D(output_val)).isclose(
                Vector1D(input_val)
            )

    # doc-region-begin temperature functions
    celsius_to_kelvin: InvertibleFunction = translate(Vector1D(273.15))
    fahrenheit_to_celsius: InvertibleFunction = compose(
        [uniform_scale(5.0 / 9.0), translate(Vector1D(-32.0))]
    )
    fahrenheit_to_kelvin: InvertibleFunction = compose(
        [celsius_to_kelvin, fahrenheit_to_celsius]
    )
    kelvin_to_celsius: InvertibleFunction = inverse(celsius_to_kelvin)
    celsius_to_fahrenheit: InvertibleFunction = inverse(
        fahrenheit_to_celsius
    )
    kelvin_to_fahrenheit: InvertibleFunction = compose(
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
    fn: InvertibleFunction, input_val: list[float], output_val: list[float]
):
    out: Vector = fn(Vector2D(*input_val))
    assert out.isclose(Vector2D(*output_val))


# doc-region-begin test add
def test_vec2___add__():
    result: Vector = Vector2D(x=1, y=2) + Vector2D(x=3, y=4)
    assert result.isclose(Vector2D(x=4, y=6))
    # doc-region-end test add

    input_output_pairs: list[tuple[int, int]] = [
        (((0.0, 0.0), (0.0, 0.0)), [0.0, 0.0]),
        (((1.0, 0.0), (0.0, 1.0)), [1.0, 1.0]),
        (((1.0, 2.0), (3.0, 4.0)), [4.0, 6.0]),
        (((0.0, 2.0), (3.0, 0.0)), [3.0, 2.0]),
    ]

    for input_val, output_val in input_output_pairs:
        assert Vector2D(*output_val).isclose(
            Vector2D(*input_val[0]) + Vector2D(*input_val[1])
        )


# doc-region-begin test substract
def test_vec2___sub__():
    result: Vector = Vector2D(x=4, y=6) - Vector2D(x=3, y=4)
    assert result.isclose(Vector2D(x=1, y=2))
    # doc-region-end test substract

    input_output_pairs: list[list[tuple[int, int]]] = [
        [[(0.0, 0.0), (0.0, 0.0)], [0.0, 0.0]],
        [[(1.0, 0.0), (0.0, 1.0)], [1.0, -1.0]],
        [[(5.0, 8.0), (1.0, 2.0)], [4.0, 6.0]],
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
    fn: InvertibleFunction = translate(Vector2D(x=2.0, y=3.0))
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0, 0], [2, 3]],
        [[1, 0], [3, 3]],
        [[0, 1], [2, 4]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


# doc-region-end translate test


def test_vec2_compose():
    fn: InvertibleFunction = translate(Vector2D(x=2, y=3))
    fn_inv: InvertibleFunction = inverse(fn)

    identity_fn: InvertibleFunction = compose([fn_inv, fn])

    input_output_pairs = [
        [[0, 0], [0, 0]],
        [[1, 0], [1, 0]],
        [[0, 1], [0, 1]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(identity_fn, input_val, output_val)


def test_vec2_uniform_scale():
    fn: InvertibleFunction = uniform_scale(4)
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0, 0], [0, 0]],
        [[1, 0], [4, 0]],
        [[0, 1], [0, 4]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_vec2_scale():
    fn: InvertibleFunction = scale_non_uniform_2d(m_x=2, m_y=3)
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0, 0], [0, 0]],
        [[1, 0], [2, 0]],
        [[0, 1], [0, 3]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_vec2_rotate_90():
    fn: InvertibleFunction = rotate_90_degrees()
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0, 0], [0, 0]],
        [[1, 0], [0, 1]],
        [[0, 1], [-1, 0]],
        [[-1, 0], [0, -1]],
        [[0, -1], [1, 0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_vec2_rotate():
    fn: InvertibleFunction = rotate(math.radians(53.130102))
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[5.0, 0.0], [3.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


# doc-region-begin test add
def test_vec3___add__():
    result: Vector = Vector3D(x=1, y=3, z=5) + Vector3D(x=2, y=4, z=6)
    assert result.isclose(Vector3D(x=3, y=7, z=11))
    # doc-region-end test add


# doc-region-begin test substract
def test_vec3___sub__():
    result: Vector = Vector3D(x=3, y=7, z=11) - Vector3D(x=2, y=4, z=6)
    assert result.isclose(Vector3D(x=1, y=3, z=5))
    # doc-region-end test substract


def test_vec3___mul__():
    result = Vector3D(x=2, y=3, z=4) * 4
    assert result.isclose(Vector3D(x=8, y=12, z=16))


def test_vec3___rmul__():
    result = 4 * Vector3D(x=2, y=3, z=4)
    assert result.isclose(Vector3D(x=8, y=12, z=16))


def test_vec3___neg__():
    result = -Vector3D(x=2, y=3, z=4)
    assert result.isclose(Vector3D(x=-2, y=-3, z=-4))


def wrap_vec3_test(
    fn: InvertibleFunction, input_val: list[float], output_val: list[float]
):
    out: Vector = fn(Vector3D(*input_val))
    assert out.isclose(Vector3D(*output_val))


# doc-region-begin translate test
def test_vec3_translate():
    fn: InvertibleFunction = translate(Vector3D(x=2, y=3, z=4))
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0, 0, 0], [2, 3, 4]],
        [[1, 0, 0], [3, 3, 4]],
        [[0, 1, 0], [2, 4, 4]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


# doc-region-end translate test


def test_vec3_uniform_scale():
    fn: InvertibleFunction = uniform_scale(4)
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0, 0, 0], [0, 0, 0]],
        [[1, 0, 0], [4, 0, 0]],
        [[0, 1, 0], [0, 4, 0]],
        [[0, 0, 1], [0, 0, 4]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_scale():
    fn: InvertibleFunction = scale_non_uniform_3d(m_x=2, m_y=3, m_z=4)
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0, 0, 0], [0, 0, 0]],
        [[1, 0, 0], [2, 0, 0]],
        [[0, 1, 0], [0, 3, 0]],
        [[0, 0, 1], [0, 0, 4]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_rotate_x():
    fn: InvertibleFunction = rotate_x(math.radians(53.130102))
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 5.0, 0.0], [0.0, 3.0, 4.0]],
        [[0.0, 0.0, 5.0], [0.0, -4.0, 3.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_rotate_y():
    fn: InvertibleFunction = rotate_y(math.radians(53.130102))
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 0.0, 5.0], [4.0, 0.0, 3.0]],
        [[5.0, 0.0, 0.0], [3.0, 0.0, -4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_rotate_z():
    fn: InvertibleFunction = rotate_z(math.radians(53.130102))
    fn_inv: InvertibleFunction = inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[5.0, 0.0, 0.0], [3.0, 4.0, 0.0]],
        [[0.0, 5.0, 0.0], [-4.0, 3.0, 0.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


# doc-region-begin function stack examples definitions
def test_vec3_fn_stack():
    identity: InvertibleFunction = uniform_scale(1)

    fn_stack.push(identity)
    assert Vector1D(1) == fn_stack.modelspace_to_ndc_fn()(Vector1D(1))

    add_one: InvertibleFunction = translate(Vector1D(1))

    fn_stack.push(add_one)
    assert Vector1D(2) == fn_stack.modelspace_to_ndc_fn()(
        Vector1D(1)
    )  # x + 1 = 2

    multiply_by_2: InvertibleFunction = uniform_scale(2)

    fn_stack.push(multiply_by_2)  # (x * 2) + 1 = 3
    assert Vector1D(3) == fn_stack.modelspace_to_ndc_fn()(Vector1D(1))

    add_5: InvertibleFunction = translate(Vector1D(5))

    fn_stack.push(add_5)  # ((x + 5) * 2) + 1 = 13
    assert Vector1D(13) == fn_stack.modelspace_to_ndc_fn()(Vector1D(1))

    fn_stack.pop()
    assert Vector1D(3) == fn_stack.modelspace_to_ndc_fn()(
        Vector1D(1)
    )  # (x * 2) + 1 = 3

    fn_stack.pop()
    assert Vector1D(2) == fn_stack.modelspace_to_ndc_fn()(
        Vector1D(1)
    )  # x + 1 = 2

    fn_stack.pop()
    assert Vector1D(1) == fn_stack.modelspace_to_ndc_fn()(
        Vector1D(1)
    )  # x = 1
    # doc-region-end function stack examples definitions


def test__doctest():
    failureCount, testCount = doctest.testmod(mu)
    assert 0 == failureCount
