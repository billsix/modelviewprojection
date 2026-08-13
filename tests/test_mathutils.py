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

"""Tests for the graphics-specific math that lives in mvp's ``mathutils`` on top
of gacalc.  The vector algebra and the core transform layer (add/sub/scale/
translate/compose/inverse and the at/steps animation layer) are gacalc's and are
tested there; here we exercise only what mvp builds: the angle/axis rotations,
the ortho/perspective projections, the plane-geometry helpers, the 2D
orientation predicates, and the function stack.
"""

import math

import gacalc.g2 as g2
import gacalc.g3 as g3
import numpy as np
import pytest
import sympy
from gacalc.transforms import (
    InvertibleFunction,
    Linearity,
    inverse,
    to_matrix,
    translate,
    uniform_scale,
)

from modelviewprojection.framebuffer.softwarerendering import (
    is_clockwise,
    is_counter_clockwise,
    is_parallel_and_same_orientation,
)
from modelviewprojection.mathutils import (
    abs_sin,
    cosine,
    distance_to_plane,
    find_normal,
    fn_stack,
    ortho,
    perspective,
    plane_equation,
    rotate,
    rotate_around,
    rotate_x,
    rotate_y,
    rotate_z,
    sine,
)


def v2(x: float, y: float) -> g2.Vector:
    return x * g2.Vector.e_1 + y * g2.Vector.e_2


def v3(x: float, y: float, z: float) -> g3.Vector:
    return x * g3.Vector.e_1 + y * g3.Vector.e_2 + z * g3.Vector.e_3


# --------------------------------------------------------------------------- #
# 2D rotation                                                                 #
# --------------------------------------------------------------------------- #


def test_rotate_quarter_turn() -> None:
    # rotate_90_degrees was retired 2026-07-09; a quarter turn is just
    # rotate(pi/2) on the module-level plane factory.
    fn: InvertibleFunction[g2.Vector] = rotate(math.radians(90.0))
    fn_inv: InvertibleFunction[g2.Vector] = inverse(fn)
    pairs: list[tuple[g2.Vector, g2.Vector]] = [
        (g2.Vector.zero(), g2.Vector.zero()),
        (g2.Vector.e_1, g2.Vector.e_2),
        (g2.Vector.e_2, -1 * g2.Vector.e_1),
        (-1 * g2.Vector.e_1, -1 * g2.Vector.e_2),
        (-1 * g2.Vector.e_2, g2.Vector.e_1),
    ]
    inp: g2.Vector
    out: g2.Vector
    for inp, out in pairs:
        assert fn(inp).isclose(out, rel_tol=1e-5, abs_tol=1e-5)
        assert fn_inv(out).isclose(inp, rel_tol=1e-5, abs_tol=1e-5)


def test_rotate_3_4_5() -> None:
    fn: InvertibleFunction[g2.Vector] = rotate(math.atan2(4, 3))
    assert fn(v2(5, 0)).isclose(v2(3, 4), rel_tol=1e-5, abs_tol=1e-5)
    assert inverse(fn)(v2(3, 4)).isclose(v2(5, 0), rel_tol=1e-5, abs_tol=1e-5)


def test_rotate_is_linear_and_animatable() -> None:
    fn: InvertibleFunction[g2.Vector] = rotate(math.radians(90.0))
    assert fn.linearity is Linearity.LINEAR
    # at(0) is identity, at(1) the full rotation
    assert fn.at(0.0)(g2.Vector.e_1).isclose(
        g2.Vector.e_1, rel_tol=1e-5, abs_tol=1e-5
    )
    assert fn.at(1.0)(g2.Vector.e_1).isclose(
        g2.Vector.e_2, rel_tol=1e-5, abs_tol=1e-5
    )


def test_rotate_around_a_point() -> None:
    # rotating the point itself about itself is a no-op
    center: g2.Vector = v2(2, 0)
    fn: InvertibleFunction[g2.Vector] = rotate_around(
        math.radians(90.0), center
    )
    assert fn(center).isclose(center, rel_tol=1e-5, abs_tol=1e-5)
    # a point one unit +x of center swings to one unit +y of center
    assert fn(center + g2.Vector.e_1).isclose(
        center + g2.Vector.e_2, rel_tol=1e-5, abs_tol=1e-5
    )


# --------------------------------------------------------------------------- #
# 3D axis rotation                                                            #
# --------------------------------------------------------------------------- #


def test_rotate_x() -> None:
    fn: InvertibleFunction[g3.Vector] = rotate_x(math.atan2(4, 3))
    along_axis: g3.Vector = g3.Vector.e_1
    pairs: list[tuple[g3.Vector, g3.Vector]] = [
        (g3.Vector.zero(), g3.Vector.zero()),
        (along_axis, along_axis),  # the axis is fixed
        (along_axis + v3(0, 5, 0), along_axis + v3(0, 3, 4)),
        (along_axis + v3(0, 0, 5), along_axis + v3(0, -4, 3)),
    ]
    inp: g3.Vector
    out: g3.Vector
    for inp, out in pairs:
        assert fn(inp).isclose(out, rel_tol=1e-5, abs_tol=1e-5)
        assert inverse(fn)(out).isclose(inp, rel_tol=1e-5, abs_tol=1e-5)


def test_rotate_y() -> None:
    fn: InvertibleFunction[g3.Vector] = rotate_y(math.atan2(4, 3))
    along_axis: g3.Vector = g3.Vector.e_2
    pairs: list[tuple[g3.Vector, g3.Vector]] = [
        (along_axis, along_axis),
        (along_axis + v3(0, 0, 5), along_axis + v3(4, 0, 3)),
        (along_axis + v3(5, 0, 0), along_axis + v3(3, 0, -4)),
    ]
    inp: g3.Vector
    out: g3.Vector
    for inp, out in pairs:
        assert fn(inp).isclose(out, rel_tol=1e-5, abs_tol=1e-5)
        assert inverse(fn)(out).isclose(inp, rel_tol=1e-5, abs_tol=1e-5)


def test_rotate_z() -> None:
    fn: InvertibleFunction[g3.Vector] = rotate_z(math.atan2(4, 3))
    along_axis: g3.Vector = g3.Vector.e_3
    pairs: list[tuple[g3.Vector, g3.Vector]] = [
        (along_axis, along_axis),
        (along_axis + v3(5, 0, 0), along_axis + v3(3, 4, 0)),
        (along_axis + v3(0, 5, 0), along_axis + v3(-4, 3, 0)),
    ]
    inp: g3.Vector
    out: g3.Vector
    for inp, out in pairs:
        assert fn(inp).isclose(out, rel_tol=1e-5, abs_tol=1e-5)
        assert inverse(fn)(out).isclose(inp, rel_tol=1e-5, abs_tol=1e-5)


# --------------------------------------------------------------------------- #
# Orientation predicates                                                      #
# --------------------------------------------------------------------------- #


def test_cosine_and_sine() -> None:
    assert math.isclose(cosine(g2.Vector.e_1, g2.Vector.e_1), 1.0)
    assert math.isclose(cosine(g2.Vector.e_1, g2.Vector.e_2), 0.0, abs_tol=1e-9)
    assert math.isclose(sine(g2.Vector.e_1, g2.Vector.e_2), 1.0)
    assert math.isclose(sine(g2.Vector.e_1, g2.Vector.e_1), 0.0, abs_tol=1e-9)


def test_is_parallel_and_same_orientation() -> None:
    cases: list[tuple[tuple[float, float], tuple[float, float], bool]] = [
        ((1, 0), (2, 0), True),
        ((0, 5), (0, 1), True),
        ((1, 5), (0, 1), False),
        ((0, 5), (0.2, 1), False),
    ]
    a: tuple[float, float]
    b: tuple[float, float]
    expected: bool
    for a, b, expected in cases:
        assert is_parallel_and_same_orientation(v2(*a), v2(*b)) is expected


def test_is_counter_clockwise_and_clockwise() -> None:
    # e_2 is CCW from e_1
    assert is_counter_clockwise(g2.Vector.e_1, g2.Vector.e_2)
    assert not is_clockwise(g2.Vector.e_1, g2.Vector.e_2)
    # the reverse pair is clockwise
    assert is_clockwise(g2.Vector.e_2, g2.Vector.e_1)
    assert not is_counter_clockwise(g2.Vector.e_2, g2.Vector.e_1)


def test_abs_sin() -> None:
    # perpendicular unit vectors -> |sin| = 1; parallel -> 0
    assert math.isclose(abs_sin(g3.Vector.e_1, g3.Vector.e_2), 1.0)
    assert math.isclose(abs_sin(g3.Vector.e_1, v3(2, 0, 0)), 0.0, abs_tol=1e-9)


# --------------------------------------------------------------------------- #
# Plane geometry (cross = wedge then dual)                                     #
# --------------------------------------------------------------------------- #


def test_find_normal_ccw_is_plus_z() -> None:
    n: g3.Vector = find_normal(v3(0, 0, 0), v3(1, 0, 0), v3(0, 1, 0))
    assert n.isclose(g3.Vector.e_3, rel_tol=1e-5, abs_tol=1e-5)


def test_find_normal_cw_flips_sign() -> None:
    p1, p2, p3 = v3(0, 0, 0), v3(1, 0, 0), v3(0, 1, 0)
    n_ccw: g3.Vector = find_normal(p1, p2, p3)
    n_cw: g3.Vector = find_normal(p1, p3, p2)
    assert n_ccw.isclose(-1 * n_cw, rel_tol=1e-5, abs_tol=1e-5)


def test_find_normal_unnormalized_magnitude() -> None:
    # |cross| == 2 * triangle area; a 1x1 right triangle has area 0.5
    n1: g3.Vector = find_normal(v3(0, 0, 0), v3(1, 0, 0), v3(0, 1, 0))
    assert math.isclose(float(abs(n1)), 1.0)
    # a 2x2 right triangle has area 2 -> |normal| = 4
    n2: g3.Vector = find_normal(v3(0, 0, 0), v3(2, 0, 0), v3(0, 2, 0))
    assert math.isclose(float(abs(n2)), 4.0)


def test_plane_equation_points_satisfy_it() -> None:
    # plane x + y + z = 1 through (1,0,0),(0,1,0),(0,0,1)
    p1, p2, p3 = v3(1, 0, 0), v3(0, 1, 0), v3(0, 0, 1)
    normal, d = plane_equation(p1, p2, p3)
    p: g3.Vector
    for p in (p1, p2, p3):
        assert math.isclose(
            float(normal.dot(p).scalar_part()) + d, 0.0, abs_tol=1e-6
        )
    # unit normal
    assert math.isclose(float(abs(normal)), 1.0, abs_tol=1e-6)


def test_distance_to_plane_signed() -> None:
    plane: tuple[g3.Vector, float] = plane_equation(
        v3(0, 0, 0), v3(1, 0, 0), v3(0, 1, 0)
    )  # XY, +Z
    assert math.isclose(distance_to_plane(v3(0, 0, 5), plane), 5.0)
    assert math.isclose(distance_to_plane(v3(0, 0, -3), plane), -3.0)
    # tangential motion doesn't change the distance
    assert math.isclose(distance_to_plane(v3(7, -2, 4), plane), 4.0)


# --------------------------------------------------------------------------- #
# Projections                                                                 #
# --------------------------------------------------------------------------- #


def test_ortho_maps_box_to_ndc() -> None:
    fn: InvertibleFunction[g3.Vector] = ortho(
        left=-2, right=2, bottom=-4, top=4, near=-1, far=-9
    )
    # the box centre maps to the NDC origin
    assert fn(v3(0, 0, -5)).isclose(
        g3.Vector.zero(), rel_tol=1e-5, abs_tol=1e-5
    )
    # +x face -> +1 in x; +y face -> +1 in y
    assert math.isclose(float(fn(v3(2, 0, -5)).coeff_e_1), 1.0)
    assert math.isclose(float(fn(v3(0, 4, -5)).coeff_e_2), 1.0)
    assert fn.linearity is Linearity.AFFINE


def test_ortho_is_invertible() -> None:
    fn: InvertibleFunction[g3.Vector] = ortho(
        left=-2, right=2, bottom=-4, top=4, near=-1, far=-9
    )
    p: g3.Vector = v3(1.5, -3.0, -7.0)
    assert inverse(fn)(fn(p)).isclose(p, rel_tol=1e-5, abs_tol=1e-5)


def test_perspective_is_nonlinear_and_invertible() -> None:
    fn: InvertibleFunction[g3.Vector] = perspective(
        field_of_view=45.0, aspect_ratio=1.0, near_z=-0.1, far_z=-1000.0
    )
    assert fn.linearity is Linearity.NONLINEAR
    p: g3.Vector = v3(1.0, 2.0, -5.0)
    assert inverse(fn)(fn(p)).isclose(p, rel_tol=1e-5, abs_tol=1e-5)


# --------------------------------------------------------------------------- #
# Function stack                                                              #
# --------------------------------------------------------------------------- #


# doc-region-begin function stack examples definitions
def test_function_stack_push_pop() -> None:
    fn_stack.clear()
    e_1: g3.Vector = g3.Vector.e_1

    fn_stack.push(uniform_scale(1.0))
    assert fn_stack.modelspace_to_ndc_fn()(e_1).isclose(
        e_1, rel_tol=1e-5, abs_tol=1e-5
    )

    fn_stack.push(translate(e_1))  # x + 1
    assert fn_stack.modelspace_to_ndc_fn()(e_1).isclose(
        2 * e_1, rel_tol=1e-5, abs_tol=1e-5
    )

    fn_stack.push(uniform_scale(2.0))  # (x * 2) + 1
    assert fn_stack.modelspace_to_ndc_fn()(e_1).isclose(
        3 * e_1, rel_tol=1e-5, abs_tol=1e-5
    )

    fn_stack.pop()
    assert fn_stack.modelspace_to_ndc_fn()(e_1).isclose(
        2 * e_1, rel_tol=1e-5, abs_tol=1e-5
    )
    fn_stack.pop()
    assert fn_stack.modelspace_to_ndc_fn()(e_1).isclose(
        e_1, rel_tol=1e-5, abs_tol=1e-5
    )
    fn_stack.clear()
    # doc-region-end function stack examples definitions


# --------------------------------------------------------------------------- #
# mvp rotations <-> gacalc to_matrix                                          #
# --------------------------------------------------------------------------- #


def test_to_matrix_of_rotate_z_is_homogeneous_rotation() -> None:
    # a linear 3D map is still a 4x4 with a zero translation column.
    transform_matrix: np.ndarray | sympy.Matrix = to_matrix(
        rotate_z(math.radians(90.0)), g3.Vector
    )
    assert transform_matrix.shape == (4, 4)
    assert np.allclose(transform_matrix[:3, 3], [0, 0, 0])  # zero translation
    # rotate_z(90): e_1 -> e_2 (column-vector premultiply convention)
    assert np.allclose(
        transform_matrix @ np.array([1, 0, 0, 1], dtype=np.float32),
        [0, 1, 0, 1],
        atol=1e-6,
    )
    # e_3 is fixed
    assert np.allclose(
        transform_matrix @ np.array([0, 0, 1, 1], dtype=np.float32),
        [0, 0, 1, 1],
        atol=1e-6,
    )


def test_to_matrix_perspective_raises() -> None:
    with pytest.raises(ValueError):
        to_matrix(perspective(45.0, 1.0, -0.1, -1000.0), g3.Vector)
