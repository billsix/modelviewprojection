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

import itertools

import sympy

from modelviewprojection.mathutils import (
    MultiVector,
    MultiVectorFn,
    a_1,
    a_2,
    a_3,
    b_1,
    b_2,
    b_3,
    e_1,
    e_2,
    e_3,
    one,
    sym_vec2_1,
    sym_vec2_2,
    sym_vec3_1,
    sym_vec3_2,
    sym_vec_plane,
    zero,
)


# doc-region-begin test add
def test_multivector_add() -> None:
    a: MultiVector = 5 * e_1 + 6 * e_2
    b: MultiVector = 7 * e_1 + 8 * e_2
    assert (a + b) == (12 * e_1 + 14 * e_2)

    c: MultiVector = 7 * e_1 + 2 * e_2
    d: MultiVector = 1 * e_1 + 3 * e_3
    assert (c + d) == (8 * e_1 + 2 * e_2 + 3 * e_3)
    # doc-region-end test add


# doc-region-begin test substract
def test_multivector_subtract() -> None:
    a: MultiVector = 5 * e_1 + 6 * e_2
    b: MultiVector = 7 * e_1 + 9 * e_2
    assert (b - a) == (2 * e_1 + 3 * e_2)
    # doc-region-end test substract


def test_multivector_absolute_units() -> None:
    # test addition
    assert (e_1 + e_2) == (e_2 + e_1)

    # test scalar multiplication
    assert (e_1 * 2) == (e_1 + e_1)
    assert (2 * e_1) == (e_1 + e_1)
    assert (e_2 * 2) == (e_2 + e_2)
    assert (2 * e_2) == (e_2 + e_2)

    # test addition on relative units
    assert ((e_1 + e_2) * 2) == ((e_1 + e_2) + (e_1 + e_2))

    # test permutations
    assert (e_1 * e_2 * e_3).magnitude_squared() == 1
    assert (e_1 * e_3 * e_2) == -1 * (e_1 * e_2 * e_3)
    assert (e_3 * e_1 * e_2) == (e_1 * e_2 * e_3)
    assert (e_3 * e_2 * e_1) == -1 * (e_1 * e_2 * e_3)
    assert (e_2 * e_1 * e_3) == -1 * (e_1 * e_2 * e_3)
    assert (e_2 * e_3 * e_1) == (e_1 * e_2 * e_3)


def test_multivector_mult() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert a.magnitude_squared() == 25

    assert (a * a) == MultiVector.from_scalar(25)
    assert (a * a).is_scalar()

    i: MultiVector = MultiVector.unit_pseudoscalar(2)
    assert (a * i) == (-4 * e_1 + 3 * e_2)
    assert ((a * i) * i) == -3 * e_1 + -4 * e_2

    assert (sym_vec2_1 * sym_vec2_2) == (
        MultiVector.from_scalar(a_1 * b_1 + a_2 * b_2)
        + (a_1 * b_2 - a_2 * b_1) * e_1 * e_2
    )

    assert (sym_vec2_1 * sym_vec2_2) == (
        sym_vec2_1.dot(sym_vec2_2) + (sym_vec2_1 * i).dot(sym_vec2_2) * i
    )


def test_multivector_mult3d() -> None:
    def planewise_wedge(plane, vec1, vec2):
        proj: MultiVectorFn = MultiVector.project(plane)
        return proj(vec1).wedge(proj(vec2))

    assert (sym_vec3_1 * sym_vec3_2) == (
        MultiVector.from_scalar(a_1 * b_1 + a_2 * b_2 + a_3 * b_3)
        + (a_1 * b_2 - a_2 * b_1) * e_1 * e_2
        + (a_2 * b_3 - a_3 * b_2) * e_2 * e_3
        + (a_3 * b_1 - a_1 * b_3) * e_3 * e_1
    )

    assert (sym_vec3_1 * sym_vec3_2) == sum(
        [
            sym_vec3_1.dot(sym_vec3_2),
            *[
                planewise_wedge(
                    plane=axis_1.wedge(axis_2), vec1=sym_vec3_1, vec2=sym_vec3_2
                )
                for axis_1, axis_2 in itertools.combinations([e_1, e_2, e_3], 2)
            ],
        ],
        start=zero,
    )

    assert sym_vec3_1.dot(sym_vec3_2) == sym_vec3_1.dot(sym_vec3_2)

    assert (sym_vec3_1.wedge(sym_vec3_2)) == sum(
        [
            planewise_wedge(
                plane=axis_1 * axis_2, vec1=sym_vec3_1, vec2=sym_vec3_2
            )
            for axis_1, axis_2 in itertools.combinations([e_1, e_2, e_3], 2)
        ],
        start=zero,
    )


def test_multivector_dual() -> None:
    assert sym_vec2_1.dual(g=2) == sum(
        [a_2 * e_1, -a_1 * e_2],
        start=zero,
    )

    assert sym_vec3_1.dual(g=3) == sum(
        [-a_3 * e_1 * e_2, -a_2 * e_3 * e_1, -a_1 * e_2 * e_3],
        start=zero,
    )


def test_multivector_grade() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert a.r_vector_part(0) == zero
    assert a.scalar_part() == 0
    assert a.max_grade() == 1

    b: MultiVector = 3 * e_1 + 4 * e_2

    assert (b * b).scalar_part() == 25
    assert (b * b).r_vector_part(1) == zero
    assert (b * b).r_vector_part(2) == zero
    assert (b * b).max_grade() == 0

    c: MultiVector = -4 * e_1 + 3 * e_2
    assert (b * c).scalar_part() == 0
    assert (b * c).r_vector_part(1) == zero
    assert (b * c).r_vector_part(2) == 25 * e_1 * e_2
    assert (b * c).max_grade() == 2

    i3: MultiVector = e_1 * e_2 * e_3
    assert i3.scalar_part() == 0
    assert i3.r_vector_part(1) == zero
    assert i3.r_vector_part(2) == zero
    assert i3.r_vector_part(3) == i3
    assert i3.max_grade() == 3


def test_is_homogeneous_of_grade_r() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert a.is_homogeneous_of_grade_r(1)
    assert (a * a).is_homogeneous_of_grade_r(0)
    assert not (a * a).is_homogeneous_of_grade_r(1)
    assert not (a * a).is_homogeneous_of_grade_r(2)

    b: MultiVector = -4 * e_1 + 3 * e_2

    assert (a * b).is_homogeneous_of_grade_r(2)
    assert (a.wedge(b)).is_homogeneous_of_grade_r(2)

    c: MultiVector = 0 * e_1 + 5 * e_2
    assert not (a * c).is_homogeneous_of_grade_r(2)
    assert (a.wedge(c)).is_homogeneous_of_grade_r(2)


def test_is_vector() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert a.is_vector()
    assert not (a * a).is_vector()


def test_is_bivector() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    b: MultiVector = 0 * e_1 + 1 * e_2
    assert not (a * b).is_bivector()
    assert (a.wedge(b)).is_bivector()


def test_even_part_odd_part() -> None:
    assert (sym_vec3_1).odd_part() == sym_vec3_1
    assert (sym_vec3_1).even_part() == zero
    assert (sym_vec3_1 * sym_vec3_2).odd_part() == zero
    assert (sym_vec3_1 * sym_vec3_2).even_part() == sym_vec3_1 * sym_vec3_2

    assert (sym_vec3_1 * sym_vec3_2) == (sym_vec3_1 * sym_vec3_2).odd_part() + (
        sym_vec3_1 * sym_vec3_2
    ).even_part()


def test_multivector_dot() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert a.dot(a) == MultiVector.from_scalar(25)
    assert a.dot(a).is_scalar()
    c: MultiVector = -4 * e_1 + 3 * e_2
    assert a.dot(c) == zero

    assert sym_vec2_1.dot(sym_vec2_2) == MultiVector.from_scalar(
        a_1 * b_1 + a_2 * b_2
    )
    assert sym_vec2_1.dot(sym_vec2_2).is_scalar()


def test_is_orthogonal() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    c: MultiVector = -4 * e_1 + 3 * e_2
    assert a.is_orthogonal_to(c)


def test_multivector_cosine() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert a.cosine(a) == 1
    b: MultiVector = -4 * e_1 + 3 * e_2
    assert a.cosine(b) == 0

    # print(sym_vec2_1.cosine(sym_vec2_2) * abs(sym_vec2_1) * abs(sym_vec2_2))
    assert MultiVector.from_scalar(
        sym_vec2_1.cosine(sym_vec2_2) * abs(sym_vec2_1) * abs(sym_vec2_2)  # type: ignore
    ) == sym_vec2_1.dot(sym_vec2_2)


def test_multivector_wedge() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert a.wedge(a) == zero
    c: MultiVector = -4 * e_1 + 3 * e_2
    assert a.wedge(c) == 25 * e_1 * e_2

    # test method itself
    assert (
        sym_vec2_1.wedge(sym_vec2_2)
        == MultiVector.from_scalar(a_1 * b_2 - a_2 * b_1) * e_1 * e_2
    )

    # test the override
    assert (
        sym_vec2_1 ^ sym_vec2_2
        == MultiVector.from_scalar(a_1 * b_2 - a_2 * b_1) * e_1 * e_2
    )

    # test the outer_product_of_vectors
    assert (
        MultiVector.outer_product_of_vectors(sym_vec2_1, sym_vec2_2)
        == MultiVector.from_scalar(a_1 * b_2 - a_2 * b_1) * e_1 * e_2
    )


def test_multivector_unit_pseudoscalar() -> None:
    assert MultiVector.unit_pseudoscalar(1) == e_1
    assert MultiVector.unit_pseudoscalar(2) == e_1 * e_2
    assert MultiVector.unit_pseudoscalar(3) == e_1 * e_2 * e_3

    i1: MultiVector = MultiVector.unit_pseudoscalar(1)
    assert i1 * i1 == one
    assert MultiVector.unit_pseudoscalar_squared(1) == one
    i2: MultiVector = MultiVector.unit_pseudoscalar(2)
    assert i2 * i2 == -one
    assert MultiVector.unit_pseudoscalar_squared(2) == -one
    i3: MultiVector = MultiVector.unit_pseudoscalar(3)
    assert i3 * i3 == -one
    i4: MultiVector = MultiVector.unit_pseudoscalar(4)
    assert i4 * i4 == one
    i5: MultiVector = MultiVector.unit_pseudoscalar(5)
    assert i5 * i5 == one
    i6: MultiVector = MultiVector.unit_pseudoscalar(6)
    assert i6 * i6 == -one
    i7: MultiVector = MultiVector.unit_pseudoscalar(7)
    assert i7 * i7 == -one
    i8: MultiVector = MultiVector.unit_pseudoscalar(8)
    assert i8 * i8 == one
    i9: MultiVector = MultiVector.unit_pseudoscalar(9)
    assert i9 * i9 == one
    i10: MultiVector = MultiVector.unit_pseudoscalar(10)
    assert i10 * i10 == -one
    i11: MultiVector = MultiVector.unit_pseudoscalar(11)
    assert i11 * i11 == -one
    i12: MultiVector = MultiVector.unit_pseudoscalar(12)
    assert i12 * i12 == one
    i13: MultiVector = MultiVector.unit_pseudoscalar(13)
    assert i13 * i13 == one
    i14: MultiVector = MultiVector.unit_pseudoscalar(14)
    assert i14 * i14 == -one
    i15: MultiVector = MultiVector.unit_pseudoscalar(14)
    assert i15 * i15 == -one


def test_multivector_reverse() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert (a * a).reverse() == a * a

    b: MultiVector = 5 * e_1 + 10 * e_2
    assert (b * a).reverse() == a * b

    assert (sym_vec2_2 * sym_vec2_1).reverse() == sym_vec2_1 * sym_vec2_2


def test_multivector_reverse_3d() -> None:
    assert (sym_vec3_2 * sym_vec3_1).reverse() == sym_vec3_1 * sym_vec3_2


def test_multivector_inverse() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert a.magnitude_squared() == 25
    assert a.magnitude_squared() * a.inverse() == a

    assert sym_vec2_1.magnitude_squared() * sym_vec2_1.inverse() == sym_vec2_1
    assert (sym_vec2_1.inverse() * sym_vec2_1).scalar_part() == 1

    assert sym_vec3_1.magnitude_squared() * sym_vec3_1.inverse() == sym_vec3_1
    assert (sym_vec3_1.inverse() * sym_vec3_1) == one

    plane: MultiVector = sym_vec_plane
    assert (plane * plane.inverse()) == one
    assert (plane.inverse() * plane) == one


def test_project_and_reject() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2
    assert MultiVector.project(onto=e_1)(a) == 3 * e_1
    assert MultiVector.reject(away_from=e_1)(a) == 4 * e_2

    assert MultiVector.project(onto=[e_1, e_2])(a) == a
    assert MultiVector.reject(away_from=[e_1, e_2])(a) == zero

    assert MultiVector.project(onto=e_1)(2 * a) == 6 * e_1
    assert MultiVector.reject(away_from=e_1)(2 * a) == 8 * e_2

    assert MultiVector.project(onto=2 * e_1)(a) == 3 * e_1
    assert MultiVector.reject(away_from=2 * e_1)(a) == 4 * e_2

    parallel_to_vec1: MultiVector = MultiVector.project(onto=sym_vec2_1)(
        sym_vec2_2
    )
    perp_to_vec1: MultiVector = MultiVector.reject(away_from=sym_vec2_1)(
        sym_vec2_2
    )
    assert sym_vec2_2 == (parallel_to_vec1 + perp_to_vec1)


def test_reflect() -> None:
    a: MultiVector = 3 * e_1 + 4 * e_2 + 5 * e_3

    # reflect across vectors
    assert MultiVector.reflect(across=e_1)(a) == 3 * e_1 + -4 * e_2 + -5 * e_3
    assert MultiVector.reflect(across=e_2)(a) == -3 * e_1 + 4 * e_2 + -5 * e_3
    assert MultiVector.reflect(across=e_3)(a) == -3 * e_1 + -4 * e_2 + 5 * e_3

    # reflect across planes
    assert (
        MultiVector.reflect(across=[e_1, e_2])(a)
        == 3 * e_1 + 4 * e_2 + -5 * e_3
    )
    assert (
        MultiVector.reflect(across=e_1 * e_2)(a) == 3 * e_1 + 4 * e_2 + -5 * e_3
    )
    assert (
        MultiVector.reflect(across=e_1 ^ e_2)(a) == 3 * e_1 + 4 * e_2 + -5 * e_3
    )

    assert (
        MultiVector.reflect(across=[e_2, e_3])(a)
        == -3 * e_1 + 4 * e_2 + 5 * e_3
    )
    assert (
        MultiVector.reflect(across=[e_3, e_1])(a)
        == 3 * e_1 + -4 * e_2 + 5 * e_3
    )
    assert (
        MultiVector.reflect(across=[e_1, e_3])(a)
        == 3 * e_1 + -4 * e_2 + 5 * e_3
    )


def test_normalize() -> None:
    assert sym_vec2_1.normalize() == sym_vec2_1 * (abs(sym_vec2_1) ** (-1))  # type: ignore
    assert sym_vec3_1.normalize() == sym_vec3_1 * (abs(sym_vec3_1) ** (-1))  # type: ignore


def test_rotate() -> None:
    # rotate across planes
    a: MultiVector = 3 * e_1 + 4 * e_2 + 5 * e_3
    # rotate across e_1 e_2 plane
    assert (
        MultiVector.rotate(from_vector=e_1, to_vector=e_2)(a)
        == -4 * e_1 + 3 * e_2 + 5 * e_3
    )
    assert (
        MultiVector.rotate(from_vector=e_2, to_vector=e_1)(a)
        == 4 * e_1 - 3 * e_2 + 5 * e_3
    )
    # rotate across e_2 e_3 plane
    b: MultiVector = 5 * e_1 + 3 * e_2 + 4 * e_3
    assert (
        MultiVector.rotate(from_vector=e_2, to_vector=e_3)(b)
        == 5 * e_1 + -4 * e_2 + 3 * e_3
    )
    assert (
        MultiVector.rotate(from_vector=e_3, to_vector=e_2)(b)
        == 5 * e_1 + 4 * e_2 - 3 * e_3
    )
    # rotate across e_3 e_1 plane
    c: MultiVector = 4 * e_1 + 5 * e_2 + 3 * e_3
    assert (
        MultiVector.rotate(from_vector=e_3, to_vector=e_1)(c)
        == 3 * e_1 + 5 * e_2 + -4 * e_3
    )
    assert (
        MultiVector.rotate(from_vector=e_1, to_vector=e_3)(c)
        == -3 * e_1 + 5 * e_2 + 4 * e_3
    )


def test_rotate_angle() -> None:
    # rotate across planes
    a: MultiVector = 3 * e_1 + 4 * e_2 + 5 * e_3
    # rotate across e_1 e_2 plane
    #   pi /2
    assert (
        MultiVector.rotate(
            from_vector=e_1, to_vector=e_2, angle_in_radians=sympy.pi / 2
        )(a)
        == -4 * e_1 + 3 * e_2 + 5 * e_3
    )
    #   pi
    assert (
        MultiVector.rotate(
            from_vector=e_1, to_vector=e_2, angle_in_radians=sympy.pi
        )(a)
        == -3 * e_1 + -4 * e_2 + 5 * e_3
    )
    #   3pi /2
    assert (
        MultiVector.rotate(
            from_vector=e_1, to_vector=e_2, angle_in_radians=3 * sympy.pi / 2
        )(a)
        == 4 * e_1 + -3 * e_2 + 5 * e_3
    )
    #   2pi
    assert (
        MultiVector.rotate(
            from_vector=e_1, to_vector=e_2, angle_in_radians=2 * sympy.pi
        )(a)
        == 3 * e_1 + 4 * e_2 + 5 * e_3
    )
    #   pi /4
    assert (
        MultiVector.rotate(
            from_vector=e_1, to_vector=e_2, angle_in_radians=sympy.pi / 4
        )(1 * e_1 + 0 * e_2 + 5 * e_3)
        == (sympy.sqrt(2) / 2) * e_1 + (sympy.sqrt(2) / 2) * e_2 + 5 * e_3
    )

    # show size of vectors in plane does not matter
    #   pi /2
    assert (
        MultiVector.rotate(
            from_vector=10 * e_1,
            to_vector=50 * e_2,
            angle_in_radians=sympy.pi / 2,
        )(a)
        == -4 * e_1 + 3 * e_2 + 5 * e_3
    )


# def wrap_vec1_test(
#     fn: mu.InvertibleFunction, input_val: float, output_val: float
# ):
#     out: mu.Vector = fn(mu.Vector1D(input_val))
#     assert out.isclose(mu.Vector1D(output_val))


# # doc-region-begin translate test
# def test__vec1_translate():
#     fn: mu.InvertibleFunction = mu.translate(mu.Vector1D(2))
#     fn_inv: mu.InvertibleFunction = mu.inverse(fn)

#     input_output_pairs = [
#         [-3, -1],
#         [-2, 0],
#         [-1, 1],
#         [0, 2],
#         [1, 3],
#         [2, 4],
#         [3, 5],
#         [4, 6],
#     ]
#     for input_val, output_val in input_output_pairs:
#         wrap_vec1_test(fn, input_val, output_val)
#         wrap_vec1_test(fn_inv, output_val, input_val)


# # doc-region-end translate test


# def test__vec1_mx_plus_b():
#     m = 5
#     b = 2

#     fn: mu.InvertibleFunction = mu.compose(
#         [mu.translate(mu.Vector1D(b)), mu.uniform_scale(m)]
#     )
#     fn_inv: mu.InvertibleFunction = mu.inverse(fn)

#     input_output_pairs = [
#         [-3, -13],
#         [-2, -8],
#         [-1, -3],
#         [0, 2],
#         [1, 7],
#         [2, 12],
#         [3, 17],
#         [4, 22],
#     ]

#     for input_val, output_val in input_output_pairs:
#         wrap_vec1_test(fn, input_val, output_val)
#         wrap_vec1_test(fn_inv, output_val, input_val)


# def test_vec1_uniform_scale():
#     fn: mu.InvertibleFunction = mu.uniform_scale(4)
#     fn_inv: mu.InvertibleFunction = mu.inverse(fn)

#     input_output_pairs = [
#         [-3, -12],
#         [-2, -8],
#         [-1, -4],
#         [0, 0],
#         [1, 4],
#         [2, 8],
#         [3, 12],
#         [4, 16],
#     ]

#     for input_val, output_val in input_output_pairs:
#         wrap_vec1_test(fn, input_val, output_val)
#         wrap_vec1_test(fn_inv, output_val, input_val)


# def test_vec1_tempature_conversion():
#     def test_vec1_vector1d_function(
#         fn: mu.InvertibleFunction,
#         input_output_pairs: list[list[float]],
#     ):
#         for input_val, output_val in input_output_pairs:
#             assert fn(mu.Vector1D(input_val)).isclose(mu.Vector1D(output_val))
#             assert mu.inverse(fn)(mu.Vector1D(output_val)).isclose(
#                 mu.Vector1D(input_val)
#             )

#     # doc-region-begin temperature functions
#     celsius_to_kelvin: mu.InvertibleFunction = mu.translate(mu.Vector1D(273.15))
#     fahrenheit_to_celsius: mu.InvertibleFunction = mu.compose(
#         [mu.uniform_scale(5.0 / 9.0), mu.translate(mu.Vector1D(-32.0))]
#     )
#     fahrenheit_to_kelvin: mu.InvertibleFunction = mu.compose(
#         [celsius_to_kelvin, fahrenheit_to_celsius]
#     )
#     kelvin_to_celsius: mu.InvertibleFunction = mu.inverse(celsius_to_kelvin)
#     celsius_to_fahrenheit: mu.InvertibleFunction = mu.inverse(
#         fahrenheit_to_celsius
#     )
#     kelvin_to_fahrenheit: mu.InvertibleFunction = mu.compose(
#         [celsius_to_fahrenheit, kelvin_to_celsius]
#     )

#     # doc-region-end temperature functions

#     test_vec1_vector1d_function(
#         celsius_to_kelvin,
#         [
#             [0.0, 273.15],
#             [100.0, 373.15],
#         ],
#     )
#     test_vec1_vector1d_function(
#         fahrenheit_to_celsius,
#         [
#             [32.0, 0.0],
#             [212.0, 100.0],
#         ],
#     )
#     test_vec1_vector1d_function(
#         fahrenheit_to_kelvin,
#         [
#             [32.0, 273.15],
#             [212.0, 373.15],
#         ],
#     )
#     test_vec1_vector1d_function(
#         kelvin_to_celsius,
#         [
#             [273.15, 0.0],
#             [373.15, 100.0],
#         ],
#     )
#     test_vec1_vector1d_function(
#         celsius_to_fahrenheit,
#         [
#             [0.0, 32.0],
#             [100.0, 212.0],
#         ],
#     )
#     test_vec1_vector1d_function(
#         kelvin_to_fahrenheit,
#         [
#             [273.15, 32.0],
#             [373.15, 212.0],
#         ],
#     )


# def wrap_vec2_test(
#     fn: mu.InvertibleFunction, input_val: list[float], output_val: list[float]
# ):
#     out: mu.Vector = fn(mu.Vector2D(*input_val))
#     assert out.isclose(mu.Vector2D(*output_val))

#     for input_val, output_val in input_output_pairs:
#         assert mu.Vector2D(*output_val).isclose(
#             mu.Vector2D(*input_val[0]) + mu.Vector2D(*input_val[1])
#         )


# def test_vec2_is_parallel():
#     input_output_pairs = [
#         [[(1.0, 0.0), (2.0, 0.0)], True],
#         [[(0.0, 5.0), (0.0, 1.0)], True],
#         [[(1.0, 5.0), (0.0, 1.0)], False],
#         [[(0.0, 5.0), (0.2, 1.0)], False],
#         [[(0.0, 5.0), (1.2, 0.0)], False],
#     ]

#     for input_val, output_val in input_output_pairs:
#         assert output_val == mu.is_parallel(
#             mu.Vector2D(*input_val[0]), mu.Vector2D(*input_val[1])
#         )


# def test_vec2_is_counter_clockwise():
#     input_output_pairs = [
#         [[(1.0, 0.0), (0.0, 1.0)], True],
#         [[(1.0, 0.0), (0.0, -0.1)], False],
#         [[(0.0, 1.0), (-0.1, 1.0)], True],
#         [[(0.0, 1.0), (10.1, 1.0)], False],
#         [[(-1.0, 0.0), (-1.0, 0.1)], False],
#         [[(-1.0, 0.0), (-1.0, -0.1)], True],
#         [[(0.0, -1.0), (-0.1, -1.0)], False],
#         [[(0.0, -1.0), (0.1, -1.0)], True],
#     ]

#     for input_val, output_val in input_output_pairs:
#         assert output_val == mu.is_counter_clockwise(
#             mu.Vector2D(*input_val[0]), mu.Vector2D(*input_val[1])
#         )


# def test_vec2_compose():
#     fn: mu.InvertibleFunction = mu.translate(mu.Vector2D(x=2, y=3))
#     fn_inv: mu.InvertibleFunction = mu.inverse(fn)

#     identity_fn: mu.InvertibleFunction = mu.compose([fn_inv, fn])

#     input_output_pairs = [
#         [[0, 0], [0, 0]],
#         [[1, 0], [1, 0]],
#         [[0, 1], [0, 1]],
#     ]

#     for input_val, output_val in input_output_pairs:
#         wrap_vec2_test(identity_fn, input_val, output_val)


# def test_vec3_rotate_x():
#     fn: mu.InvertibleFunction = mu.rotate_x(math.radians(53.130102))
#     fn_inv: mu.InvertibleFunction = mu.inverse(fn)

#     input_output_pairs = [
#         [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
#         [[0.0, 5.0, 0.0], [0.0, 3.0, 4.0]],
#         [[0.0, 0.0, 5.0], [0.0, -4.0, 3.0]],
#     ]

#     for input_val, output_val in input_output_pairs:
#         wrap_vec3_test(fn, input_val, output_val)
#         wrap_vec3_test(fn_inv, output_val, input_val)


# def test_vec3_rotate_y():
#     fn: mu.InvertibleFunction = mu.rotate_y(math.radians(53.130102))
#     fn_inv: mu.InvertibleFunction = mu.inverse(fn)

#     input_output_pairs = [
#         [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
#         [[0.0, 0.0, 5.0], [4.0, 0.0, 3.0]],
#         [[5.0, 0.0, 0.0], [3.0, 0.0, -4.0]],
#     ]

#     for input_val, output_val in input_output_pairs:
#         wrap_vec3_test(fn, input_val, output_val)
#         wrap_vec3_test(fn_inv, output_val, input_val)


# def test_vec3_rotate_z():
#     fn: mu.InvertibleFunction = mu.rotate_z(math.radians(53.130102))
#     fn_inv: mu.InvertibleFunction = mu.inverse(fn)

#     input_output_pairs = [
#         [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
#         [[5.0, 0.0, 0.0], [3.0, 4.0, 0.0]],
#         [[0.0, 5.0, 0.0], [-4.0, 3.0, 0.0]],
#     ]

#     for input_val, output_val in input_output_pairs:
#         wrap_vec3_test(fn, input_val, output_val)
#         wrap_vec3_test(fn_inv, output_val, input_val)


# # doc-region-begin function stack examples definitions
# def test_vec3_fn_stack():
#     identity: InvertibleFunction = mu.uniform_scale(1)

#     mu.fn_stack.push(identity)
#     assert mu.Vector1D(1) == mu.fn_stack.modelspace_to_ndc_fn()(mu.Vector1D(1))

#     add_one: InvertibleFunction = mu.translate(mu.Vector1D(1))

#     mu.fn_stack.push(add_one)
#     assert mu.Vector1D(2) == mu.fn_stack.modelspace_to_ndc_fn()(
#         mu.Vector1D(1)
#     )  # x + 1 = 2

#     multiply_by_2: InvertibleFunction = mu.uniform_scale(2)

#     mu.fn_stack.push(multiply_by_2)  # (x * 2) + 1 = 3
#     assert mu.Vector1D(3) == mu.fn_stack.modelspace_to_ndc_fn()(mu.Vector1D(1))

#     add_5: InvertibleFunction = mu.translate(mu.Vector1D(5))

#     mu.fn_stack.push(add_5)  # ((x + 5) * 2) + 1 = 13
#     assert mu.Vector1D(13) == mu.fn_stack.modelspace_to_ndc_fn()(mu.Vector1D(1))

#     mu.fn_stack.pop()
#     assert mu.Vector1D(3) == mu.fn_stack.modelspace_to_ndc_fn()(
#         mu.Vector1D(1)
#     )  # (x * 2) + 1 = 3

#     mu.fn_stack.pop()
#     assert mu.Vector1D(2) == mu.fn_stack.modelspace_to_ndc_fn()(
#         mu.Vector1D(1)
#     )  # x + 1 = 2

#     mu.fn_stack.pop()
#     assert mu.Vector1D(1) == mu.fn_stack.modelspace_to_ndc_fn()(
#         mu.Vector1D(1)
#     )  # x = 1
#     # doc-region-end function stack examples definitions


# def test__doctest():
#     failureCount, testCount = doctest.testmod(mu)
#     assert 0 == failureCount
