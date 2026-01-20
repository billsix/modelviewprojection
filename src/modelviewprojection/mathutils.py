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
import functools
import itertools
import math
import numbers
import typing

import numpy as np
import pytest
import sympy

__all__ = [
    "Vector",
    "MultiVector",
    "project",
    "reject",
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
    "a_1",
    "a_2",
    "a_3",
    "b_1",
    "b_2",
    "b_3",
    "sym_vec2_1",
    "sym_vec2_2",
    "sym_vec3_1",
    "sym_vec3_2",
    "sym_vec_plane",
    "sym_vec_plane_simplified",
]


BladeCoef = dict[tuple[int, ...], numbers.Number]


@dataclasses.dataclass
class MultiVector:
    coefficient_of_blade: BladeCoef

    def __post_init__(self):
        # prune zero coefficient_of_blade
        self.coefficient_of_blade = {
            blade: self.coefficient_of_blade[blade]
            for blade in self.coefficient_of_blade.keys()
            if self.coefficient_of_blade[blade] != 0
        }

    @staticmethod
    def from_scalar(scalar: int | float):
        return MultiVector({tuple(): scalar})  # type: ignore

    @staticmethod
    def from_sympy_expr(s: sympy.Expr):
        return MultiVector({tuple(): s})  # type: ignore

    @staticmethod
    def unit_pseudoscalar(g: int) -> "MultiVector":
        return math.prod(
            [MultiVector({(x,): 1}) for x in range(1, g + 1)], start=one
        )  # type: ignore

    @staticmethod
    def unit_pseudoscalar_squared(g: int) -> "MultiVector":
        unit_pseudoscalar: MultiVector = MultiVector.unit_pseudoscalar(g)
        return unit_pseudoscalar * unit_pseudoscalar

    @staticmethod
    def sum_dicts(dicts: list[BladeCoef]) -> BladeCoef:
        def sum_2_dicts(dict1: BladeCoef, dict2: BladeCoef) -> BladeCoef:
            return {
                blade: dict1.get(blade, 0) + dict2.get(blade, 0)  # type: ignore
                for blade in dict1.keys() | dict2.keys()
            }

        return functools.reduce(sum_2_dicts, dicts, {})

    def __add__(self, rhs) -> "MultiVector":
        return MultiVector(
            coefficient_of_blade={
                blade: (
                    self.coefficient_of_blade.get(blade, 0)
                    + rhs.coefficient_of_blade.get(blade, 0)
                )
                for blade in (
                    self.coefficient_of_blade.keys()
                    | rhs.coefficient_of_blade.keys()
                )
            }
        )

    def __sub__(self, rhs: typing.Self) -> "MultiVector":
        return self + -rhs

    def __mul__(self, rhs) -> "MultiVector":
        def decrease_grade(
            basis_blades: tuple[int, ...], magnitude: numbers.Number
        ) -> tuple[tuple[int, ...], numbers.Number]:
            match basis_blades:
                case ():
                    return (), magnitude
                case (a,):
                    return (a,), magnitude
                case (a, c, *rest) if a == c:
                    return decrease_grade((*rest,), magnitude)
                case (a, c, *rest) if a > c:
                    return decrease_grade((c, a, *rest), -magnitude)  # type: ignore
                case (a, c, *rest) if a < c:
                    sorted_rest, new_mag = decrease_grade((c, *rest), magnitude)
                    match sorted_rest:
                        case (b, *_) if a < b:
                            return (a, *sorted_rest), new_mag
                        case _:
                            return decrease_grade((a, *sorted_rest), new_mag)
                case _:
                    raise ValueError(
                        "This code should never be able to be excuted"
                    )

        match rhs:
            case int() as n:
                return self * MultiVector.from_scalar(n)
            case float() as n:
                return self * MultiVector.from_scalar(n)
            case sympy.Expr() as s:
                return self * MultiVector.from_sympy_expr(s)
            case _:
                return MultiVector(
                    coefficient_of_blade=MultiVector.sum_dicts(
                        [
                            dict(
                                [
                                    decrease_grade(
                                        basis_blades=(
                                            *blade_left,
                                            *blade_right,
                                        ),
                                        magnitude=scalar_left * scalar_right,  # type: ignore
                                    )
                                ]
                            )
                            for (blade_left, scalar_left), (
                                blade_right,
                                scalar_right,
                            ) in itertools.product(
                                self.coefficient_of_blade.items(),
                                rhs.coefficient_of_blade.items(),
                            )
                        ]
                    )
                )

    def __rmul__(self, lhs) -> "MultiVector":
        match lhs:
            case int() as n:
                return self * MultiVector.from_scalar(n)
            case float() as n:
                return self * MultiVector.from_scalar(n)
            case sympy.Expr() as s:
                return self * MultiVector.from_sympy_expr(s)
            case _:
                return -self.__mul__(lhs)

    def __neg__(self) -> "MultiVector":
        return -1 * self

    def __abs__(self) -> numbers.Number | sympy.Expr:
        return sympy.sqrt(self.abs_squared())

    def component(self, x: typing.Self) -> numbers.Number:
        return self.dot(x).scalar_part()

    def dot(self, rhs) -> "MultiVector":
        return sum(
            [
                (self.r(lg) * rhs.r(rg)).r(abs(lg - rg))
                for lg, rg in itertools.product(self.grades(), rhs.grades())
                if lg > 0 and rg > 0
            ],
            start=zero,
        )

    def wedge(self, rhs) -> "MultiVector":
        return sum(
            [
                (self.r(lg) * rhs.r(rg)).r(lg + rg)
                for lg, rg in itertools.product(self.grades(), rhs.grades())
            ],
            start=zero,
        )

    def r(self, part: int) -> "MultiVector":
        return self.r_vector_part(part)

    def r_vector_part(self, r: int) -> "MultiVector":
        return MultiVector(
            coefficient_of_blade={
                blade: self.coefficient_of_blade[blade]
                for blade in self.coefficient_of_blade.keys()
                if len(blade) == r
            }
        )

    def is_homogeneous_of_grade_r(self, r: int) -> bool:
        return self == self.r_vector_part(r)

    def scalar_part(self) -> numbers.Number:
        return self.r(0).coefficient_of_blade.get(tuple(), 0)  # type: ignore

    def grades(self) -> list[int]:
        return list(
            set(len(blade) for blade in self.coefficient_of_blade.keys())
        )

    def max_grade(self) -> int:
        return max(self.grades())

    def reverse(self) -> "MultiVector":
        """
        from Hestenes and Sobczyk, Clifford Algebra to Geometric Calculus, page 5

        to avoid using floats, I subtituted (-1)**(r*(r-1)/2) with an equivalent
        expression
        """
        return sum(
            [
                MultiVector.unit_pseudoscalar_squared(g) * self.r(g)
                for g in self.grades()
            ],
            start=zero,
        )

    def simplify(self) -> "MultiVector":
        return MultiVector(
            coefficient_of_blade={
                blade: sympy.simplify(self.coefficient_of_blade[blade])  # type: ignore
                for blade in self.coefficient_of_blade.keys()
            }
        )

    def abs_squared(self) -> numbers.Number:
        return (self.reverse() * self).simplify().scalar_part()

    def inverse(self) -> "MultiVector":
        """
        from Hestenes and Sobczyk, Clifford Algebra to Geometric Calculus, page 18

        Note sure if I'm doing it correctly
        """
        return self.reverse().simplify() * (self.abs_squared() ** (-1))  # type: ignore

    def dual(self, g: int) -> "MultiVector":
        return self * MultiVector.unit_pseudoscalar(g).inverse()

    def even_part(self) -> "MultiVector":
        """
        from Hestenes and Sobczyk, Clifford Algebra to Geometric Calculus, page 8

        """
        return sum(
            [self.r_vector_part(g) for g in self.grades() if g % 2 == 0],
            start=zero,
        )

    def odd_part(self) -> "MultiVector":
        """
        from Hestenes and Sobczyk, Clifford Algebra to Geometric Calculus, page 8

        """
        return sum(
            [self.r_vector_part(g) for g in self.grades() if g % 2 == 1],
            start=zero,
        )

    def cosine(self, other: "MultiVector") -> numbers.Number:
        """
        from Hestenes and Sobczyk, Clifford Algebra to Geometric Calculus, page 14

        """
        return (
            (self.reverse() * other).scalar_part()
            * (abs(self) ** (-1))
            * (abs(other) ** (-1))
        )  # type: ignore

    def _repr_latex_(self):
        def add_parens_or_dont(x):
            if isinstance(x, sympy.Expr):
                if x.is_Add:
                    return "(" + sympy.latex(sympy.sympify(str(x))) + ")"
                else:
                    return sympy.latex(sympy.sympify(str(x)))
            else:
                return sympy.latex(sympy.sympify(str(x)))

        blades = [
            add_parens_or_dont(self.coefficient_of_blade[blade])
            + " ".join(map(lambda b: r"\mathbf{\vec{e}}_" + str(b), blade))
            if blade != tuple()
            else add_parens_or_dont(self.coefficient_of_blade[blade])
            for blade in sorted(self.coefficient_of_blade.keys())
        ]
        # latex_string = r"$\frac{1}{2}$"
        return "$" + " +  ".join(blades) + "$"


def project(
    onto_mv: MultiVector,
) -> typing.Callable[[MultiVector], MultiVector]:
    """
    page 18
    """

    def value(value: MultiVector) -> MultiVector:
        return (value.dot(onto_mv)) * onto_mv.inverse()

    return value


def reject(from_mv: MultiVector) -> typing.Callable[[MultiVector], MultiVector]:
    """
    page 18
    """

    def value(value: MultiVector) -> MultiVector:
        return (value.wedge(from_mv)) * from_mv.inverse()

    return value


e_1: MultiVector = MultiVector({(1,): 1})  # type: ignore
e_2: MultiVector = MultiVector({(2,): 1})  # type: ignore
e_3: MultiVector = MultiVector({(3,): 1})  # type: ignore
zero: MultiVector = MultiVector.from_scalar(0)
one: MultiVector = MultiVector.from_scalar(1)


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
    def dot(self, other: typing.Self) -> typing.Self:
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
    func: typing.Callable[[MultiVector], MultiVector]  #: The wrapped function
    inverse: typing.Callable[
        [MultiVector], MultiVector
    ]  #: The inverse of the wrapped function
    latex_repr: str  #: The LaTeX representation of the function
    latex_repr_inv: str  #: The LaTeX representation of the inverse function
    # doc-region-end invertible function members

    # doc-region-begin begin call
    def __call__(self, x: MultiVector) -> MultiVector:
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
            x: MultiVector = f(x)
        return x

    def inv_composed_fn(x):
        for f in functions:
            x: MultiVector = inverse(f)(x)
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
    def f(vector: MultiVector) -> MultiVector:
        return vector

    def f_inv(vector: MultiVector) -> MultiVector:
        return vector

    tex_str: str = "I"
    inv_str: str = "I"
    return InvertibleFunction(f, f_inv, tex_str, inv_str)
    # doc-region-end define identity


# doc-region-begin define translate
def translate(b: MultiVector) -> InvertibleFunction:
    def f(vector: MultiVector) -> MultiVector:
        return vector + b

    def f_inv(vector: MultiVector) -> MultiVector:
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
    def f(vector: MultiVector) -> MultiVector:
        return vector * m

    def f_inv(vector: MultiVector) -> MultiVector:
        if m == 0.0:
            raise ValueError("Not invertible.  Scaling factor cannot be zero.")

        return vector * (1.0 / m)

    tex_str: str = f"S_{{{m}}}"
    inv_str: str = f"S_{{{-m}}}"
    return InvertibleFunction(f, f_inv, tex_str, inv_str)
    # doc-region-end define uniform scale


e_1: MultiVector = MultiVector({(1,): 1})  # type: ignore
e_2: MultiVector = MultiVector({(2,): 1})  # type: ignore
e_3: MultiVector = MultiVector({(3,): 1})  # type: ignore
zero: MultiVector = MultiVector.from_scalar(0)
one: MultiVector = MultiVector.from_scalar(1)

a_1, a_2, a_3, b_1, b_2, b_3 = sympy.symbols("a_1 a_2 a_3 b_1 b_2 b_3")

sym_vec2_1: MultiVector = a_1 * e_1 + a_2 * e_2
sym_vec2_2: MultiVector = b_1 * e_1 + b_2 * e_2

sym_vec3_1: MultiVector = a_1 * e_1 + a_2 * e_2 + a_3 * e_3
sym_vec3_2: MultiVector = b_1 * e_1 + b_2 * e_2 + b_3 * e_3

sym_vec_plane: MultiVector = sym_vec3_1 * sym_vec3_2
sym_vec_plane_simplified: MultiVector = sym_vec_plane.simplify()


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
    def f(vector: MultiVector) -> MultiVector:
        # TODO - assert isinstance(vector, Vector2D)
        return m_x * project(onto_mv=e_1)(vector) + m_y * project(onto_mv=e_2)(
            vector
        )

    def f_inv(vector: MultiVector) -> MultiVector:
        assert isinstance(vector, Vector2D)
        if m_x == 0.0 or m_y == 0.0:
            raise ValueError(
                "Note invertible.  Scaling factors cannot be zero."
            )

        return (m_x) ** (-1) * project(onto_mv=e_1)(vector) + (m_y) ** (
            -1
        ) * project(onto_mv=e_2)(vector)

    return InvertibleFunction(
        f,
        f_inv,
        f"S_{{<{m_x},{m_y}>}}",
        f"S_{{<\\\frac{{1}}{{{m_x}}},\\\frac{{1}}{{{m_y}>}}",
    )


# doc-region-begin define rotate
def rotate_90_degrees() -> InvertibleFunction:
    rot_90: MultiVector = e_1 * e_2

    def f(vector: MultiVector) -> MultiVector:
        return vector * rot_90

    def f_inv(vector: MultiVector) -> MultiVector:
        return vector * rot_90.inverse()

    return InvertibleFunction(f, f_inv, "R_{<xy90>}", "R_{<xy90>}^{-1}")


def rotate(angle_in_radians: float) -> InvertibleFunction:
    r90: InvertibleFunction = rotate_90_degrees()

    def create_rotate_function(
        perp: InvertibleFunction,
    ) -> typing.Callable[[MultiVector], MultiVector]:
        def f(vector: MultiVector) -> MultiVector:
            parallel: MultiVector = math.cos(float(angle_in_radians)) * vector
            perpendicular: MultiVector = math.sin(
                float(angle_in_radians)
            ) * perp(vector)
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
    angle_in_radians: float, center: MultiVector
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
    def f(vector: MultiVector) -> MultiVector:
        # TODO assert isinstance(vector, Vector3D)
        return (
            m_x * project(onto_mv=e_1)(vector)
            + m_y * project(onto_mv=e_2)(vector)
            + m_z * project(onto_mv=e_3)(vector)
        )

    def f_inv(vector: MultiVector) -> MultiVector:
        if m_x == 0.0 or m_y == 0.0 or m_z == 0.0:
            raise ValueError(
                "Note invertible.  Scaling factors cannot be zero."
            )
        # assert isinstance(vector, Vector3D)
        return (
            (m_x) ** (-1) * project(onto_mv=e_1)(vector)
            + (m_y) ** (-1) * project(onto_mv=e_2)(vector)
            + (m_z) ** (-1) * project(onto_mv=e_3)(vector)
        )

    return InvertibleFunction(
        f,
        f_inv,
        f"S_{{{m_x},{m_y},{m_z}}}",
        f"S_{{{1.0 / m_x},{1.0 / m_y},{1.0 / m_z}}}",
    )


def inefficient_rotate_x(angle_in_radians: float) -> InvertibleFunction:
    project_onto_e2_e3 = project(e_2 * e_3)
    project_onto_e1 = reject(e_2 * e_3)

    def create_rotate_function(
        perp: InvertibleFunction,
    ) -> typing.Callable[[MultiVector], MultiVector]:
        def rotate_plane(vector: MultiVector) -> MultiVector:
            parallel: MultiVector = math.cos(float(angle_in_radians)) * vector
            perpendicular: MultiVector = math.sin(
                float(angle_in_radians)
            ) * perp(vector)
            return parallel + perpendicular

        def f(vector: MultiVector):
            return rotate_plane(project_onto_e2_e3(vector)) + project_onto_e1(
                vector
            )

        return f

    def rotate_90_degrees_e2_e3() -> InvertibleFunction:
        rot_90: MultiVector = e_2 * e_3

        def f(vector: MultiVector) -> MultiVector:
            return vector * rot_90

        def f_inv(vector: MultiVector) -> MultiVector:
            return vector * rot_90.inverse()

        return InvertibleFunction(f, f_inv, "R_{<yz90>}", "R_{<yz90>}^{-1}")

    r90: InvertibleFunction = rotate_90_degrees_e2_e3()
    return InvertibleFunction(
        create_rotate_function(r90),
        create_rotate_function(inverse(r90)),
        f"RX_{{<{angle_in_radians}>}}",
        f"RX_{{<{-angle_in_radians}>}}",
    )


# doc-region-begin define rotate x
def rotate_x(angle_in_radians: float) -> InvertibleFunction:
    half_angle: float = angle_in_radians / 2.0
    a: MultiVector = e_2
    b: MultiVector = math.cos(half_angle) * e_2 + math.sin(half_angle) * e_3  # type: ignore

    def f(vector: MultiVector) -> MultiVector:
        return b * a * vector * a * b

    def f_inv(vector: MultiVector) -> MultiVector:
        return a * b * vector * b * a

    return InvertibleFunction(
        f,
        f_inv,
        f"RX_{{<{angle_in_radians}>}}",
        f"RX_{{<{-angle_in_radians}>}}",
    )
    # doc-region-end define rotate x


# doc-region-begin define rotate y
def rotate_y(angle_in_radians: float) -> InvertibleFunction:
    half_angle: float = angle_in_radians / 2.0

    a: MultiVector = e_3
    b: MultiVector = math.cos(half_angle) * e_3 + math.sin(half_angle) * e_1  # type: ignore

    def f(vector: MultiVector) -> MultiVector:
        return b * a * vector * a * b

    def f_inv(vector: MultiVector) -> MultiVector:
        return a * b * vector * b * a

    return InvertibleFunction(
        f,
        f_inv,
        f"YZ_{{<{angle_in_radians}>}}",
        f"YZ_{{<{-angle_in_radians}>}}",
    )
    # doc-region-end define rotate y


# doc-region-begin define rotate z
def rotate_z(angle_in_radians: float) -> InvertibleFunction:
    half_angle: float = angle_in_radians / 2.0
    a: MultiVector = e_1
    b: MultiVector = math.cos(half_angle) * e_1 + math.sin(half_angle) * e_2  # type: ignore

    def f(vector: MultiVector) -> MultiVector:
        return b * a * vector * a * b

    def f_inv(vector: MultiVector) -> MultiVector:
        return a * b * vector * b * a

    return InvertibleFunction(
        f,
        f_inv,
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
    midpoint: MultiVector = (
        ((left + right) / 2.0) * e_1
        + ((bottom + top) / 2.0) * e_2
        + ((near + far) / 2.0) * e_3
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

    def f(vector: MultiVector) -> MultiVector:
        return fn(vector)

    def f_inv(vector: MultiVector) -> MultiVector:
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

    def f(vector: MultiVector) -> MultiVector:
        # assert isinstance(vector, Vector3D)
        s1d: InvertibleFunction = uniform_scale(near_z / vector.component(e_3))  # type: ignore
        return fn(s1d(project(e_1 * e_2)(vector)) + project(e_3)(vector))

    def f_inv(vector: MultiVector) -> MultiVector:
        s1d: InvertibleFunction = uniform_scale(near_z / vector.component(e_3))  # type: ignore
        return inverse(fn)(
            inverse(s1d)(project(e_1 * e_2)(vector)) + project(e_3)(vector)
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
