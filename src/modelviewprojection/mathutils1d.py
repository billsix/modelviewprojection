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
import typing

import numpy as np

import modelviewprojection.mathutils as mu

# for ease of use in importing and using
from modelviewprojection.mathutils import (
    InvertibleFunction,
    compose,
    inverse,
    translate,
    uniform_scale,
)

__all__ = [
    "Vector1D",
    "translate",
    "uniform_scale",
    "InvertibleFunction",
    "inverse",
    "compose",
]


# doc-region-begin define vector class
@dataclasses.dataclass
class Vector1D(mu.Vector):
    x: float  #: The value of the 1D mu.Vector
    # doc-region-end define vector class

    # doc-region-begin begin define add
    def __add__(self, rhs: "mu.Vector") -> "Vector1D":
        # doc-region-end begin define add
        """
        Add together two Vector1Ds.

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\end{pmatrix}`
        and :math:`\\vec{b} = \\begin{pmatrix} b_x \\end{pmatrix}`:

        .. math::

             \\vec{a} + \\vec{b} = \\begin{pmatrix} a_x + b_x \\end{pmatrix}

        Args:
            rhs (Vector1D): The vector on the right hand side of the addition
                            symbol
        Returns:
            Vector1D: The Vector1D that represents the additon of the two
                      input Vector1Ds
        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils1d import Vector1D
            >>> a = Vector1D(x=2.0)
            >>> b = Vector1D(x=5.0)
            >>> a + b
            Vector1D(x=7.0)
        """
        assert isinstance(rhs, Vector1D)
        # doc-region-begin define add
        return Vector1D(x=(self.x + rhs.x))
        # doc-region-end define add

    # doc-region-begin define mul
    def __mul__(self, scalar: float) -> "Vector1D":
        """
        Multiply the Vector1D by a scalar number

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\end{pmatrix}` and constant scalar :math:`s`:

        .. math::

             s*\\vec{a} = \\begin{pmatrix} s*a_x \\end{pmatrix}

        Args:
            rhs (Vector1D): The scalar to be multiplied to the mu.Vector's component
                            subtraction symbol
        Returns:
            Vector1D: The Vector1D that represents scalar times the amount of the input mu.Vector1d

        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils1d import Vector1D
            >>> a = Vector1D(x=2.0)
            >>> a * 4
            Vector1D(x=8.0)
        """
        return Vector1D(x=(self.x * scalar))
        # doc-region-end define mul

    # The dot method uses the generic iterators provided by self and other
    def dot(self, other: typing.Self) -> float:
        return sum(v1 * v2 for v1, v2 in zip(self, other))

    def __abs__(self) -> float:
        return np.sqrt(self.dot(self))
