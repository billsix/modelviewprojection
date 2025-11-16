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


import dataclasses
import itertools
import typing

import numpy as np

__all__ = [
    "Vector",
    "InvertibleFunction",
    "inverse",
    "compose",
    "compose_intermediate_fns",
    "compose_intermediate_fns_and_fn",
    "translate",
    "uniform_scale",
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
            Vector: The Vector that represents the additon of the two
                    input Vectors
        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils1d import Vector1D
            >>> a = Vector1D(x=2)
            >>> b = Vector1D(x=5)
            >>> a + b
            Vector1D(x=7)
            >>> from modelviewprojection.mathutils2d import Vector2D
            >>> a = Vector2D(x=2, y=3)
            >>> b = Vector2D(x=5, y=6)
            >>> a + b
            Vector2D(x=7, y=9)
            >>> from modelviewprojection.mathutils3d import Vector3D
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
        """
        Multiply the Vector by a scalar number, component-wise

        Args:
            rhs (Vector): The scalar to be multiplied to the Vector's component
                          subtraction symbol
        Returns:
            Vector: The Vector that represents scalar times the amount of the input
                    Vector

        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils1d import Vector1D
            >>> a = Vector1D(x=2)
            >>> a * 4
            Vector1D(x=8)
            >>> from modelviewprojection.mathutils2d import Vector2D
            >>> a = Vector2D(x=2, y=3)
            >>> a * 4
            Vector2D(x=8, y=12)
            >>> from modelviewprojection.mathutils3d import Vector3D
            >>> a = Vector3D(x=2, y=3, z=5)
            >>> a * 4
            Vector3D(x=8, y=12, z=20)
        """
        return type(self)(*[scalar * a for a in dataclasses.astuple(self)])

    # doc-region-end define mul

    def __neg__(self) -> typing.Self:
        """
        Let :math:`\\vec{a}` and constant :math:`-1`:

        .. math::

             -1 * \\vec{a}

        Example:
            >>> from modelviewprojection.mathutils1d import Vector1D
            >>> a = Vector1D(x=2.0)
            >>> -a
            Vector1D(x=-2.0)
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
            >>> from modelviewprojection.mathutils1d import Vector1D
            >>> a = Vector1D(x=2.0)
            >>> b = Vector1D(x=5.0)
            >>> a - b
            Vector1D(x=-3.0)
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
    # doc-region-end invertible function members

    # doc-region-begin begin call
    def __call__(self, x: Vector) -> Vector:
        # doc-region-end begin call
        """
        Execute a function with the given value.

        Args:
            func (typing.Callable[[Vector], Vector]): A function that takes a value of
                                                      type Vector and returns a value
                                                      of the same type Vector.
            value (Vector): The input value to pass to the function
        Returns:
            Vector: The result of calling func(value). Will be the same type as the
                input value.
        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils import InvertibleFunction
            >>> from modelviewprojection.mathutils import inverse
            >>> def f(x):
            ...     return 2 + x
            ...
            >>> def f_inv(x):
            ...     return x - 2
            ...
            >>> foo = InvertibleFunction(func=f, inverse=f_inv)
            >>> foo # doctest: +ELLIPSIS
            InvertibleFunction(func=<...>, inverse=<...>)
            >>> foo(5)
            7
            >>> inverse(foo) # doctest: +ELLIPSIS
            InvertibleFunction(func=<...>, inverse=<...>)
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
                                               and returns a value of the same type
                                               Vector.
        Returns:
            InvertibleFunction: The composed function.

        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils import InvertibleFunction
            >>> from modelviewprojection.mathutils import inverse
            >>> def f(x):
            ...     return 2 + x
            ...
            >>> def f_inv(x):
            ...     return x - 2
            ...
            >>> foo = InvertibleFunction(func=f, inverse=f_inv)
            >>> foo(5)
            7
            >>> (foo @ foo)(5)
            9
            >>> inverse(foo @ foo)(5)
            1
            >>> (foo @ f_inv)(5)
            5
        """
        return compose([self, f2])

    def __rmatmul__(self, f2: "InvertibleFunction") -> "InvertibleFunction":
        return f2 @ self


# doc-region-begin begin define inverse
def inverse(f: InvertibleFunction) -> InvertibleFunction:
    # doc-region-end begin define inverse
    """
    Get the inverse of the InvertibleFunction

    Args:
        f: InvertibleFunction: A function with it's associated inverse
           function.
    Returns:
        InvertibleFunction: The Inverse of the function
           function.
    Raises:
        Nothing
    Example:
        >>> from modelviewprojection.mathutils import InvertibleFunction
        >>> from modelviewprojection.mathutils import inverse
        >>> def f(x):
        ...     return 2 + x
        ...
        >>> def f_inv(x):
        ...     return x - 2
        ...
        >>> foo = InvertibleFunction(func=f, inverse=f_inv)
        >>> foo # doctest: +ELLIPSIS
        InvertibleFunction(func=<...>, inverse=<...>)
        >>> foo(5)
        7
        >>> inverse(foo) # doctest: +ELLIPSIS
        InvertibleFunction(func=<...>, inverse=<...>)
        >>> inverse(foo)(foo(5))
        5
    """

    # doc-region-begin inverse body
    return InvertibleFunction(f.inverse, f.func)
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
                                                     InvertibleFunctions to compose.
                                                     At least on value must be provided.
    Returns:
        Vector: One function that is the aggregate function of the argument
                functions composed.
    Raises:
        Nothing
    Example:
        >>> from modelviewprojection.mathutils import compose
        >>> compose([lambda x: 5])(1)
        5
        >>> compose([lambda x: 2*x])(1)
        2
        >>> compose([lambda x: x+4, lambda x: 2*x])(1)
        6
        >>> compose([lambda x: x+ 10, lambda x: x+4, lambda x: 2*x])(1)
        16
    """

    def composed_fn(x):
        for f in reversed(functions):
            x: Vector = f(x)
        return x

    def inv_composed_fn(x):
        for f in functions:
            x: Vector = inverse(f)(x)
        return x

    return InvertibleFunction(composed_fn, inv_composed_fn)


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
        >>> from modelviewprojection.mathutils1d import Vector1D
        >>> from pytest import approx
        >>> m = 5.0
        >>> b = 2.0
        >>> # natural basis
        >>> fns: list[InvertibleFunction] = compose_intermediate_fns(
        ...      [translate(Vector1D(b)), uniform_scale(m)]
        ... )
        >>> len(fns)
        2
        >>> fns[0](Vector1D(1))
        Vector1D(x=5.0)
        >>> fns[1](Vector1D(1))
        Vector1D(x=7.0)
        >>> # relative basis
        >>> fns: list[InvertibleFunction] = compose_intermediate_fns(
        ...     [translate(Vector1D(b)), uniform_scale(m)], relative_basis=True
        ... )
        >>> len(fns)
        2
        >>> fns[0](Vector1D(1))
        Vector1D(x=3.0)
        >>> fns[1](Vector1D(1))
        Vector1D(x=7.0)
    """

    return [
        compose(fs)
        for fs in (
            [functions[i:] for i in reversed(range(len(functions)))]
            if not relative_basis
            else [functions[:i] for i in range(1, len(functions) + 1)]
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
        >>> from modelviewprojection.mathutils1d import Vector1D
        >>> from pytest import approx
        >>> m = 5.0
        >>> b = 2.0
        >>> # natural basis
        >>> for aggregate_fn, current_fn in compose_intermediate_fns_and_fn(
        ...      [translate(Vector1D(b)), uniform_scale(m)]):
        ...      print("agg " + str(aggregate_fn(Vector1D(1.0))))
        ...      print("current " + str(current_fn(Vector1D(1.0))))
        ...
        agg Vector1D(x=5.0)
        current Vector1D(x=5.0)
        agg Vector1D(x=7.0)
        current Vector1D(x=3.0)
        >>> # relative basis
        >>> for aggregate_fn, current_fn in compose_intermediate_fns_and_fn(
        ...      [translate(Vector1D(b)), uniform_scale(m)], relative_basis=True):
        ...      print("agg " + str(aggregate_fn(Vector1D(1.0))))
        ...      print("current " + str(current_fn(Vector1D(1.0))))
        ...
        agg Vector1D(x=3.0)
        current Vector1D(x=3.0)
        agg Vector1D(x=7.0)
        current Vector1D(x=5.0)
    """
    return list(
        zip(
            compose_intermediate_fns(functions, relative_basis=relative_basis),
            functions if relative_basis else reversed(functions),
        )
    )


# doc-region-begin define translate
def translate(b: Vector) -> InvertibleFunction:
    def f(vector: Vector) -> Vector:
        return vector + b

    def f_inv(vector: Vector) -> Vector:
        return vector - b

    return InvertibleFunction(f, f_inv)
    # doc-region-end define translate


# doc-region-begin define uniform scale
def uniform_scale(m: float) -> InvertibleFunction:
    def f(vector: Vector) -> Vector:
        return vector * m

    def f_inv(vector: Vector) -> Vector:
        if m == 0.0:
            raise ValueError("Not invertible.  Scaling factor cannot be zero.")

        return vector * (1.0 / m)

    return InvertibleFunction(f, f_inv)
    # doc-region-end define uniform scale
