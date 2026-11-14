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

"""Plain tests for the graphics-specific math that lives in mvp's
``mathutils`` on top of gacalc.  The vector algebra and the core transform
layer are gacalc's and are tested there.

Most of mvp's own math is tested by the doctests in its docstrings
(``mathutils`` and ``framebuffer.softwarerendering``), which ``make test``
collects.  What stays here has no doctest home or needs pytest machinery:

- ``rotate`` and ``rotate_x``/``_y``/``_z`` are module-level
  ``plane_rotation`` closures documented by book-region comments, not
  docstrings, and their checks are tolerance-based;
- the function-stack test is the source of a book ``literalinclude``;
- the ``to_matrix`` tests use ``numpy.allclose`` and ``pytest.raises``.
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

from modelviewprojection.mathutils import (
    fn_stack,
    perspective,
    rotate,
    rotate_x,
    rotate_y,
    rotate_z,
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
# Function stack                                                              #
# --------------------------------------------------------------------------- #


# doc-region-begin function stack examples definitions
def test_function_stack_push_pop() -> None:
    fn_stack.clear()
    e_1: g3.Vector = g3.Vector.e_1

    fn_stack.push(uniform_scale(m=1.0))
    assert fn_stack.modelspace_to_ndc_fn()(e_1).isclose(
        e_1, rel_tol=1e-5, abs_tol=1e-5
    )

    fn_stack.push(translate(b=e_1))  # x + 1
    assert fn_stack.modelspace_to_ndc_fn()(e_1).isclose(
        2 * e_1, rel_tol=1e-5, abs_tol=1e-5
    )

    fn_stack.push(uniform_scale(m=2.0))  # (x * 2) + 1
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
