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

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

# doc-region-begin define invertible function
# Define a generic type variable
T = TypeVar("T")


@dataclass
class InvertibleFunction(Generic[T]):
    func: Callable[[T], T]
    inverse: Callable[[T], T]

    def __call__(self, x: T) -> T:
        return self.func(x)


def inverse(f: InvertibleFunction[T]) -> InvertibleFunction[T]:
    return InvertibleFunction(f.inverse, f.func)


# doc-region-end define invertible function


def compose(*functions: InvertibleFunction[T]) -> InvertibleFunction[T]:
    def composed_fn(x):
        for f in reversed(functions):
            x: T = f(x)
        return x

    def inv_composed_fn(x):
        for f in functions:
            x: T = inverse(f)(x)
        return x

    return InvertibleFunction[T](composed_fn, inv_composed_fn)
