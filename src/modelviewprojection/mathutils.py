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


from __future__ import annotations  # to appease Python 3.7-3.9

from dataclasses import dataclass, field
from typing import Callable, Generic, TypeVar

# doc-region-begin define invertible function
# Define a generic type variable
T = TypeVar("T")


@dataclass
class InvertibleFunction(Generic[T]):
    """
    Class that wraps a function and its inverse function.
    The function takes type T as it's argument and it's evaluation
    results in a value of type T.
    """

    func: Callable[[T], T] = field(metadata={"doc": "The wrapped function"})
    inverse: Callable[[T], T] = field(
        metadata={"doc": "The inverse of the wrapped function"}
    )

    def foo(self):
        """autodoc"""

    def __call__(self, x: T) -> T:
        """
        Execute a function with the given value.

        Args:
            func (Callable[[T], T]): A function that takes a value of type T and returns a value of the same type T.
            value (T): The input value to pass to the function
        Returns:
            T: The result of calling func(value). Will be the same type as the
                input value.
        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils import InvertibleFunction, inverse
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


def inverse(f: InvertibleFunction[T]) -> InvertibleFunction[T]:
    return InvertibleFunction(f.inverse, f.func)


# doc-region-end define invertible function


def compose(*functions: InvertibleFunction[T]) -> InvertibleFunction[T]:
    """
    Compose a sequence of functions.

    If two functions are passed as arguments, named :math:`f` and :math:`g`:

        :math:`(f \\circ g)(x) = f(g(x))`.

    If :math:`n` functions are passed as arguments, :math:`f_1...f_n`:

        :math:`(f_1 \\circ (f_2 \\circ (... f_n )(x) = f_1(f_2...(f_n(x))`.


    Args:
        *functions (InvertibleFunction[T]): Variable number of InvertibleFunctions
        to compose.  At least on value must be provided.
    Returns:
        T: One function that is the aggregate function of the argument functions
        composed.
    Raises:
        Nothing
    Example:
        >>> from modelviewprojection.mathutils import compose
        >>> compose(lambda x: 5)(1)
        5
        >>> compose(lambda x: 2*x)(1)
        2
        >>> compose(lambda x: x+4, lambda x: 2*x)(1)
        6
        >>> compose(lambda x: x+ 10, lambda x: x+4, lambda x: 2*x)(1)
        16
    """

    def composed_fn(x):
        for f in reversed(functions):
            x: T = f(x)
        return x

    def inv_composed_fn(x):
        for f in functions:
            x: T = inverse(f)(x)
        return x

    return InvertibleFunction[T](composed_fn, inv_composed_fn)
