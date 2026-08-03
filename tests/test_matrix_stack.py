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

"""Tests for ``matrix_stack.planar_shadow`` (tasks/planar-shadow-matrix.md).

The reference implementation is the fixed-function
``make_planar_shadow_matrix`` in
``ports/openglsuperbiblev4/chapt01/block/Block.py`` (itself a port of
``m3dMakePlanarShadowMatrix``). Block.py stores the matrix column-major for
``glMultMatrixf``; ``matrix_stack`` stores row-major (``M @ column_vector``),
so the faithfulness test transposes the reference before comparing.
"""

import numpy as np

from modelviewprojection.matrix_stack import (
    MatrixStack,
    get_current_matrix,
    planar_shadow,
    set_to_identity_matrix,
    translate,
)


def _reference_row_major(
    plane_eq: tuple[float, float, float, float],
    light_pos: tuple[float, float, float],
) -> np.ndarray:
    """Block.py's column-major flat (sign=+1), reinterpreted row-major.

    ``glMultMatrixf`` reads the flat buffer column-major, so
    ``M[row][col] == flat[col * 4 + row]`` -- i.e. the reshaped buffer
    transposed. This is an independent transcription of the reference, so
    matching it pins ``planar_shadow`` to the working demo's matrix.
    """
    a, b, c, d = plane_eq
    dx, dy, dz = -light_pos[0], -light_pos[1], -light_pos[2]
    # Each inner list is one column of the GL matrix (the order
    # glMultMatrixf reads). Stacking them makes a matrix whose rows are
    # those columns, so its transpose is the row-major M.
    columns = [
        [b * dy + c * dz, -a * dy, -a * dz, 0.0],
        [-b * dx, a * dx + c * dz, -b * dz, 0.0],
        [-c * dx, -c * dy, a * dx + b * dy, 0.0],
        [-d * dx, -d * dy, -d * dz, a * dx + b * dy + c * dz],
    ]
    return np.array(columns, dtype=np.float64).T


def _shadow_matrix(
    plane_eq: tuple[float, float, float, float],
    light_pos: tuple[float, float, float],
) -> np.ndarray:
    """The matrix ``planar_shadow`` post-multiplies, recovered by applying
    it to an identity model stack."""
    set_to_identity_matrix(MatrixStack.model)
    planar_shadow(MatrixStack.model, plane_eq, light_pos)
    return get_current_matrix(MatrixStack.model).astype(np.float64)


def test_matches_block_reference() -> None:
    # A generic plane and light -- nothing axis-aligned, so every entry of
    # the matrix is exercised.
    plane_eq = (0.2, 0.7, 0.5, -1.3)
    light_pos = (-80.0, 120.0, 100.0)
    got = _shadow_matrix(plane_eq, light_pos)
    want = _reference_row_major(plane_eq, light_pos)
    assert np.allclose(got, want, atol=1e-5)


def test_projects_points_onto_the_plane() -> None:
    # Plane y = 0, light straight overhead: shadows drop straight down and
    # land on y = 0 with x, z unchanged (parallel projection).
    plane_eq = (0.0, 1.0, 0.0, 0.0)
    light_pos = (0.0, 10.0, 0.0)
    m = _shadow_matrix(plane_eq, light_pos)
    for point in [(2.0, 5.0, 3.0, 1.0), (-3.0, 9.0, -1.0, 1.0)]:
        shadow = m @ np.array(point, dtype=np.float64)
        shadow = shadow / shadow[3]
        assert abs(shadow[1]) < 1e-6  # on the plane
        assert abs(shadow[0] - point[0]) < 1e-6  # x unchanged
        assert abs(shadow[2] - point[2]) < 1e-6  # z unchanged


def test_shadow_lands_on_arbitrary_plane() -> None:
    # A tilted plane and off-axis light: every shadowed point must satisfy
    # the plane equation a x + b y + c z + d = 0.
    plane_eq = (0.3, 0.8, -0.5, 2.0)
    light_pos = (4.0, 9.0, -2.0)
    m = _shadow_matrix(plane_eq, light_pos)
    a, b, c, d = plane_eq
    for point in [(1.0, 2.0, 3.0, 1.0), (-5.0, 4.0, 6.0, 1.0)]:
        shadow = m @ np.array(point, dtype=np.float64)
        shadow = shadow / shadow[3]
        residual = a * shadow[0] + b * shadow[1] + c * shadow[2] + d
        assert abs(residual) < 1e-5


def test_matrix_is_rank_deficient() -> None:
    # The whole point: the shadow collapses 3D onto a 2D plane, so the
    # matrix is singular (rank 3) and has no inverse -- it is not a Cayley
    # graph edge.
    m = _shadow_matrix((0.2, 0.7, 0.5, -1.3), (-80.0, 120.0, 100.0))
    assert abs(np.linalg.det(m)) < 1e-4
    assert np.linalg.matrix_rank(m) == 3


def test_post_multiplies_current_matrix() -> None:
    # planar_shadow composes onto the current matrix like
    # glMultMatrixf(shadow): the result is current @ shadow, not shadow
    # alone.
    plane_eq = (0.0, 1.0, 0.0, 0.0)
    light_pos = (0.0, 10.0, 0.0)
    shadow_only = _reference_row_major(plane_eq, light_pos)

    set_to_identity_matrix(MatrixStack.model)
    translate(MatrixStack.model, 1.0, 2.0, 3.0)
    current = get_current_matrix(MatrixStack.model).astype(np.float64).copy()
    planar_shadow(MatrixStack.model, plane_eq, light_pos)
    got = get_current_matrix(MatrixStack.model).astype(np.float64)
    assert np.allclose(got, current @ shadow_only, atol=1e-5)
