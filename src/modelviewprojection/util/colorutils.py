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


import dataclasses
import typing

# doc-region-begin define invertible function
# Define a generic type variable
T = typing.TypeVar("T")


@dataclasses.dataclass
class Color3:
    """An RGB color, iterable so it unpacks straight into a GL call.

    >>> red = Color3(r=1.0, g=0.0, b=0.0)
    >>> red.g
    0.0

    Iterating yields ``(r, g, b)`` in order, so ``*color`` spreads into any
    call wanting three channel arguments:

    >>> list(Color3(r=0.1, g=0.2, b=0.3))
    [0.1, 0.2, 0.3]
    >>> r, g, b = Color3(r=0.1, g=0.2, b=0.3)
    >>> b
    0.3
    """

    r: float
    g: float
    b: float

    def __iter__(self) -> typing.Iterator[float]:
        return iter(dataclasses.astuple(self))


@dataclasses.dataclass
class Color4:
    """An RGBA color -- :class:`Color3` plus an alpha channel.

    >>> list(Color4(r=1.0, g=0.5, b=0.25, a=1.0))
    [1.0, 0.5, 0.25, 1.0]
    >>> opaque = Color4(r=0.0, g=0.0, b=0.0, a=1.0)
    >>> opaque.a
    1.0
    """

    r: float
    g: float
    b: float
    a: float

    def __iter__(self) -> typing.Iterator[float]:
        return iter(dataclasses.astuple(self))
