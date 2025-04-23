# Copyright (c) 2018-2025 William Emerison Six
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
