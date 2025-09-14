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

from modelviewprojection.mathutils import InvertibleFunction


# doc-region-begin define vector class
@dataclass
class Vector1D:
    x: float  #: The value of the 1D Vector
    # doc-region-end define vector class

    # doc-region-begin define add
    def __add__(self, rhs: Vector1D) -> Vector1D:
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

        return Vector1D(x=(self.x + rhs.x))

    # doc-region-end define add

    # doc-region-begin define subtract
    def __sub__(self, rhs: Vector1D) -> Vector1D:
        """
        Subtract the right hand side Vector1D from the left hand side Vector1D.

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\end{pmatrix}`
        and :math:`\\vec{b} = \\begin{pmatrix} b_x \\end{pmatrix}`:

        .. math::

             \\vec{a} - \\vec{b} = \\begin{pmatrix} a_x - b_x \\end{pmatrix}

        Args:
            rhs (Vector1D): The vector on the right hand side of the
                            subtraction symbol
        Returns:
            Vector1D: The Vector1D that represents the subtraction of the
                      right hand side Vector1D from the left hand side
                      Vector1D
        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils1d import Vector1D
            >>> a = Vector1D(x=2.0)
            >>> b = Vector1D(x=5.0)
            >>> a - b
            Vector1D(x=-3.0)
        """
        return Vector1D(x=(self.x - rhs.x))

    # doc-region-end define subtract

    # doc-region-begin define mul
    def __mul__(self, scalar: float) -> Vector1D:
        """
        Multiply the Vector1D by a scalar number

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\end{pmatrix}` and constant scalar :math:`s`:

        .. math::

             s*\\vec{a} = \\begin{pmatrix} s*a_x \\end{pmatrix}

        Args:
            rhs (Vector1D): The scalar to be multiplied to the Vector's component
                            subtraction symbol
        Returns:
            Vector1D: The Vector1D that represents scalar times the amount of the input Vector1d

        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils1d import Vector1D
            >>> a = Vector1D(x=2.0)
            >>> a * 4
            Vector1D(x=8.0)
        """
        return Vector1D(x=(self.x * scalar))

    def __rmul__(self, scalar: float) -> Vector1D:
        return self * scalar

    # doc-region-end define mul

    def __neg__(self) -> Vector1D:
        """
        Multiply the Vector1D by -1

        Let :math:`\\vec{a} = (a_x)` and constant :math:`-1`:

        .. math::

             -1 * \\vec{a}

        Returns:
            Vector1D: The Vector1D with the opposite orientation

        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils1d import Vector1D
            >>> a = Vector1D(x=2.0)
            >>> -a
            Vector1D(x=-2.0)
        """
        return -1.0 * self



# doc-region-begin define translate
def translate(translate_amount: float) -> InvertibleFunction[Vector1D]:
    def f(vector: Vector1D) -> Vector1D:
        return vector + Vector1D(translate_amount)

    def f_inv(vector: Vector1D) -> Vector1D:
        return vector - Vector1D(translate_amount)

    return InvertibleFunction[Vector1D](f, f_inv)


# doc-region-end define translate


# doc-region-begin define uniform scale
def uniform_scale(scalar: float) -> InvertibleFunction[Vector1D]:
    def f(vector: Vector1D) -> Vector1D:
        return vector * scalar

    def f_inv(vector: Vector1D) -> Vector1D:
        if scalar == 0:
            raise ValueError("Scaling factor cannot be zero.")
        return vector * (1.0 / scalar)

    return InvertibleFunction[Vector1D](f, f_inv)


# doc-region-end define uniform scale
