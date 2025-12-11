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

import doctest
import math

import modelviewprojection.mathutils as mu


# doc-region-begin test add
def test__vec1__add__():
    result: mu.Vector = mu.Vector1D(x=1) + mu.Vector1D(x=3)
    assert result.isclose(mu.Vector1D(x=4))
    # doc-region-end test add


# doc-region-begin test substract
def test__vec1__sub__():
    result: mu.Vector = mu.Vector1D(x=5) - mu.Vector1D(x=1)
    assert result.isclose(mu.Vector1D(x=4))
    # doc-region-end test substract


def test__vec1__mul__():
    result = mu.Vector1D(x=2) * 4
    assert result.isclose(mu.Vector1D(x=8))


def test__vec1__rmul__():
    result = 4 * mu.Vector1D(x=2)
    assert result.isclose(mu.Vector1D(x=8))


def test__vec1__neg__():
    result = -mu.Vector1D(x=2)
    assert result.isclose(mu.Vector1D(x=-2))


def wrap_vec1_test(
    fn: mu.InvertibleFunction, input_val: float, output_val: float
):
    out: mu.Vector = fn(mu.Vector1D(input_val))
    assert out.isclose(mu.Vector1D(output_val))


# doc-region-begin translate test
def test__vec1_translate():
    fn: mu.InvertibleFunction = mu.translate(mu.Vector1D(2))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [-3, -1],
        [-2, 0],
        [-1, 1],
        [0, 2],
        [1, 3],
        [2, 4],
        [3, 5],
        [4, 6],
    ]
    for input_val, output_val in input_output_pairs:
        wrap_vec1_test(fn, input_val, output_val)
        wrap_vec1_test(fn_inv, output_val, input_val)


# doc-region-end translate test


def test__vec1_mx_plus_b():
    m = 5
    b = 2

    fn: mu.InvertibleFunction = mu.compose(
        [mu.translate(mu.Vector1D(b)), mu.uniform_scale(m)]
    )
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [-3, -13],
        [-2, -8],
        [-1, -3],
        [0, 2],
        [1, 7],
        [2, 12],
        [3, 17],
        [4, 22],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec1_test(fn, input_val, output_val)
        wrap_vec1_test(fn_inv, output_val, input_val)


def test_vec1_uniform_scale():
    fn: mu.InvertibleFunction = mu.uniform_scale(4)
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [-3, -12],
        [-2, -8],
        [-1, -4],
        [0, 0],
        [1, 4],
        [2, 8],
        [3, 12],
        [4, 16],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec1_test(fn, input_val, output_val)
        wrap_vec1_test(fn_inv, output_val, input_val)


def test_vec1_tempature_conversion():
    def test_vec1_vector1d_function(
        fn: mu.InvertibleFunction,
        input_output_pairs: list[list[float]],
    ):
        for input_val, output_val in input_output_pairs:
            assert fn(mu.Vector1D(input_val)).isclose(mu.Vector1D(output_val))
            assert mu.inverse(fn)(mu.Vector1D(output_val)).isclose(
                mu.Vector1D(input_val)
            )

    # doc-region-begin temperature functions
    celsius_to_kelvin: mu.InvertibleFunction = mu.translate(mu.Vector1D(273.15))
    fahrenheit_to_celsius: mu.InvertibleFunction = mu.compose(
        [mu.uniform_scale(5.0 / 9.0), mu.translate(mu.Vector1D(-32.0))]
    )
    fahrenheit_to_kelvin: mu.InvertibleFunction = mu.compose(
        [celsius_to_kelvin, fahrenheit_to_celsius]
    )
    kelvin_to_celsius: mu.InvertibleFunction = mu.inverse(celsius_to_kelvin)
    celsius_to_fahrenheit: mu.InvertibleFunction = mu.inverse(
        fahrenheit_to_celsius
    )
    kelvin_to_fahrenheit: mu.InvertibleFunction = mu.compose(
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
    fn: mu.InvertibleFunction, input_val: list[float], output_val: list[float]
):
    out: mu.Vector = fn(mu.Vector2D(*input_val))
    assert out.isclose(mu.Vector2D(*output_val))


# doc-region-begin test add
def test_vec2___add__():
    result: mu.Vector = mu.Vector2D(x=1, y=2) + mu.Vector2D(x=3, y=4)
    assert result.isclose(mu.Vector2D(x=4, y=6))
    # doc-region-end test add

    input_output_pairs = [
        [[(0.0, 0.0), (0.0, 0.0)], [0.0, 0.0]],
        [[(1.0, 0.0), (0.0, 1.0)], [1.0, 1.0]],
        [[(1.0, 2.0), (3.0, 4.0)], [4.0, 6.0]],
        [[(0.0, 2.0), (3.0, 0.0)], [3.0, 2.0]],
    ]

    for input_val, output_val in input_output_pairs:
        assert mu.Vector2D(*output_val).isclose(
            mu.Vector2D(*input_val[0]) + mu.Vector2D(*input_val[1])
        )


# doc-region-begin test substract
def test_vec2___sub__():
    result: mu.Vector = mu.Vector2D(x=4, y=6) - mu.Vector2D(x=3, y=4)
    assert result.isclose(mu.Vector2D(x=1, y=2))
    # doc-region-end test substract

    input_output_pairs = [
        [[(0.0, 0.0), (0.0, 0.0)], [0.0, 0.0]],
        [[(1.0, 0.0), (0.0, 1.0)], [1.0, -1.0]],
        [[(5.0, 8.0), (1.0, 2.0)], [4.0, 6.0]],
    ]

    for input_val, output_val in input_output_pairs:
        assert mu.Vector2D(*output_val).isclose(
            mu.Vector2D(*input_val[0]) - mu.Vector2D(*input_val[1])
        )


def test_vec2___mul__():
    input_output_pairs = [
        [[(0.0, 0.0), 2], [0.0, 0.0]],
        [[(1.0, 0.0), 2], [2.0, 0.0]],
        [[(0.0, 1.0), 2], [0.0, 2.0]],
        [[(1.0, 1.0), 2], [2.0, 2.0]],
    ]

    for input_val, output_val in input_output_pairs:
        assert mu.Vector2D(*output_val).isclose(
            input_val[1] * mu.Vector2D(*input_val[0])
        )


def test_vec2___rmul__():
    input_output_pairs = [
        [[(0.0, 0.0), 2], [0.0, 0.0]],
        [[(1.0, 0.0), 2], [2.0, 0.0]],
        [[(0.0, 1.0), 2], [0.0, 2.0]],
        [[(1.0, 1.0), 2], [2.0, 2.0]],
    ]

    for input_val, output_val in input_output_pairs:
        assert mu.Vector2D(*output_val).isclose(
            mu.Vector2D(*input_val[0]) * input_val[1]
        )


def test_vec2___neg__():
    input_output_pairs = [
        [(0.0, 0.0), (0.0, 0.0)],
        [(1.0, 0.0), (-1.0, 0.0)],
        [(0.0, 1.0), (0.0, -1.0)],
        [(1.0, 1.0), (-1.0, -1.0)],
    ]

    for input_val, output_val in input_output_pairs:
        assert mu.Vector2D(*output_val).isclose(-mu.Vector2D(*input_val))


def test_vec2___abs__():
    input_output_pairs = [
        [(3.0, 4.0), 5.0],
        [(-3.0, 4.0), 5.0],
        [(3.0, -4.0), 5.0],
        [(-3.0, -4.0), 5.0],
    ]

    for input_val, output_val in input_output_pairs:
        assert output_val == abs(mu.Vector2D(*input_val))


def test_vec2___dot__():
    input_output_pairs = [
        [[(1.0, 0.0), (0.0, 1.0)], 0.0],
        [[(1.0, 0.0), (1.0, 0.0)], 1.0],
        [[(0.0, 1.0), (0.0, 1.0)], 1.0],
        [[(3.0, 0.0), (1.0, 0.0)], 3.0],
        [[(0.0, 1.0), (0.0, 4.0)], 4.0],
    ]

    for input_val, output_val in input_output_pairs:
        assert output_val == mu.Vector2D(*input_val[0]).dot(
            mu.Vector2D(*input_val[1])
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
        assert output_val == mu.is_parallel(
            mu.Vector2D(*input_val[0]), mu.Vector2D(*input_val[1])
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
        assert output_val == mu.is_counter_clockwise(
            mu.Vector2D(*input_val[0]), mu.Vector2D(*input_val[1])
        )


# doc-region-begin translate test
def test_vec2_translate():
    fn: mu.InvertibleFunction = mu.translate(mu.Vector2D(x=2.0, y=3.0))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

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
    fn: mu.InvertibleFunction = mu.translate(mu.Vector2D(x=2, y=3))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    identity_fn: mu.InvertibleFunction = mu.compose([fn_inv, fn])

    input_output_pairs = [
        [[0, 0], [0, 0]],
        [[1, 0], [1, 0]],
        [[0, 1], [0, 1]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(identity_fn, input_val, output_val)


def test_vec2_uniform_scale():
    fn: mu.InvertibleFunction = mu.uniform_scale(4)
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0, 0], [0, 0]],
        [[1, 0], [4, 0]],
        [[0, 1], [0, 4]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_vec2_scale():
    fn: mu.InvertibleFunction = mu.scale_non_uniform_2d(m_x=2, m_y=3)
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0, 0], [0, 0]],
        [[1, 0], [2, 0]],
        [[0, 1], [0, 3]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


def test_vec2_rotate_90():
    fn: mu.InvertibleFunction = mu.rotate_90_degrees()
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

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
    fn: mu.InvertibleFunction = mu.rotate(math.radians(53.130102))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0], [0.0, 0.0]],
        [[5.0, 0.0], [3.0, 4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec2_test(fn, input_val, output_val)
        wrap_vec2_test(fn_inv, output_val, input_val)


# doc-region-begin test add
def test_vec3___add__():
    result: mu.Vector = mu.Vector3D(x=1, y=3, z=5) + mu.Vector3D(x=2, y=4, z=6)
    assert result.isclose(mu.Vector3D(x=3, y=7, z=11))
    # doc-region-end test add


# doc-region-begin test substract
def test_vec3___sub__():
    result: mu.Vector = mu.Vector3D(x=3, y=7, z=11) - mu.Vector3D(x=2, y=4, z=6)
    assert result.isclose(mu.Vector3D(x=1, y=3, z=5))
    # doc-region-end test substract


def test_vec3___mul__():
    result = mu.Vector3D(x=2, y=3, z=4) * 4
    assert result.isclose(mu.Vector3D(x=8, y=12, z=16))


def test_vec3___rmul__():
    result = 4 * mu.Vector3D(x=2, y=3, z=4)
    assert result.isclose(mu.Vector3D(x=8, y=12, z=16))


def test_vec3___neg__():
    result = -mu.Vector3D(x=2, y=3, z=4)
    assert result.isclose(mu.Vector3D(x=-2, y=-3, z=-4))


def wrap_vec3_test(
    fn: mu.InvertibleFunction, input_val: list[float], output_val: list[float]
):
    out: mu.Vector = fn(mu.Vector3D(*input_val))
    assert out.isclose(mu.Vector3D(*output_val))


# doc-region-begin translate test
def test_vec3_translate():
    fn: mu.InvertibleFunction = mu.translate(mu.Vector3D(x=2, y=3, z=4))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

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
    fn: mu.InvertibleFunction = mu.uniform_scale(4)
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

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
    fn: mu.InvertibleFunction = mu.scale_non_uniform_3d(m_x=2, m_y=3, m_z=4)
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

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
    fn: mu.InvertibleFunction = mu.rotate_x(math.radians(53.130102))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 5.0, 0.0], [0.0, 3.0, 4.0]],
        [[0.0, 0.0, 5.0], [0.0, -4.0, 3.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_rotate_y():
    fn: mu.InvertibleFunction = mu.rotate_y(math.radians(53.130102))
    fn_inv: mu.InvertibleFunction = mu.inverse(fn)

    input_output_pairs = [
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        [[0.0, 0.0, 5.0], [4.0, 0.0, 3.0]],
        [[5.0, 0.0, 0.0], [3.0, 0.0, -4.0]],
    ]

    for input_val, output_val in input_output_pairs:
        wrap_vec3_test(fn, input_val, output_val)
        wrap_vec3_test(fn_inv, output_val, input_val)


def test_vec3_rotate_z():
    fn: mu.InvertibleFunction = mu.rotate_z(math.radians(53.130102))
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
def test_vec3_fn_stack():
    identity: InvertibleFunction = mu.uniform_scale(1)

    mu.fn_stack.push(identity)
    assert mu.Vector1D(1) == mu.fn_stack.modelspace_to_ndc_fn()(mu.Vector1D(1))

    add_one: InvertibleFunction = mu.translate(mu.Vector1D(1))

    mu.fn_stack.push(add_one)
    assert mu.Vector1D(2) == mu.fn_stack.modelspace_to_ndc_fn()(
        mu.Vector1D(1)
    )  # x + 1 = 2

    multiply_by_2: InvertibleFunction = mu.uniform_scale(2)

    mu.fn_stack.push(multiply_by_2)  # (x * 2) + 1 = 3
    assert mu.Vector1D(3) == mu.fn_stack.modelspace_to_ndc_fn()(mu.Vector1D(1))

    add_5: InvertibleFunction = mu.translate(mu.Vector1D(5))

    mu.fn_stack.push(add_5)  # ((x + 5) * 2) + 1 = 13
    assert mu.Vector1D(13) == mu.fn_stack.modelspace_to_ndc_fn()(mu.Vector1D(1))

    mu.fn_stack.pop()
    assert mu.Vector1D(3) == mu.fn_stack.modelspace_to_ndc_fn()(
        mu.Vector1D(1)
    )  # (x * 2) + 1 = 3

    mu.fn_stack.pop()
    assert mu.Vector1D(2) == mu.fn_stack.modelspace_to_ndc_fn()(
        mu.Vector1D(1)
    )  # x + 1 = 2

    mu.fn_stack.pop()
    assert mu.Vector1D(1) == mu.fn_stack.modelspace_to_ndc_fn()(
        mu.Vector1D(1)
    )  # x = 1
    # doc-region-end function stack examples definitions


def test__doctest():
    failureCount, testCount = doctest.testmod(mu)
    assert 0 == failureCount
