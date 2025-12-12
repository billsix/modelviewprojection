# Copyright (c) 2018-2025 William Emerison Six
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


import contextlib
import dataclasses
import itertools
import math
import typing

import numpy as np
import pytest
import sympy

__all__ = [
    "Vector",
    "Vector1D",
    "InvertibleFunction",
    "identity",
    "inverse",
    "compose",
    "compose_intermediate_fns",
    "compose_intermediate_fns_and_fn",
    "translate",
    "uniform_scale",
    "Vector2D",
    "scale_non_uniform_2d",
    "rotate_90_degrees",
    "rotate",
    "rotate_around",
    "sine",
    "is_counter_clockwise",
    "is_clockwise",
    "is_parallel",
    "Vector3D",
    "cos",
    "abs_sin",
    "scale_non_uniform_3d",
    "rotate_x",
    "rotate_y",
    "rotate_z",
    "ortho",
    "perspective",
    "cs_to_ndc_space_fn",
    "FunctionStack",
    "push_transformation",
]


@dataclasses.dataclass
class Vector:
    # doc-region-begin begin define add
    def __add__(self, rhs: typing.Self) -> typing.Self:
        # doc-region-end begin define add
        """
        Add together two Vectors, component-wise.

        Args:
            rhs (Vector): The vector on the right hand side of the addition
                symbol
        Returns:
            Vector: The Vector that represents the additon of the two input Vectors
        Example:
            >>> from modelviewprojection.mathutils import Vector1D
            >>> a = Vector1D(x=2)
            >>> b = Vector1D(x=5)
            >>> a + b
            Vector1D(x=7)
            >>> from modelviewprojection.mathutils import Vector2D
            >>> a = Vector2D(x=2, y=3)
            >>> b = Vector2D(x=5, y=6)
            >>> a + b
            Vector2D(x=7, y=9)
            >>> from modelviewprojection.mathutils import Vector3D
            >>> a = Vector3D(x=2, y=3, z=1)
            >>> b = Vector3D(x=5, y=6, z=10)
            >>> a + b
            Vector3D(x=7, y=9, z=11)
        """

        # doc-region-begin define add
        if type(self) is not type(rhs):
            return NotImplemented
        return type(self)(
            *[
                a + b
                for a, b in zip(
                    dataclasses.astuple(self), dataclasses.astuple(rhs)
                )
            ]
        )
        # doc-region-end define add

    # doc-region-begin define mul
    def __mul__(self, scalar: float) -> typing.Self:
        # doc-region-end define mul
        """
        Multiply the Vector by a scalar number, component-wise

        Args:
            rhs (Vector): The scalar to be multiplied to the Vector's component
                subtraction symbol
        Returns:
            Vector: The Vector that represents scalar times the amount of the input Vector

        Example:
            >>> from modelviewprojection.mathutils import Vector1D
            >>> a = Vector1D(x=2)
            >>> a * 4
            Vector1D(x=8)
            >>> from modelviewprojection.mathutils import Vector2D
            >>> a = Vector2D(x=2, y=3)
            >>> a * 4
            Vector2D(x=8, y=12)
            >>> from modelviewprojection.mathutils import Vector3D
            >>> a = Vector3D(x=2, y=3, z=5)
            >>> a * 4
            Vector3D(x=8, y=12, z=20)
        """
        # doc-region-begin define mul body
        return type(self)(*[scalar * a for a in dataclasses.astuple(self)])
        # doc-region-end define mul body

    def __neg__(self) -> typing.Self:
        """
        Let :math:`\\vec{a}` and constant :math:`-1`:

        .. math::

             -1 * \\vec{a}

        Example:
            >>> from modelviewprojection.mathutils import Vector1D
            >>> a = Vector1D(x=2)
            >>> -a
            Vector1D(x=-2)
        """
        return -1 * self

    def __iter__(self):
        return iter(dataclasses.astuple(self))

    # doc-region-begin begin define subtract
    def __sub__(self, rhs: typing.Self) -> typing.Self:
        # doc-region-end begin define subtract
        """
        .. math::

             \\vec{a} + -\\vec{b}

        Example:
            >>> from modelviewprojection.mathutils import Vector1D
            >>> a = Vector1D(x=2)
            >>> b = Vector1D(x=5)
            >>> a - b
            Vector1D(x=-3)
        """
        # doc-region-begin define subtract
        return self + -rhs
        # doc-region-end define subtract

    def __rmul__(self, scalar: float) -> typing.Self:
        return self * scalar

    def isclose(self, other: typing.Self) -> float:
        return all(
            bool(np.isclose(v1, v2, rtol=1e-5, atol=1e-5))
            for v1, v2 in zip(self, other)
        )

    def component_wise_with_index(self, other: typing.Self):
        return itertools.product(
            enumerate(self, start=1), enumerate(other, start=1)
        )

    # The dot method uses the generic iterators provided by self and other
    def dot(self, other: typing.Self) -> float:
        if type(self) is not type(other):
            return NotImplemented
        return sum(
            self_component * other_component
            for (self_index, self_component), (
                other_index,
                other_component,
            ) in self.component_wise_with_index(other)
            if self_index == other_index
        )

    def __abs__(self) -> float:
        return np.sqrt(self.dot(self))


# doc-region-begin begin define invertible function
@dataclasses.dataclass
class InvertibleFunction:
    # doc-region-end begin define invertible function
    """
    Class that wraps a function and its
    inverse function.  The function takes
    type T as it's argument and it's evaluation
    results in a value of type T.
    """

    # doc-region-begin invertible function members
    func: typing.Callable[[Vector], Vector]  #: The wrapped function
    inverse: typing.Callable[
        [Vector], Vector
    ]  #: The inverse of the wrapped function
    latex_repr: str  #: The LaTeX representation of the function
    latex_repr_inv: str  #: The LaTeX representation of the inverse function
    # doc-region-end invertible function members

    # doc-region-begin begin call
    def __call__(self, x: Vector) -> Vector:
        # doc-region-end begin call
        """
        Execute a function with the given value.

        Args:
            func (typing.Callable[[Vector], Vector]): A function that takes a
                value of type Vector and returns a value of the same type Vector.
            value (Vector): The input value to pass to the function
        Returns:
            Vector: The result of calling func(value).

            Will be the same type as the input value.
        Example:
            >>> from modelviewprojection.mathutils import InvertibleFunction
            >>> from modelviewprojection.mathutils import inverse
            >>> def f(x):
            ...     return 2 + x
            ...
            >>> def f_inv(x):
            ...     return x - 2
            ...
            >>> foo = InvertibleFunction(func=f, inverse=f_inv, latex_repr="", latex_repr_inv="")
            >>> foo # doctest: +ELLIPSIS
            InvertibleFunction(func=<...>, inverse=<...>, latex_repr=..., latex_repr_inv=...)
            >>> foo(5)
            7
            >>> inverse(foo) # doctest: +ELLIPSIS
            InvertibleFunction(func=<...>, inverse=<...>, latex_repr=..., latex_repr_inv=...)
            >>> inverse(foo)(foo(5))
            5
        """
        # doc-region-begin call definition
        return self.func(x)
        # doc-region-end call definition

    def __matmul__(self, f2: "InvertibleFunction") -> "InvertibleFunction":
        """
        Override @ for function composition.  This is abusing the @ symbol,
        which is normally for matrix multiplication.

        Args:
            f2 (mathutils.InvertibleFunction): A function that self is composed with
                and returns a value of the same type Vector.
        Returns:
            InvertibleFunction: The composed function.

        Example:
            >>> from modelviewprojection.mathutils import InvertibleFunction
            >>> from modelviewprojection.mathutils import inverse
            >>> def f(x):
            ...     return 2 + x
            ...
            >>> def f_inv(x):
            ...     return x - 2
            ...
            >>> foo = InvertibleFunction(func=f, inverse=f_inv, latex_repr="", latex_repr_inv="")
            >>> foo(5)
            7
            >>> (foo @ foo)(5)
            9
            >>> inverse(foo @ foo)(5)
            1
            >>> (foo @ inverse(foo))(5)
            5
        """
        return compose([self, f2])

    def __rmatmul__(self, f2: "InvertibleFunction") -> "InvertibleFunction":
        return f2 @ self

    def _repr_latex_(self):
        return "$" + self.latex_repr + "$"


# doc-region-begin begin define inverse
def inverse(f: InvertibleFunction) -> InvertibleFunction:
    # doc-region-end begin define inverse
    """
    Get the inverse of the InvertibleFunction

    Args:
        f: InvertibleFunction: A function with it's associated inverse
            function.
    Returns:
        InvertibleFunction: The Inverse of the function.
    Example:
        >>> from modelviewprojection.mathutils import InvertibleFunction
        >>> from modelviewprojection.mathutils import inverse
        >>> def f(x):
        ...     return 2 + x
        ...
        >>> def f_inv(x):
        ...     return x - 2
        ...
        >>> foo = InvertibleFunction(func=f, inverse=f_inv, latex_repr="", latex_repr_inv="")
        >>> foo # doctest: +ELLIPSIS
        InvertibleFunction(func=<...>, inverse=<...>, latex_repr=..., latex_repr_inv=...)
        >>> foo(5)
        7
        >>> inverse(foo) # doctest: +ELLIPSIS
        InvertibleFunction(func=<...>, inverse=<...>, latex_repr=..., latex_repr_inv=...)
        >>> inverse(foo)(foo(5))
        5
    """

    # doc-region-begin inverse body
    return InvertibleFunction(f.inverse, f.func, f.latex_repr_inv, f.latex_repr)
    # doc-region-end inverse body


def compose(
    functions: list[InvertibleFunction],
) -> InvertibleFunction:
    """
    Compose a sequence of functions.

    If two functions are passed as arguments, named :math:`f` and :math:`g`:

        :math:`(f \\circ g)(x) = f(g(x))`.

    If :math:`n` functions are passed as arguments, :math:`f_1...f_n`:

        :math:`(f_1 \\circ (f_2 \\circ (... f_n )(x) = f_1(f_2...(f_n(x))`.

    Args:
        functions (list[InvertibleFunction]): Variable number of
            InvertibleFunctions to compose.  At least on value must be provided.

    Returns:
        Vector: One function that is the aggregate function.

    Example:
        >>> from modelviewprojection.mathutils import compose
        >>> from modelviewprojection.mathutils import translate as T
        >>> from modelviewprojection.mathutils import uniform_scale as S
        >>> from modelviewprojection.mathutils import Vector2D
        >>> fn = compose([S(2), T(Vector2D(3, 4))])
        >>> fn(Vector2D(1,1))
        Vector2D(x=8, y=10)
    """

    def composed_fn(x):
        for f in reversed(functions):
            x: Vector = f(x)
        return x

    def inv_composed_fn(x):
        for f in functions:
            x: Vector = inverse(f)(x)
        return x

    tex_str: str = ""
    for f in reversed(functions):
        if tex_str == "":
            tex_str = f.latex_repr
        else:
            tex_str = f.latex_repr + r" \circ " + tex_str

    inv_str: str = ""
    for f in functions:
        if inv_str == "":
            inv_str = inverse(f).latex_repr
        else:
            inv_str = inverse(f).latex_repr + r" \circ " + inv_str

    return InvertibleFunction(composed_fn, inv_composed_fn, tex_str, inv_str)


def compose_intermediate_fns(
    functions: list[InvertibleFunction], relative_basis: bool = False
) -> typing.Iterable[InvertibleFunction]:
    """
    Like compose, but returns a list of all of the partial compositions

    Example:
        >>> from modelviewprojection.mathutils import compose_intermediate_fns
        >>> from modelviewprojection.mathutils import InvertibleFunction
        >>> from modelviewprojection.mathutils import uniform_scale
        >>> from modelviewprojection.mathutils import translate
        >>> from modelviewprojection.mathutils import Vector1D
        >>> from pytest import approx
        >>> m = 5
        >>> b = 2
        >>> # natural basis
        >>> fns: list[InvertibleFunction] = compose_intermediate_fns(
        ...      [translate(Vector1D(b)), uniform_scale(m)]
        ... )
        >>> len(fns)
        3
        >>> fns[0](Vector1D(1))
        Vector1D(x=1)
        >>> fns[1](Vector1D(1))
        Vector1D(x=5)
        >>> fns[2](Vector1D(1))
        Vector1D(x=7)
        >>> # relative basis
        >>> fns: list[InvertibleFunction] = compose_intermediate_fns(
        ...     [translate(Vector1D(b)), uniform_scale(m)], relative_basis=True
        ... )
        >>> len(fns)
        3
        >>> fns[0](Vector1D(1))
        Vector1D(x=1)
        >>> fns[1](Vector1D(1))
        Vector1D(x=3)
        >>> fns[2](Vector1D(1))
        Vector1D(x=7)
    """
    functions_with_identity_fn: list[InvertibleFunction] = (
        [identity()] + functions if relative_basis else functions + [identity()]
    )

    return [
        compose(fs)
        for fs in (
            [
                functions_with_identity_fn[i:]
                for i in reversed(range(len(functions_with_identity_fn)))
            ]
            if not relative_basis
            else [
                functions_with_identity_fn[:i]
                for i in range(1, len(functions_with_identity_fn) + 1)
            ]
        )
    ]


def compose_intermediate_fns_and_fn(
    functions: list[InvertibleFunction], relative_basis: bool = False
) -> list[tuple[InvertibleFunction, InvertibleFunction]]:
    """
    Like compose, but returns a list of all of the partial compositions

    Example:
        >>> from modelviewprojection.mathutils import compose_intermediate_fns_and_fn
        >>> from modelviewprojection.mathutils import InvertibleFunction
        >>> from modelviewprojection.mathutils import uniform_scale
        >>> from modelviewprojection.mathutils import translate
        >>> from modelviewprojection.mathutils import Vector1D
        >>> from pytest import approx
        >>> m = 5
        >>> b = 2
        >>> # natural basis
        >>> for aggregate_fn, current_fn in compose_intermediate_fns_and_fn(
        ...      [translate(Vector1D(b)), uniform_scale(m)]):
        ...      print("agg " + str(aggregate_fn(Vector1D(1))))
        ...      print("current " + str(current_fn(Vector1D(1))))
        ...
        agg Vector1D(x=1)
        current Vector1D(x=5)
        agg Vector1D(x=5)
        current Vector1D(x=3)
        agg Vector1D(x=7)
        current Vector1D(x=1)
        >>> # relative basis
        >>> for aggregate_fn, current_fn in compose_intermediate_fns_and_fn(
        ...      [translate(Vector1D(b)), uniform_scale(m)], relative_basis=True):
        ...      print("agg " + str(aggregate_fn(Vector1D(1))))
        ...      print("current " + str(current_fn(Vector1D(1))))
        ...
        agg Vector1D(x=1)
        current Vector1D(x=1)
        agg Vector1D(x=3)
        current Vector1D(x=3)
        agg Vector1D(x=7)
        current Vector1D(x=5)
    """
    return list(
        zip(
            compose_intermediate_fns(functions, relative_basis=relative_basis),
            [identity()] + functions
            if relative_basis
            else reversed([identity()] + functions),
        )
    )


# doc-region-begin define identity
def identity() -> InvertibleFunction:
    def f(vector: Vector) -> Vector:
        return vector

    def f_inv(vector: Vector) -> Vector:
        return vector

    tex_str: str = "I"
    inv_str: str = "I"
    return InvertibleFunction(f, f_inv, tex_str, inv_str)
    # doc-region-end define identity


# doc-region-begin define translate
def translate(b: Vector) -> InvertibleFunction:
    def f(vector: Vector) -> Vector:
        return vector + b

    def f_inv(vector: Vector) -> Vector:
        return vector - b

    values = dataclasses.astuple(b)
    tex_str: str = (
        f"T_{{<[{str(values[0]) if len(values) == 1 else str(values)[1:-1]}]>}}"
    )
    negative_values = dataclasses.astuple(-b)
    inv_str: str = f"T_{{<[{str(negative_values[0]) if len(negative_values) == 1 else str(negative_values)[1:-1]}]>}}"
    return InvertibleFunction(f, f_inv, tex_str, inv_str)
    # doc-region-end define translate


# doc-region-begin define uniform scale
def uniform_scale(m: float) -> InvertibleFunction:
    def f(vector: Vector) -> Vector:
        return vector * m

    def f_inv(vector: Vector) -> Vector:
        if m == 0.0:
            raise ValueError("Not invertible.  Scaling factor cannot be zero.")

        return vector * (1.0 / m)

    tex_str: str = f"S_{{{m}}}"
    inv_str: str = f"S_{{{-m}}}"
    return InvertibleFunction(f, f_inv, tex_str, inv_str)
    # doc-region-end define uniform scale


# doc-region-begin define vector class
@dataclasses.dataclass
class Vector1D(Vector):
    x: float  #: The value of the 1D Vector
    # doc-region-end define vector class


# doc-region-begin define vector class
@dataclasses.dataclass
class Vector2D(Vector1D):
    y: float  #: The y-component of the 2D Vector
    # doc-region-end define vector class


# doc-region-begin define vector class
@dataclasses.dataclass
class Vector3D(Vector2D):
    z: float  #: The z-component of the 3D Vector
    # doc-region-end define vector class

    def cross(self, rhs: typing.Self) -> typing.Self:
        return Vector3D(
            x=self.y * rhs.z - self.z * rhs.y,
            y=self.z * rhs.x - self.x * rhs.z,
            z=self.x * rhs.y - self.y * rhs.x,
        )


def scale_non_uniform_2d(m_x: float, m_y: float) -> InvertibleFunction:
    def f(vector: Vector) -> Vector:
        assert isinstance(vector, Vector2D)
        return Vector2D(vector.x * m_x, vector.y * m_y)

    def f_inv(vector: Vector) -> Vector:
        assert isinstance(vector, Vector2D)
        if m_x == 0.0 or m_y == 0.0:
            raise ValueError(
                "Note invertible.  Scaling factors cannot be zero."
            )

        return Vector2D(vector.x / m_x, vector.y / m_y)

    return InvertibleFunction(
        f,
        f_inv,
        f"S_{{<{m_x},{m_y}>}}",
        f"S_{{<\\\frac{{1}}{{{m_x}}},\\\frac{{1}}{{{m_y}>}}",
    )


# doc-region-begin define rotate
def rotate_90_degrees() -> InvertibleFunction:
    def f(vector: Vector) -> Vector:
        assert isinstance(vector, Vector2D)
        return Vector2D(-vector.y, vector.x)

    def f_inv(vector: Vector) -> Vector:
        return -f(vector)

    return InvertibleFunction(f, f_inv, "R_{<xy90>}", "R_{<xy90>}^{-1}")


def rotate(angle_in_radians: float) -> InvertibleFunction:
    r90: InvertibleFunction = rotate_90_degrees()

    def create_rotate_function(
        perp: InvertibleFunction,
    ) -> typing.Callable[[Vector], Vector]:
        def f(vector: Vector) -> Vector:
            parallel: Vector = math.cos(float(angle_in_radians)) * vector
            perpendicular: Vector = math.sin(float(angle_in_radians)) * perp(
                vector
            )
            return parallel + perpendicular

        return f

    return InvertibleFunction(
        create_rotate_function(r90),
        create_rotate_function(inverse(r90)),
        f"R_{{<{sympy.latex(angle_in_radians)}>}}",
        f"R_{{<{sympy.latex(-angle_in_radians)}>}}",
    )
    # doc-region-end define rotate


# doc-region-begin define rotate around
def rotate_around(
    angle_in_radians: float, center: Vector2D
) -> InvertibleFunction:
    return compose(
        [translate(center), rotate(angle_in_radians), translate(-center)]
    )
    # doc-region-end define rotate around


def cosine(v1: Vector, v2: Vector) -> float:
    assert isinstance(v1, Vector2D)
    assert isinstance(v2, Vector2D)
    return v1.dot(v2) / (abs(v1) * (abs(v2)))


def sine(v1: Vector, v2: Vector) -> float:
    assert isinstance(v1, Vector2D)
    assert isinstance(v2, Vector2D)
    return rotate_90_degrees()(v1).dot(v2) / (abs(v1) * (abs(v2)))


# doc-region-begin counter clockwise
def is_counter_clockwise(v1: Vector2D, v2: Vector2D) -> bool:
    return sine(v1, v2) >= 0.000000
    # doc-region-end counter clockwise


# doc-region-begin clockwise
def is_clockwise(v1: Vector2D, v2: Vector2D) -> bool:
    return not is_clockwise(v1, v2)
    # doc-region-end clockwise


# doc-region-begin parallel
def is_parallel(v1: Vector2D, v2: Vector2D) -> bool:
    return cosine(v1, v2) == pytest.approx(1.0, abs=0.01)
    # doc-region-end parallel


def cos(v1: Vector3D, v2: Vector3D) -> float:
    return v1.dot(v2) / (abs(v1) * abs(v2))


def abs_sin(v1: Vector3D, v2: Vector3D) -> float:
    return abs(v1.cross(v2)) / (abs(v1) * abs(v2))


def scale_non_uniform_3d(
    m_x: float, m_y: float, m_z: float
) -> InvertibleFunction:
    def f(vector: Vector) -> Vector:
        assert isinstance(vector, Vector3D)
        return Vector3D(vector.x * m_x, vector.y * m_y, vector.z * m_z)

    def f_inv(vector: Vector) -> Vector:
        if m_x == 0.0 or m_y == 0.0 or m_z == 0.0:
            raise ValueError(
                "Note invertible.  Scaling factors cannot be zero."
            )
        assert isinstance(vector, Vector3D)
        return Vector3D(vector.x / m_x, vector.y / m_y, vector.z / m_z)

    return InvertibleFunction(
        f,
        f_inv,
        f"S_{{{m_x},{m_y},{m_z}}}",
        f"S_{{{1.0 / m_x},{1.0 / m_y},{1.0 / m_z}}}",
    )


# doc-region-begin define rotate x
def rotate_x(angle_in_radians: float) -> InvertibleFunction:
    def create_rotate_function(r) -> typing.Callable[[Vector], Vector]:
        def f(vector: Vector) -> Vector:
            assert isinstance(vector, Vector3D)
            yz_on_xy: Vector = Vector2D(x=vector.y, y=vector.z)
            rotated_yz_on_xy: Vector = r(yz_on_xy)
            return Vector3D(
                x=vector.x, y=rotated_yz_on_xy.x, z=rotated_yz_on_xy.y
            )

        return f

    r = rotate(angle_in_radians)
    return InvertibleFunction(
        create_rotate_function(r),
        create_rotate_function(inverse(r)),
        f"RX_{{<{angle_in_radians}>}}",
        f"RX_{{<{-angle_in_radians}>}}",
    )
    # doc-region-end define rotate x


# doc-region-begin define rotate y
def rotate_y(angle_in_radians: float) -> InvertibleFunction:
    def create_rotate_function(r) -> typing.Callable[[Vector], Vector]:
        def f(vector: Vector) -> Vector:
            assert isinstance(vector, Vector3D)
            zx_on_xy: Vector = Vector2D(x=vector.z, y=vector.x)
            rotated_zx_on_xy: Vector = r(zx_on_xy)
            assert isinstance(rotated_zx_on_xy, Vector2D)
            return Vector3D(
                x=rotated_zx_on_xy.y, y=vector.y, z=rotated_zx_on_xy.x
            )

        return f

    r = rotate(angle_in_radians)
    return InvertibleFunction(
        create_rotate_function(r),
        create_rotate_function(inverse(r)),
        f"RY_{{<{angle_in_radians}>}}",
        f"RY_{{<{-angle_in_radians}>}}",
    )
    # doc-region-end define rotate y


# doc-region-begin define rotate z
def rotate_z(angle_in_radians: float) -> InvertibleFunction:
    def create_rotate_function(r) -> typing.Callable[[Vector], Vector]:
        def f(vector: Vector) -> Vector:
            assert isinstance(vector, Vector3D)
            xy_on_xy: Vector = Vector2D(x=vector.x, y=vector.y)
            rotated_xy_on_xy: Vector = r(xy_on_xy)
            assert isinstance(rotated_xy_on_xy, Vector2D)
            return Vector3D(
                x=rotated_xy_on_xy.x, y=rotated_xy_on_xy.y, z=vector.z
            )

        return f

    r: InvertibleFunction = rotate(angle_in_radians)
    return InvertibleFunction(
        create_rotate_function(r),
        create_rotate_function(inverse(r)),
        f"RZ_{{<{angle_in_radians}>}}",
        f"RZ_{{<{-angle_in_radians}>}}",
    )
    # doc-region-end define rotate z


# doc-region-begin define ortho
def ortho(
    left: float,
    right: float,
    bottom: float,
    top: float,
    near: float,
    far: float,
) -> InvertibleFunction:
    midpoint = Vector3D(
        x=(left + right) / 2.0, y=(bottom + top) / 2.0, z=(near + far) / 2.0
    )
    length_x: float
    length_y: float
    length_z: float
    length_x, length_y, length_z = right - left, top - bottom, far - near

    fn = compose(
        [
            scale_non_uniform_3d(
                m_x=(2.0 / length_x),
                m_y=(2.0 / length_y),
                m_z=(2.0 / (-length_z)),
            ),
            translate(-midpoint),
        ]
    )

    def f(vector: Vector) -> Vector:
        return fn(vector)

    def f_inv(vector: Vector) -> Vector:
        return inverse(fn)(vector)

    return InvertibleFunction(f, f_inv, "Ortho", "Ortho Inv")
    # doc-region-end define ortho


# doc-region-begin define perspective
def perspective(
    field_of_view: float, aspect_ratio: float, near_z: float, far_z: float
) -> InvertibleFunction:
    # field_of_view, dataclasses.field of view, is angle of y
    # aspect_ratio is x_width / y_width

    top: float = -near_z * math.tan(math.radians(field_of_view) / 2.0)
    right: float = top * aspect_ratio

    fn = ortho(
        left=-right,
        right=right,
        bottom=-top,
        top=top,
        near=near_z,
        far=far_z,
    )

    def f(vector: Vector) -> Vector:
        assert isinstance(vector, Vector3D)
        s1d: InvertibleFunction = uniform_scale(near_z / vector.z)
        x_component: Vector = s1d(Vector1D(x=vector.x))
        y_component: Vector = s1d(Vector1D(x=vector.y))
        assert isinstance(x_component, Vector1D)
        assert isinstance(y_component, Vector1D)

        rectangular_prism: Vector3D = Vector3D(
            x=x_component.x, y=y_component.x, z=vector.z
        )
        return fn(rectangular_prism)

    def f_inv(vector: Vector) -> Vector:
        assert isinstance(vector, Vector3D)
        rectangular_prism: Vector = inverse(fn)(vector)
        assert isinstance(rectangular_prism, Vector3D)

        inverse_s1d: InvertibleFunction = inverse(
            uniform_scale(near_z / vector.z)
        )
        x_component: Vector = inverse_s1d(Vector1D(x=rectangular_prism.x))
        y_component: Vector = inverse_s1d(Vector1D(x=rectangular_prism.y))
        assert isinstance(x_component, Vector1D)
        assert isinstance(y_component, Vector1D)

        return Vector3D(
            x_component.x,
            y_component.x,
            rectangular_prism.z,
        )

    return InvertibleFunction(f, f_inv, "Perspective", "Perspective Inv")
    # doc-region-end define perspective


# doc-region-begin define camera space to ndc
def cs_to_ndc_space_fn(
    vector: Vector3D,
) -> InvertibleFunction:
    return perspective(
        field_of_view=45.0, aspect_ratio=1.0, near_z=-0.1, far_z=-1000.0
    )


# doc-region-end define camera space to ndc


# doc-region-begin define function stack class
@dataclasses.dataclass
class FunctionStack:
    stack: list[InvertibleFunction] = dataclasses.field(
        default_factory=lambda: []
    )

    def push(self, o: InvertibleFunction):
        self.stack.append(o)

    def pop(self) -> InvertibleFunction:
        return self.stack.pop()

    def clear(self):
        self.stack.clear()

    def modelspace_to_ndc_fn(self) -> InvertibleFunction:
        return compose(self.stack)


fn_stack = FunctionStack()
# doc-region-end define function stack class


@contextlib.contextmanager
def push_transformation(f):
    try:
        fn_stack.push(f)
        yield fn_stack
    finally:
        fn_stack.pop()
