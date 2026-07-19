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
``uniform_scale`` / ``scale_non_uniform``, the ``at`` / ``steps`` animation
layer,
and the ``Linearity`` tag).  They are re-exported here so the course can keep
importing them from ``modelviewprojection.mathutils``.

What lives *here* is the graphics-specific math that gacalc deliberately does
not
carry: angle-based 2D/axis rotations (built on top of gacalc vectors), the
``ortho`` / ``perspective`` projections, the plane-geometry helpers
(``find_normal`` via the geometric-algebra ``wedge`` + ``dual``,
``plane_equation``,
``distance_to_plane``), the 2D orientation predicates, and the
``FunctionStack`` (the Python analogue of OpenGL's matrix stack).
"""

import contextlib
import dataclasses
import math
import typing

# Re-exported from gacalc: the vector representations and the transform layer.
from gacalc.base import MultiVectorBase
from gacalc.g1 import Vector1
from gacalc.g2 import Bivector2, Vector2
from gacalc.g3 import Vector3
from gacalc.transforms import (
    InvertibleFunction,
    Linearity,
    compose,
    compose_intermediate_fns,
    compose_intermediate_fns_and_fn,
    identity,
    inverse,
    plane_rotation,
    scale_non_uniform,
    to_matrix,
    translate,
    uniform_scale,
)

__all__ = [
    # re-exported from gacalc
    "MultiVectorBase",
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
    "rotate",
    "rotate_around",
    "rotate_x",
    "rotate_y",
    "rotate_z",
    "cosine",
    "sine",
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
#: transforms; bound to ``MultiVectorBase``, matching gacalc's
#: ``InvertibleFunction[V]``.  Used where the type is open (the function stack).
V = typing.TypeVar("V", bound=MultiVectorBase)


# doc-region-begin define rotate 2d
# rotate(theta) rotates a Vector2 by theta in the plane e_1 wedge e_2 (the
# only plane there is, in 2D).  It is bound at module scope ON PURPOSE:
# plane_rotation derives the plane ONCE (wedge -> normalized unit bivector,
# cached in the closure), so each rotate(theta) call -- and every animation
# frame's .at(t) -- just assembles the half-angle rotor from it.  Rebinding
# it per call would re-derive the plane every time.  A numeric theta stays
# in plain floats end to end.
rotate: typing.Callable[[float], InvertibleFunction[Vector2]] = plane_rotation(
    Vector2.e_1,
    Vector2.e_2,
    latex_repr=lambda t: f"R_{{<{t}>}}",
    latex_repr_inv=lambda t: f"R_{{<{-t}>}}",
)
# doc-region-end define rotate 2d


# doc-region-begin define rotate around
def rotate_around(
    angle_in_radians: float, center: Vector2
) -> InvertibleFunction[Vector2]:
    # doc-region-end rotate around signature
    """Rotate about ``center`` instead of about the origin.

    Read the composition right-to-left: move ``center`` to the origin, rotate
    there, then put it back.

    >>> import math
    >>> from modelviewprojection.mathutils import Vector2
    >>> quarter_turn = rotate_around(math.pi / 2, 1.0 * Vector2.e_1)
    >>> [round(float(c), 6) for c in quarter_turn(2.0 * Vector2.e_1)]
    [1.0, 1.0]

    The center is the one point that does not move:

    >>> [round(float(c), 6) for c in quarter_turn(1.0 * Vector2.e_1)]
    [1.0, 0.0]

    Contrast plain :data:`rotate`, which turns about the origin -- the same
    input lands somewhere else entirely:

    >>> [round(float(c), 6) for c in rotate(math.pi / 2)(2.0 * Vector2.e_1)]
    [0.0, 2.0]
    """
    # doc-region-begin rotate around body
    return compose(
        [translate(center), rotate(angle_in_radians), translate(-center)]
    )
    # doc-region-end define rotate around


def cosine(v1: MultiVectorBase, v2: MultiVectorBase) -> float:
    """Cosine of the angle between two vectors, of any dimension.

    This is the dot product normalized by both lengths, so it depends only on
    the directions -- ``1`` for parallel, ``0`` for perpendicular, ``-1`` for
    opposite:

    >>> from modelviewprojection.mathutils import Vector2
    >>> cosine(1.0 * Vector2.e_1, 1.0 * Vector2.e_1)
    1.0
    >>> cosine(1.0 * Vector2.e_1, 1.0 * Vector2.e_2)
    0.0
    >>> cosine(1.0 * Vector2.e_1, -1.0 * Vector2.e_1)
    -1.0

    Lengthening a vector does not change the angle it makes:

    >>> cosine(1.0 * Vector2.e_1, 5.0 * Vector2.e_1)
    1.0

    A zero-length vector has no direction, so the angle is undefined and the
    result is NaN rather than a ZeroDivisionError:

    >>> import math
    >>> math.isnan(cosine(0.0 * Vector2.e_1, 1.0 * Vector2.e_1))
    True
    """
    # gacalc's dot product returns a (scalar) multivector; read off its value.
    denominator: float = float(abs(v1)) * float(abs(v2))
    if denominator == 0.0:
        # the angle is undefined when either vector has zero length
        return float("nan")
    return float(v1.dot(v2).scalar_part()) / denominator


def sine(v1: Vector2, v2: Vector2) -> float:
    """Sine of the angle from ``v1`` to ``v2``, in 2D.  **Signed.**

    >>> from modelviewprojection.mathutils import Vector2
    >>> sine(1.0 * Vector2.e_1, 1.0 * Vector2.e_2)
    1.0

    Unlike :func:`cosine`, the sign carries the *direction of the turn* -- so
    swapping the arguments negates the result.  This is what makes it useful
    for deciding which way a point lies relative to an edge:

    >>> sine(1.0 * Vector2.e_2, 1.0 * Vector2.e_1)
    -1.0

    Parallel vectors span no area, so the sine is zero:

    >>> sine(1.0 * Vector2.e_1, 5.0 * Vector2.e_1)
    0.0

    Undefined (NaN) when either vector has zero length, as with :func:`cosine`:

    >>> import math
    >>> math.isnan(sine(0.0 * Vector2.e_1, 1.0 * Vector2.e_2))
    True
    """
    denominator: float = float(abs(v1)) * float(abs(v2))
    if denominator == 0.0:
        return float("nan")
    # |v1||v2| sin(theta) IS the 2D wedge -- the bivector coefficient of
    # v1 ^ v2, a.k.a. the 2D cross product / signed area.  The classic
    # "rotate v1 by 90 degrees, then dot with v2" trick computes exactly
    # this number; the algebra hands it to us directly.
    return float((v1 ^ v2).coefficient(Bivector2.e_12)) / denominator


# doc-region-begin define rotate x
# rotation in the y-z plane: carry e_2 toward e_3 (the x axis, e_1, is
# fixed).  Bound at module scope for the same reason as rotate: the plane
# is derived once, each call is just trig + rotor.
rotate_x: typing.Callable[[float], InvertibleFunction[Vector3]] = (
    plane_rotation(
        Vector3.e_2,
        Vector3.e_3,
        latex_repr=lambda t: f"RX_{{<{t}>}}",
        latex_repr_inv=lambda t: f"RX_{{<{-t}>}}",
    )
)
# doc-region-end define rotate x


# doc-region-begin define rotate y
# rotation in the z-x plane: carry e_3 toward e_1 (the y axis, e_2, is fixed)
rotate_y: typing.Callable[[float], InvertibleFunction[Vector3]] = (
    plane_rotation(
        Vector3.e_3,
        Vector3.e_1,
        latex_repr=lambda t: f"RY_{{<{t}>}}",
        latex_repr_inv=lambda t: f"RY_{{<{-t}>}}",
    )
)
# doc-region-end define rotate y


# doc-region-begin define rotate z
# rotation in the x-y plane: carry e_1 toward e_2 (the z axis, e_3, is fixed)
rotate_z: typing.Callable[[float], InvertibleFunction[Vector3]] = (
    plane_rotation(
        Vector3.e_1,
        Vector3.e_2,
        latex_repr=lambda t: f"RZ_{{<{t}>}}",
        latex_repr_inv=lambda t: f"RZ_{{<{-t}>}}",
    )
)
# doc-region-end define rotate z


def abs_sin(v1: Vector3, v2: Vector3) -> float:
    """Unsigned sine of the angle between two 3D vectors.

    The 3D counterpart of :func:`sine`, but **unsigned** -- in 3D there is no
    single "turn direction" to take a sign from, since the two vectors span a
    plane that can be viewed from either side:

    >>> from modelviewprojection.mathutils import Vector3
    >>> abs_sin(1.0 * Vector3.e_1, 1.0 * Vector3.e_2)
    1.0
    >>> abs_sin(1.0 * Vector3.e_2, 1.0 * Vector3.e_1)
    1.0

    Parallel vectors span no area:

    >>> abs_sin(1.0 * Vector3.e_1, 5.0 * Vector3.e_1)
    0.0
    """
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

    A triangle in the x-y plane, wound counter-clockwise, has a normal pointing
    along +z:

    >>> from modelviewprojection.mathutils import Vector3
    >>> origin = 0.0 * Vector3.e_1
    >>> find_normal(origin, 1.0 * Vector3.e_1, 1.0 * Vector3.e_2)
    Vector3(coeff_e_1=0.0, coeff_e_2=0.0, coeff_e_3=1.0)

    Reversing the winding flips the normal -- which is exactly how a renderer
    tells a front face from a back face:

    >>> find_normal(origin, 1.0 * Vector3.e_2, 1.0 * Vector3.e_1)
    Vector3(coeff_e_1=0.0, coeff_e_2=0.0, coeff_e_3=-1.0)

    The length is twice the triangle's area, not 1 -- this triangle has area
    ``0.5``:

    >>> float(abs(find_normal(origin, 1.0 * Vector3.e_1, 1.0 * Vector3.e_2)))
    1.0
    """
    bivector = (p2 - p1) ^ (p3 - p1)
    n = bivector.dual()
    return Vector3(
        coeff_e_1=float(n.coefficient(Vector3.e_1)),
        coeff_e_2=float(n.coefficient(Vector3.e_2)),
        coeff_e_3=float(n.coefficient(Vector3.e_3)),
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

    The horizontal plane at ``z == 3``, given by three of its points:

    >>> from modelviewprojection.mathutils import Vector3
    >>> normal, d = plane_equation(
    ...     3.0 * Vector3.e_3,
    ...     1.0 * Vector3.e_1 + 3.0 * Vector3.e_3,
    ...     1.0 * Vector3.e_2 + 3.0 * Vector3.e_3,
    ... )
    >>> normal
    Vector3(coeff_e_1=0.0, coeff_e_2=0.0, coeff_e_3=1.0)
    >>> d
    -3.0

    Unlike :func:`find_normal`, the normal here is always unit length, whatever
    the size of the triangle you passed in:

    >>> float(abs(normal))
    1.0

    Read ``d`` as "how far the plane sits from the origin, along the normal,
    negated": the plane is 3 units up, so ``d`` is ``-3.0``.  That is what makes
    the plane equation come out to zero on the plane itself -- for any point
    ``P`` there, ``normal . P + d == 0``.
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
def distance_to_plane(
    point: Vector3, plane: typing.Tuple[Vector3, float]
) -> float:
    """Signed distance from ``point`` to ``plane`` (the ``(normal, d)`` tuple
    from :func:`plane_equation`).  Positive on the side the normal points
    toward, negative on the other, zero on the plane.

    Using the ``z == 3`` plane from :func:`plane_equation`, whose normal points
    up:

    >>> from modelviewprojection.mathutils import Vector3
    >>> plane = plane_equation(
    ...     3.0 * Vector3.e_3,
    ...     1.0 * Vector3.e_1 + 3.0 * Vector3.e_3,
    ...     1.0 * Vector3.e_2 + 3.0 * Vector3.e_3,
    ... )
    >>> distance_to_plane(5.0 * Vector3.e_3, plane)
    2.0
    >>> distance_to_plane(1.0 * Vector3.e_3, plane)
    -2.0

    Zero exactly on the plane -- and note it is the *perpendicular* distance,
    so sliding the point sideways within the plane does not change it:

    >>> distance_to_plane(
    ...     2.0 * Vector3.e_1 + 2.0 * Vector3.e_2 + 3.0 * Vector3.e_3, plane
    ... )
    0.0

    The sign is the useful part: it says which side of the plane a point is on,
    which is how a clipper decides to keep, cut, or discard a vertex.
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
    # doc-region-end ortho signature
    """Map the viewable rectangular prism onto NDC -- the ``[-1, 1]`` cube.

    Center the prism on the origin, then scale each axis by the inverse of its
    length.  The corner of the viewable region lands on the corner of the cube:

    >>> from modelviewprojection.mathutils import Vector3
    >>> to_ndc = ortho(
    ...     left=-10.0, right=10.0, bottom=-10.0, top=10.0,
    ...     near=-1.0, far=-100.0,
    ... )
    >>> def xyz(v):
    ...     return [round(float(c), 6) for c in v]
    >>> xyz(to_ndc(10.0 * Vector3.e_1 + 10.0 * Vector3.e_2))
    [1.0, 1.0, 1.020202]

    The transform is affine and invertible, so it round-trips:

    >>> point = 3.0 * Vector3.e_1 + 4.0 * Vector3.e_2 - 5.0 * Vector3.e_3
    >>> xyz(inverse(to_ndc)(to_ndc(point)))
    [3.0, 4.0, -5.0]
    """
    # doc-region-begin ortho body
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
        func=f,
        latex_repr="Ortho",
        inverse=f_inv,
        latex_repr_inv="Ortho Inv",
        linearity=Linearity.AFFINE,
    )
    # doc-region-end define ortho


# doc-region-begin define perspective
def perspective(
    field_of_view: float, aspect_ratio: float, near_z: float, far_z: float
) -> InvertibleFunction[Vector3]:
    # doc-region-end perspective signature
    """Map the viewable *frustum* onto NDC, so distant things appear smaller.

    Where :func:`ortho` maps a box, this maps a pyramid-shaped frustum: x and y
    are scaled toward the axis in proportion to depth (the perspective divide),
    and the squished result is then handed to :func:`ortho`.

    >>> from modelviewprojection.mathutils import Vector3
    >>> to_ndc = perspective(
    ...     field_of_view=90.0, aspect_ratio=1.0, near_z=-1.0, far_z=-100.0
    ... )
    >>> def xyz(v):
    ...     return [round(float(c), 6) for c in v]

    This is the whole idea of perspective in one pair of examples.  A point 1
    unit off-axis at 1 unit away, and a point 2 units off-axis at 2 units away,
    land on **the same** NDC x -- they subtend the same angle from the eye, so
    they draw at the same place on screen:

    >>> xyz(to_ndc(1.0 * Vector3.e_1 - 1.0 * Vector3.e_3))
    [1.0, 0.0, 1.0]
    >>> xyz(to_ndc(2.0 * Vector3.e_1 - 2.0 * Vector3.e_3))
    [1.0, 0.0, 0.979798]

    Their NDC *depths* still differ, which is what the depth buffer uses to
    decide which one is in front.

    A point straight ahead stays on the axis:

    >>> xyz(to_ndc(-5.0 * Vector3.e_3))
    [0.0, 0.0, 0.919192]

    The perspective divide is non-linear, but it is still invertible -- the
    inverse un-scales by the recovered camera-space depth, so it round-trips:

    >>> point = 3.0 * Vector3.e_1 + 4.0 * Vector3.e_2 - 5.0 * Vector3.e_3
    >>> xyz(inverse(to_ndc)(to_ndc(point)))
    [3.0, 4.0, -5.0]
    """
    # doc-region-begin perspective body
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
        func=f,
        latex_repr="Perspective",
        inverse=f_inv,
        latex_repr_inv="Perspective Inv",
        linearity=Linearity.NONLINEAR,
    )
    # doc-region-end define perspective


# doc-region-begin define camera space to ndc
def cs_to_ndc_space_fn(vector: Vector3) -> InvertibleFunction[Vector3]:
    # doc-region-end camera space to ndc signature
    """The course's standard camera-space-to-NDC transform.

    A :func:`perspective` with the settings the demos use, wrapped so a demo
    can say what it means without repeating the four numbers:

    >>> from modelviewprojection.mathutils import Vector3
    >>> to_ndc = cs_to_ndc_space_fn(0.0 * Vector3.e_1)
    >>> [round(float(c), 6) for c in to_ndc(-10.0 * Vector3.e_3)]
    [0.0, 0.0, 0.980198]
    """
    # doc-region-begin camera space to ndc body
    return perspective(
        field_of_view=45.0, aspect_ratio=1.0, near_z=-0.1, far_z=-1000.0
    )


# doc-region-end define camera space to ndc


# doc-region-begin define function stack class
@dataclasses.dataclass
class FunctionStack(typing.Generic[V]):
    # doc-region-end function stack class signature
    """A stack of transformations -- the Python analogue of OpenGL's matrix
    stack.

    Push transformations as you descend a scene hierarchy, pop as you come back
    up, and ask for the composed function whenever you need to draw.

    >>> from modelviewprojection.mathutils import Vector3, translate
    >>> stack = FunctionStack()
    >>> stack.push(translate(1.0 * Vector3.e_1))
    >>> len(stack.stack)
    1
    >>> _ = stack.pop()
    >>> len(stack.stack)
    0
    """

    # doc-region-begin function stack class fields

    stack: list[InvertibleFunction[V]] = dataclasses.field(
        default_factory=lambda: []
    )

    def push(self, o: InvertibleFunction[V]) -> None:
        # doc-region-end function stack push signature
        """Add a transformation to the top of the stack.

        >>> stack = FunctionStack()
        >>> stack.push(translate(1.0 * Vector3.e_1))
        >>> len(stack.stack)
        1
        """
        # doc-region-begin function stack push body
        self.stack.append(o)

    def pop(self) -> InvertibleFunction[V]:
        # doc-region-end function stack pop signature
        """Remove the top transformation and return it.

        >>> stack = FunctionStack()
        >>> stack.push(translate(1.0 * Vector3.e_1))
        >>> popped = stack.pop()
        >>> len(stack.stack)
        0
        """
        # doc-region-begin function stack pop body
        return self.stack.pop()

    def clear(self) -> None:
        # doc-region-end function stack clear signature
        """Empty the stack.

        >>> stack = FunctionStack()
        >>> stack.push(translate(1.0 * Vector3.e_1))
        >>> stack.push(translate(2.0 * Vector3.e_2))
        >>> stack.clear()
        >>> len(stack.stack)
        0
        """
        # doc-region-begin function stack clear body
        self.stack.clear()

    def modelspace_to_ndc_fn(self) -> InvertibleFunction[V]:
        # doc-region-end function stack compose signature
        """Compose the whole stack into one transformation.

        An empty stack composes to the identity -- nothing moves:

        >>> stack = FunctionStack()
        >>> composed = stack.modelspace_to_ndc_fn()
        >>> [round(float(c), 6) for c in composed(3.0 * Vector3.e_1)]
        [3.0, 0.0, 0.0]

        Pushed transformations apply as one function -- here the scale runs
        first, then the translate:

        >>> stack.push(translate(1.0 * Vector3.e_1))
        >>> stack.push(uniform_scale(2.0))
        >>> composed = stack.modelspace_to_ndc_fn()
        >>> [round(float(c), 6) for c in composed(1.0 * Vector3.e_1)]
        [3.0, 0.0, 0.0]
        """
        # doc-region-begin function stack compose body
        return compose(self.stack)


fn_stack = FunctionStack()
# doc-region-end define function stack class


@contextlib.contextmanager
def push_transformation(
    f: InvertibleFunction[V],
) -> typing.Iterator["FunctionStack[V]"]:
    """Push a transformation onto the global stack for the duration of a block.

    The Python analogue of OpenGL's ``glPushMatrix`` / ``glPopMatrix`` pair.
    The ``finally`` is the point: the pop happens on the way out **whether the
    block finishes normally or raises**, so a failed draw cannot leave the
    stack unbalanced for every later frame.

    The block yields the stack itself, so the depth is visible inside it:

    >>> from modelviewprojection.mathutils import Vector3, translate
    >>> with push_transformation(translate(1.0 * Vector3.e_1)) as stack:
    ...     len(stack.stack)
    1

    ``stack`` still names that same object afterwards, and the transformation
    is gone from it:

    >>> len(stack.stack)
    0

    Nesting composes -- each block adds one transformation and removes it
    again:

    >>> with push_transformation(translate(1.0 * Vector3.e_1)):
    ...     with push_transformation(translate(2.0 * Vector3.e_2)) as stack:
    ...         len(stack.stack)
    2
    >>> len(stack.stack)
    0

    An exception still unwinds the stack, because the pop is in a ``finally``:

    >>> try:
    ...     with push_transformation(translate(1.0 * Vector3.e_1)) as stack:
    ...         raise ValueError("a draw call failed")
    ... except ValueError:
    ...     len(stack.stack)
    0
    """
    try:
        fn_stack.push(f)
        yield fn_stack
    finally:
        fn_stack.pop()
