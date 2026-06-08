# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

"""Math for the ModelViewProjection course.

The vector algebra and the invertible-function transform layer now come from the
**gacalc** geometric-algebra library (``Vector2`` / ``Vector3``,
``InvertibleFunction``, ``compose`` / ``inverse`` / ``translate`` /
``uniform_scale`` / ``scale_non_uniform``, the ``at`` / ``steps`` animation layer,
and the ``Linearity`` tag).  They are re-exported here so the course can keep
importing them from ``modelviewprojection.mathutils``.

What lives *here* is the graphics-specific math that gacalc deliberately does not
carry: angle-based 2D/axis rotations (built on top of gacalc vectors), the
``ortho`` / ``perspective`` projections, the plane-geometry helpers
(``find_normal`` via the geometric-algebra ``wedge`` + ``dual``, ``plane_equation``,
``distance_to_plane``), the 2D orientation predicates, and the
``FunctionStack`` (the Python analogue of OpenGL's matrix stack).
"""

import contextlib
import dataclasses
import math
import typing

# Re-exported from gacalc: the vector representations and the transform layer.
from gacalc.base import AbstractMultiVector
from gacalc.g1 import Vector1
from gacalc.g2 import Vector2
from gacalc.g3 import Vector3
from gacalc.transforms import (
    InvertibleFunction,
    Linearity,
    compose,
    compose_intermediate_fns,
    compose_intermediate_fns_and_fn,
    identity,
    inverse,
    rotor_rotation,
    scale_non_uniform,
    to_matrix,
    translate,
    uniform_scale,
)

__all__ = [
    # re-exported from gacalc
    "AbstractMultiVector",
    "Vector1",
    "Vector2",
    "Vector3",
    "InvertibleFunction",
    "Linearity",
    "identity",
    "inverse",
    "compose",
    "compose_intermediate_fns",
    "compose_intermediate_fns_and_fn",
    "translate",
    "uniform_scale",
    "scale_non_uniform",
    "to_matrix",
    # graphics-specific, defined here on top of gacalc
    "rotate_90_degrees",
    "rotate",
    "rotate_around",
    "rotate_x",
    "rotate_y",
    "rotate_z",
    "cosine",
    "sine",
    "is_counter_clockwise",
    "is_clockwise",
    "is_parallel",
    "abs_sin",
    "find_normal",
    "plane_equation",
    "distance_to_plane",
    "ortho",
    "perspective",
    "cs_to_ndc_space_fn",
    "FunctionStack",
    "push_transformation",
    "fn_stack",
]


#: Type variable for a vector representation an ``InvertibleFunction``
#: transforms; bound to ``AbstractMultiVector``, matching gacalc's
#: ``InvertibleFunction[V]``.  Used where the type is open (the function stack).
V = typing.TypeVar("V", bound=AbstractMultiVector)


# doc-region-begin define rotate
def rotate_90_degrees() -> InvertibleFunction[Vector2]:
    # a quarter turn carries e_1 to e_2; gacalc builds the rotor and applies it.
    return rotor_rotation(
        Vector2.e_1,
        Vector2.e_2,
        latex_repr="R_{<xy90>}",
        latex_repr_inv="R_{<xy90>}^{-1}",
        interpolate=lambda t: rotate(math.radians(90.0) * t),
    )


def rotate(angle_in_radians: float) -> InvertibleFunction[Vector2]:
    # rotating by theta carries e_1 to the unit vector at angle theta; gacalc's
    # rotor_rotation builds R = rotor_from_vectors(e_1, that) and sandwiches.
    to_vector: Vector2 = (
        math.cos(angle_in_radians) * Vector2.e_1
        + math.sin(angle_in_radians) * Vector2.e_2
    )
    return rotor_rotation(
        Vector2.e_1,
        to_vector,
        latex_repr=f"R_{{<{angle_in_radians}>}}",
        latex_repr_inv=f"R_{{<{-angle_in_radians}>}}",
        interpolate=lambda t: rotate(angle_in_radians * t),
    )
    # doc-region-end define rotate


# doc-region-begin define rotate around
def rotate_around(
    angle_in_radians: float, center: Vector2
) -> InvertibleFunction[Vector2]:
    return compose([translate(center), rotate(angle_in_radians), translate(-center)])
    # doc-region-end define rotate around


def cosine(v1: AbstractMultiVector, v2: AbstractMultiVector) -> float:
    # gacalc's dot product returns a (scalar) multivector; read off its value.
    denominator: float = float(abs(v1)) * float(abs(v2))
    if denominator == 0.0:
        # the angle is undefined when either vector has zero length
        return float("nan")
    return float(v1.dot(v2).scalar_part()) / denominator


def sine(v1: Vector2, v2: Vector2) -> float:
    denominator: float = float(abs(v1)) * float(abs(v2))
    if denominator == 0.0:
        return float("nan")
    return float(rotate_90_degrees()(v1).dot(v2).scalar_part()) / denominator


# doc-region-begin counter clockwise
def is_counter_clockwise(v1: Vector2, v2: Vector2) -> bool:
    # orientation is the SIGN of the cross product  v1 x v2 = |v1||v2| sin(theta)
    # (sine's numerator).  Use it unnormalized: dividing by the magnitudes would
    # not change the sign but would blow up when either vector is zero -- e.g. a
    # rasterized pixel sitting exactly on a triangle vertex.
    return float(rotate_90_degrees()(v1).dot(v2).scalar_part()) >= 0.0
    # doc-region-end counter clockwise


# doc-region-begin clockwise
def is_clockwise(v1: Vector2, v2: Vector2) -> bool:
    # the mirror of is_counter_clockwise (the cross product the other way).  Both
    # include the cross == 0 (collinear / on-the-edge) case, so a point lying
    # exactly on an edge or vertex counts as BOTH -- which lets the rasterizer
    # light boundary pixels no matter which way the triangle is wound.
    return float(rotate_90_degrees()(v1).dot(v2).scalar_part()) <= 0.0
    # doc-region-end clockwise


# doc-region-begin parallel
def is_parallel(v1: Vector2, v2: Vector2) -> bool:
    # a zero-length vector has no direction; treat it as degenerate/collinear so
    # callers (e.g. the rasterizer's degenerate-triangle guard) get a definite
    # answer instead of dividing by a zero magnitude.
    if float(abs(v1)) == 0.0 or float(abs(v2)) == 0.0:
        return True
    return math.isclose(cosine(v1, v2), 1.0, abs_tol=0.01)
    # doc-region-end parallel


# doc-region-begin define rotate x
def rotate_x(angle_in_radians: float) -> InvertibleFunction[Vector3]:
    # rotation in the y-z plane: carry e_2 toward e_3 (the x axis, e_1, is fixed)
    to_vector: Vector3 = (
        math.cos(angle_in_radians) * Vector3.e_2
        + math.sin(angle_in_radians) * Vector3.e_3
    )
    return rotor_rotation(
        Vector3.e_2,
        to_vector,
        latex_repr=f"RX_{{<{angle_in_radians}>}}",
        latex_repr_inv=f"RX_{{<{-angle_in_radians}>}}",
        interpolate=lambda t: rotate_x(angle_in_radians * t),
    )
    # doc-region-end define rotate x


# doc-region-begin define rotate y
def rotate_y(angle_in_radians: float) -> InvertibleFunction[Vector3]:
    # rotation in the z-x plane: carry e_3 toward e_1 (the y axis, e_2, is fixed)
    to_vector: Vector3 = (
        math.cos(angle_in_radians) * Vector3.e_3
        + math.sin(angle_in_radians) * Vector3.e_1
    )
    return rotor_rotation(
        Vector3.e_3,
        to_vector,
        latex_repr=f"RY_{{<{angle_in_radians}>}}",
        latex_repr_inv=f"RY_{{<{-angle_in_radians}>}}",
        interpolate=lambda t: rotate_y(angle_in_radians * t),
    )
    # doc-region-end define rotate y


# doc-region-begin define rotate z
def rotate_z(angle_in_radians: float) -> InvertibleFunction[Vector3]:
    # rotation in the x-y plane: carry e_1 toward e_2 (the z axis, e_3, is fixed)
    to_vector: Vector3 = (
        math.cos(angle_in_radians) * Vector3.e_1
        + math.sin(angle_in_radians) * Vector3.e_2
    )
    return rotor_rotation(
        Vector3.e_1,
        to_vector,
        latex_repr=f"RZ_{{<{angle_in_radians}>}}",
        latex_repr_inv=f"RZ_{{<{-angle_in_radians}>}}",
        interpolate=lambda t: rotate_z(angle_in_radians * t),
    )
    # doc-region-end define rotate z


def abs_sin(v1: Vector3, v2: Vector3) -> float:
    # |a x b| == |a ^ b| (the magnitude of the bivector they span)
    return float(abs(v1 ^ v2)) / (float(abs(v1)) * float(abs(v2)))


# doc-region-begin define find normal
def find_normal(p1: Vector3, p2: Vector3, p3: Vector3) -> Vector3:
    """Surface normal of the triangle :math:`(p_1, p_2, p_3)`.

    In geometric algebra the cross product is the **dual of the wedge**:
    :math:`a \\times b = (a \\wedge b)^{*}`.  The two edge vectors
    :math:`p_2 - p_1` and :math:`p_3 - p_1` span a bivector; its dual is the
    normal.  CCW winding (matching OpenGL's ``GL_CCW`` front face) gives an
    outward-facing normal in a right-handed coordinate system.

    The result is **not** normalized -- its length equals twice the area of the
    triangle.  Normalize with :func:`plane_equation` or ``n.normalize()`` for a
    unit normal.
    """
    bivector = (p2 - p1) ^ (p3 - p1)
    n = bivector.dual()
    return Vector3(
        coeff_e_1=float(n.component(Vector3.e_1)),
        coeff_e_2=float(n.component(Vector3.e_2)),
        coeff_e_3=float(n.component(Vector3.e_3)),
    )
    # doc-region-end define find normal


# doc-region-begin define plane equation
def plane_equation(
    p1: Vector3, p2: Vector3, p3: Vector3
) -> typing.Tuple[Vector3, float]:
    """The plane through three points as ``(normal, d)`` with
    :math:`\\vec{n} \\cdot P + d = 0` for all points :math:`P` on the plane.

    ``normal`` is a unit ``Vector3``; ``d`` is the signed offset from the origin
    along the normal.  Winding follows :func:`find_normal` (CCW).
    """
    n = find_normal(p1, p2, p3)
    inv_len = 1.0 / float(abs(n))
    n_unit = Vector3(
        coeff_e_1=float(n.coeff_e_1) * inv_len,
        coeff_e_2=float(n.coeff_e_2) * inv_len,
        coeff_e_3=float(n.coeff_e_3) * inv_len,
    )
    d = float(-n_unit.dot(p1).scalar_part())
    return (n_unit, d)
    # doc-region-end define plane equation


# doc-region-begin define distance to plane
def distance_to_plane(point: Vector3, plane: typing.Tuple[Vector3, float]) -> float:
    """Signed distance from ``point`` to ``plane`` (the ``(normal, d)`` tuple
    from :func:`plane_equation`).  Positive on the side the normal points
    toward, negative on the other, zero on the plane.
    """
    normal, d = plane
    return float(normal.dot(point).scalar_part()) + d
    # doc-region-end define distance to plane


# doc-region-begin define ortho
def ortho(
    left: float,
    right: float,
    bottom: float,
    top: float,
    near: float,
    far: float,
) -> InvertibleFunction[Vector3]:
    midpoint = Vector3(
        coeff_e_1=(left + right) / 2.0,
        coeff_e_2=(bottom + top) / 2.0,
        coeff_e_3=(near + far) / 2.0,
    )
    length_x: float = right - left
    length_y: float = top - bottom
    length_z: float = far - near

    fn: InvertibleFunction[Vector3] = compose(
        [
            scale_non_uniform(
                2.0 / length_x,
                2.0 / length_y,
                2.0 / (-length_z),
            ),
            translate(-midpoint),
        ]
    )

    def f(vector: Vector3) -> Vector3:
        return fn(vector)

    def f_inv(vector: Vector3) -> Vector3:
        return inverse(fn)(vector)

    return InvertibleFunction(
        f, f_inv, "Ortho", "Ortho Inv", linearity=Linearity.AFFINE
    )
    # doc-region-end define ortho


# doc-region-begin define perspective
def perspective(
    field_of_view: float, aspect_ratio: float, near_z: float, far_z: float
) -> InvertibleFunction[Vector3]:
    # field_of_view is the angle of y; aspect_ratio is x_width / y_width.
    top: float = -near_z * math.tan(math.radians(field_of_view) / 2.0)
    right: float = top * aspect_ratio

    fn: InvertibleFunction[Vector3] = ortho(
        left=-right,
        right=right,
        bottom=-top,
        top=top,
        near=near_z,
        far=far_z,
    )

    def f(vector: Vector3) -> Vector3:
        # squish the frustum into a rectangular prism: scale x and y toward the
        # axis in proportion to their depth (the perspective divide).
        scale_factor: float = near_z / vector.coeff_e_3
        rectangular_prism: Vector3 = Vector3(
            coeff_e_1=vector.coeff_e_1 * scale_factor,
            coeff_e_2=vector.coeff_e_2 * scale_factor,
            coeff_e_3=vector.coeff_e_3,
        )
        return fn(rectangular_prism)

    def f_inv(vector: Vector3) -> Vector3:
        rectangular_prism: Vector3 = inverse(fn)(vector)
        # un-scale by the *camera-space* z (recovered as the prism's z), not the
        # NDC input z -- that is what makes this a genuine inverse of f.
        scale_factor: float = near_z / rectangular_prism.coeff_e_3
        return Vector3(
            coeff_e_1=rectangular_prism.coeff_e_1 / scale_factor,
            coeff_e_2=rectangular_prism.coeff_e_2 / scale_factor,
            coeff_e_3=rectangular_prism.coeff_e_3,
        )

    # the perspective divide is non-linear: it is not representable as a single
    # affine matrix recovered by probing points (see gacalc.to_matrix).
    return InvertibleFunction(
        f, f_inv, "Perspective", "Perspective Inv", linearity=Linearity.NONLINEAR
    )
    # doc-region-end define perspective


# doc-region-begin define camera space to ndc
def cs_to_ndc_space_fn(vector: Vector3) -> InvertibleFunction[Vector3]:
    return perspective(field_of_view=45.0, aspect_ratio=1.0, near_z=-0.1, far_z=-1000.0)


# doc-region-end define camera space to ndc


# doc-region-begin define function stack class
@dataclasses.dataclass
class FunctionStack(typing.Generic[V]):
    stack: list[InvertibleFunction[V]] = dataclasses.field(default_factory=lambda: [])

    def push(self, o: InvertibleFunction[V]):
        self.stack.append(o)

    def pop(self) -> InvertibleFunction[V]:
        return self.stack.pop()

    def clear(self):
        self.stack.clear()

    def modelspace_to_ndc_fn(self) -> InvertibleFunction[V]:
        return compose(self.stack)


fn_stack = FunctionStack()
# doc-region-end define function stack class


@contextlib.contextmanager
def push_transformation(f: InvertibleFunction[V]):
    try:
        fn_stack.push(f)
        yield fn_stack
    finally:
        fn_stack.pop()
