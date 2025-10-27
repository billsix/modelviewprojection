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

import modelviewprojection.mathutils1d as mu1d


def test___add__():
    result = mu1d.Vector1D(x=1) + mu1d.Vector1D(x=3)
    assert result.isclose(mu1d.Vector1D(x=4))


def test___sub__():
    result = mu1d.Vector1D(x=5) - mu1d.Vector1D(x=1)
    assert result.isclose(mu1d.Vector1D(x=4))


def test___mul__():
    result = mu1d.Vector1D(x=2) * 4
    assert result.isclose(mu1d.Vector1D(x=8))


def test___rmul__():
    result = 4 * mu1d.Vector1D(x=2)
    assert result.isclose(mu1d.Vector1D(x=8))


def test___neg__():
    result = -mu1d.Vector1D(x=2)
    assert result.isclose(mu1d.Vector1D(x=-2))


def wrap_vec1_test(
    fn: mu1d.InvertibleFunction, input_val: float, output_val: float
):
    out: mu1d.Vector = fn(mu1d.Vector1D(input_val))
    assert out.isclose(mu1d.Vector1D(output_val))


# doc-region-begin translate test
def test_translate():
    fn: mu1d.InvertibleFunction = mu1d.translate(mu1d.Vector1D(2))
    fn_inv: mu1d.InvertibleFunction = mu1d.inverse(fn)

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


def test_mx_plus_b():
    m = 5
    b = 2

    fn: mu1d.InvertibleFunction = mu1d.compose(
        [mu1d.translate(mu1d.Vector1D(b)), mu1d.uniform_scale(m)]
    )
    fn_inv: mu1d.InvertibleFunction = mu1d.inverse(fn)

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


def test_uniform_scale():
    fn: mu1d.InvertibleFunction = mu1d.uniform_scale(4)
    fn_inv: mu1d.InvertibleFunction = mu1d.inverse(fn)

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


def test_tempature_conversion():
    def test_vector1d_function(
        fn: mu1d.InvertibleFunction,
        input_output_pairs: list[list[float]],
    ):
        for input_val, output_val in input_output_pairs:
            assert fn(mu1d.Vector1D(input_val)).isclose(
                mu1d.Vector1D(output_val)
            )
            assert mu1d.inverse(fn)(mu1d.Vector1D(output_val)).isclose(
                mu1d.Vector1D(input_val)
            )

    # doc-region-begin temperature functions
    celsius_to_kelvin: mu1d.InvertibleFunction = mu1d.translate(
        mu1d.Vector1D(273.15)
    )
    fahrenheit_to_celsius: mu1d.InvertibleFunction = mu1d.compose(
        [mu1d.uniform_scale(5.0 / 9.0), mu1d.translate(mu1d.Vector1D(-32.0))]
    )
    fahrenheit_to_kelvin: mu1d.InvertibleFunction = mu1d.compose(
        [celsius_to_kelvin, fahrenheit_to_celsius]
    )
    kelvin_to_celsius: mu1d.InvertibleFunction = mu1d.inverse(celsius_to_kelvin)
    celsius_to_fahrenheit: mu1d.InvertibleFunction = mu1d.inverse(
        fahrenheit_to_celsius
    )
    kelvin_to_fahrenheit: mu1d.InvertibleFunction = mu1d.compose(
        [celsius_to_fahrenheit, kelvin_to_celsius]
    )

    # doc-region-end temperature functions

    test_vector1d_function(
        celsius_to_kelvin,
        [
            [0.0, 273.15],
            [100.0, 373.15],
        ],
    )
    test_vector1d_function(
        fahrenheit_to_celsius,
        [
            [32.0, 0.0],
            [212.0, 100.0],
        ],
    )
    test_vector1d_function(
        fahrenheit_to_kelvin,
        [
            [32.0, 273.15],
            [212.0, 373.15],
        ],
    )
    test_vector1d_function(
        kelvin_to_celsius,
        [
            [273.15, 0.0],
            [373.15, 100.0],
        ],
    )
    test_vector1d_function(
        celsius_to_fahrenheit,
        [
            [0.0, 32.0],
            [100.0, 212.0],
        ],
    )
    test_vector1d_function(
        kelvin_to_fahrenheit,
        [
            [273.15, 32.0],
            [373.15, 212.0],
        ],
    )


def test_doctest():
    failureCount, testCount = doctest.testmod(mu1d)
    assert 0 == failureCount
