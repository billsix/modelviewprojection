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


import abc
import dataclasses
import typing


class Vector(abc.ABC):
    @abc.abstractmethod
    def __add__(self, rhs: typing.Self) -> typing.Self:
        pass

    @abc.abstractmethod
    def __mul__(self, scalar: float) -> typing.Self:
        pass

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


# doc-region-begin define invertible function
@dataclasses.dataclass
class InvertibleFunction:
    """
    Class that wraps a function and its
    inverse function.  The function takes
    type T as it's argument and it's evaluation
    results in a value of type T.
    """

    func: typing.Callable[[Vector], Vector]  #: The wrapped function
    inverse: typing.Callable[
        [Vector], Vector
    ]  #: The inverse of the wrapped function

    def __call__(self, x: Vector) -> Vector:
        """
        Execute a function with the given value.

        Args:
            func (typing.Callable[[Vector], Vector]): A function that takes a value of type Vector
                                     and returns a value of the same type Vector.
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
            InvertibleFunction(func=<function f at 0x...>, inverse=<function f_inv at 0x...>)
            >>> foo(5)
            7
            >>> inverse(foo) # doctest: +ELLIPSIS
            InvertibleFunction(func=<function f_inv at 0x...>, inverse=<function f at 0x...>)
            >>> inverse(foo)(foo(5))
            5
        """
        return self.func(x)


def inverse(f: InvertibleFunction) -> InvertibleFunction:
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
        InvertibleFunction(func=<function f at 0x...>, inverse=<function f_inv at 0x...>)
        >>> foo(5)
        7
        >>> inverse(foo) # doctest: +ELLIPSIS
        InvertibleFunction(func=<function f_inv at 0x...>, inverse=<function f at 0x...>)
        >>> inverse(foo)(foo(5))
        5
    """

    return InvertibleFunction(f.inverse, f.func)
    # doc-region-end define invertible function


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
        >>> from modelviewprojection.mathutils import compose_intermediate_fns, InvertibleFunction, uniform_scale, translate
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
) -> typing.Iterable[InvertibleFunction]:
    """
    Like compose, but returns a list of all of the partial compositions

    Example:
        >>> from modelviewprojection.mathutils import compose_intermediate_fns_and_fn, InvertibleFunction, uniform_scale, translate
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
