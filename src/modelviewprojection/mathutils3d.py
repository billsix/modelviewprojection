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

import math
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List

from modelviewprojection.mathutils import InvertibleFunction, compose, inverse
from modelviewprojection.mathutils1d import Vector1D
from modelviewprojection.mathutils1d import uniform_scale as scale1d
from modelviewprojection.mathutils2d import Vector2D
from modelviewprojection.mathutils2d import rotate as rotate2D


# doc-region-begin define vector class
@dataclass
class Vector3D:
    x: float  #: The x-component of the 3D Vector
    y: float  #: The y-component of the 3D Vector
    z: float  #: The z-component of the 3D Vector

    def __add__(self, rhs: Vector3D) -> Vector3D:
        """
        Add together two Vector3Ds.

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\\\ a_y \\\\ a_z \\end{pmatrix}`
        and :math:`\\vec{b} = \\begin{pmatrix} b_x \\\\ b_y \\\\ b_z \\end{pmatrix}`:

        .. math::

             \\vec{a} + \\vec{b} = \\begin{pmatrix} a_x + b_x \\\\ a_y + b_y \\\\ a_z + b_z \\end{pmatrix}

        Args:
            rhs (Vector3D): The vector on the right hand side of the addition
                            symbol
        Returns:
            Vector3D: The Vector3D that represents the additon of the two
                      input Vector3Ds
        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils3d import Vector3D
            >>> a = Vector3D(x=2.0, y=3.0, z=1.0)
            >>> b = Vector3D(x=5.0, y=6.0, z=9.0)
            >>> a + b
            Vector3D(x=7.0, y=9.0, z=10.0)
        """
        return Vector3D(
            x=(self.x + rhs.x), y=(self.y + rhs.y), z=(self.z + rhs.z)
        )

    def __sub__(self, rhs: Vector3D) -> Vector3D:
        """
        Subtract the right hand side Vector3D from the left hand side Vector3D.

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\\\ a_y \\\\ a_z \\end{pmatrix}`
        and :math:`\\vec{b} = \\begin{pmatrix} b_x \\\\ b_y \\\\ b_z \\end{pmatrix}`:

        .. math::

             \\vec{a} - \\vec{b} = \\vec{a} + \\vec{b} = \\begin{pmatrix} a_x - b_x  \\\\ a_y - b_y \\\\ a_z - b_z \\end{pmatrix}

        Args:
            rhs (Vector3D): The vector on the right hand side of the
                            subtraction symbol
        Returns:
            Vector3D: The Vector3D that represents the subtraction of the
                      right hand side Vector3D from the left hand side
                      Vector3D
        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils3d import Vector3D
            >>> a = Vector3D(x=2.0, y=3.0, z=10.0)
            >>> b = Vector3D(x=5.0, y=2.0, z=1.0)
            >>> a - b
            Vector3D(x=-3.0, y=1.0, z=9.0)
        """
        return Vector3D(
            x=(self.x - rhs.x), y=(self.y - rhs.y), z=(self.z - rhs.z)
        )

    def __mul__(vector, scalar: float) -> Vector3D:
        """
        Multiply the Vector3D by a scalar number

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\\\ a_y \\\\ a_z \\end{pmatrix}` and constant scalar :math:`s`:

        .. math::

             s*\\vec{a} = \\begin{pmatrix} s*a_x \\\\ s*a_y \\\\ s*a_z \\end{pmatrix}

        Args:
            rhs (Vector3D): The scalar to be multiplied to the Vector's component
                            subtraction symbol
        Returns:
            Vector3D: The Vector3D that represents scalar times the amount of the input Vector3D

        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils3d import Vector3D
            >>> a = Vector3D(x=2.0, y=3.0, z=4.0)
            >>> a * 4
            Vector3D(x=8.0, y=12.0, z=16.0)
        """
        return Vector3D(
            x=(vector.x * scalar), y=(vector.y * scalar), z=(vector.z * scalar)
        )

    def __rmul__(vector, scalar: float) -> Vector3D:
        return vector * scalar

    def __neg__(vector) -> Vector3D:
        """
        Multiply the Vector3D by -1

        Let :math:`\\vec{a} = \\begin{pmatrix} a_x \\\\ a_y \\\\ a_z  \\end{pmatrix}` and constant :math:`-1`:

        .. math::

             -1 * \\vec{a}

        Returns:
            Vector3D: The Vector3D with the opposite orientation

        Raises:
            Nothing
        Example:
            >>> from modelviewprojection.mathutils3d import Vector3D
            >>> a = Vector3D(x=2.0, y=3.0, z=4.0)
            >>> -a
            Vector3D(x=-2.0, y=-3.0, z=-4.0)
        """
        return -1.0 * vector

    def __abs__(self) -> float:
        return np.sqrt(self.dot(self))

    def dot(self, rhs: Vector3D) -> float:
        return self.x * rhs.x + self.y * rhs.y + self.z * rhs.z

    def cross(self, rhs: Vector3D) -> Vector3D:
        return Vector3D(
            x=self.y * rhs.z - self.z * rhs.y,
            y=self.z * rhs.x - self.x * rhs.z,
            z=self.x * rhs.y - self.y * rhs.x,
        )


def cos(v1: Vector3D, v2: Vector3D) -> float:
    return v1.dot(v2) / (abs(v1) * abs(v2))


def abs_sin(v1: Vector3D, v2: Vector3D) -> float:
    return abs(v1.cross(v2)) / (abs(v1) * abs(v2))


def translate(translate_amount: Vector3D) -> InvertibleFunction[Vector3D]:
    def f(vector: Vector3D) -> Vector3D:
        return vector + translate_amount

    def f_inv(vector: Vector3D) -> Vector3D:
        return vector - translate_amount

    return InvertibleFunction[Vector3D](f, f_inv)


# doc-region-end define vector class


# doc-region-begin define rotate x
def rotate_x(angle_in_radians: float) -> InvertibleFunction[Vector3D]:
    fn = rotate2D(angle_in_radians)

    def f(vector: Vector3D) -> Vector3D:
        yz_on_xy: Vector2D = fn(Vector2D(x=vector.y, y=vector.z))
        return Vector3D(x=vector.x, y=yz_on_xy.x, z=yz_on_xy.y)

    def f_inv(vector: Vector3D) -> Vector3D:
        yz_on_xy: Vector2D = inverse(fn)(Vector2D(x=vector.y, y=vector.z))
        return Vector3D(x=vector.x, y=yz_on_xy.x, z=yz_on_xy.y)

    return InvertibleFunction[Vector3D](f, f_inv)


# doc-region-end define rotate x


# doc-region-begin define rotate y
def rotate_y(angle_in_radians: float) -> InvertibleFunction[Vector3D]:
    fn = rotate2D(angle_in_radians)

    def f(vector: Vector3D) -> Vector3D:
        zx_on_xy: Vector2D = fn(Vector2D(x=vector.z, y=vector.x))
        return Vector3D(x=zx_on_xy.y, y=vector.y, z=zx_on_xy.x)

    def f_inv(vector: Vector3D) -> Vector3D:
        zx_on_xy: Vector2D = inverse(fn)(Vector2D(x=vector.z, y=vector.x))
        return Vector3D(x=zx_on_xy.y, y=vector.y, z=zx_on_xy.x)

    return InvertibleFunction[Vector3D](f, f_inv)


# doc-region-end define rotate y


# doc-region-begin define rotate z
def rotate_z(angle_in_radians: float) -> InvertibleFunction[Vector3D]:
    fn = rotate2D(angle_in_radians)

    def f(vector: Vector3D) -> Vector3D:
        xy_on_xy: Vector2D = fn(Vector2D(x=vector.x, y=vector.y))
        return Vector3D(x=xy_on_xy.x, y=xy_on_xy.y, z=vector.z)

    def f_inv(vector: Vector3D) -> Vector3D:
        xy_on_xy: Vector2D = inverse(fn)(Vector2D(x=vector.x, y=vector.y))
        return Vector3D(x=xy_on_xy.x, y=xy_on_xy.y, z=vector.z)

    return InvertibleFunction[Vector3D](f, f_inv)


# doc-region-end define rotate z


# doc-region-begin define uniform scale
def uniform_scale(scalar: float) -> InvertibleFunction[Vector3D]:
    def f(vector: Vector3D) -> Vector3D:
        return vector * scalar

    def f_inv(vector: Vector3D) -> Vector3D:
        if scalar == 0.0:
            raise ValueError("Not invertible.  Scaling factor cannot be zero.")

        return vector * (1.0 / scalar)

    return InvertibleFunction[Vector3D](f, f_inv)


# doc-region-end define uniform scale


def scale(
    scale_x: float, scale_y: float, scale_z: float
) -> InvertibleFunction[Vector3D]:
    def f(vector: Vector3D) -> Vector3D:
        return Vector3D(
            x=(vector.x * scale_x),
            y=(vector.y * scale_y),
            z=(vector.z * scale_z),
        )

    def f_inv(vector: Vector3D) -> Vector3D:
        if scale_x == 0:
            raise ValueError("Note invertible.  Scale_x cannot be zero.")
        if scale_y == 0:
            raise ValueError("Note invertible.  Scale_y cannot be zero.")
        if scale_z == 0:
            raise ValueError("Note invertible.  Scale_z cannot be zero.")

        return Vector3D(
            x=(vector.x / scale_x),
            y=(vector.y / scale_y),
            z=(vector.z / scale_z),
        )

    return InvertibleFunction[Vector3D](f, f_inv)


# doc-region-begin define ortho
def ortho(
    left: float,
    right: float,
    bottom: float,
    top: float,
    near: float,
    far: float,
) -> InvertibleFunction[Vector3D]:
    midpoint = Vector3D(
        x=(left + right) / 2.0, y=(bottom + top) / 2.0, z=(near + far) / 2.0
    )
    length_x: float
    length_y: float
    length_z: float
    length_x, length_y, length_z = right - left, top - bottom, far - near

    fn = compose(
        scale(
            scale_x=(2.0 / length_x),
            scale_y=(2.0 / length_y),
            scale_z=(2.0 / (-length_z)),
        ),
        translate(-midpoint),
    )

    def f(vector: Vector3D) -> Vector3D:
        return fn(vector)

    def f_inv(vector: Vector3D) -> Vector3D:
        return f_inv(fn)(vector)

    return InvertibleFunction[Vector3D](f, f_inv)


# doc-region-end define ortho


# doc-region-begin define perspective
def perspective(
    field_of_view: float, aspect_ratio: float, near_z: float, far_z: float
) -> InvertibleFunction[Vector3D]:
    # field_of_view, field of view, is angle of y
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

    def f(vector: Vector3D) -> Vector3D:
        s1d: InvertibleFunction[Vector1D] = scale1d(near_z / vector.z)
        rectangular_prism: Vector3D = Vector3D(
            s1d(vector.x), s1d(vector.y), vector.z
        )
        return fn(rectangular_prism)

    def f_inv(vector: Vector3D) -> Vector3D:
        rectangular_prism: Vector3D = inverse(fn)(vector)

        inverse_s1d: InvertibleFunction[Vector1D] = inverse(
            scale1d(near_z / vector.z)
        )
        return Vector3D(
            inverse_s1d(rectangular_prism.x),
            inverse_s1d(rectangular_prism.y),
            rectangular_prism.z,
        )

    return InvertibleFunction[Vector3D](f, f_inv)


# doc-region-end define perspective


def cs_to_ndc_space_fn(vector: Vector3D) -> InvertibleFunction[Vector3D]:
    def f(vector: Vector3D) -> Vector3D:
        fn = perspective(
            field_of_view=45.0, aspect_ratio=1.0, near_z=-0.1, far_z=-1000.0
        )
        return fn(vector)

    def f_inv(vector: Vector3D) -> Vector3D:
        raise ValueError("Inverse_Inner cs_to_ndc_spcae_fn not yet implement")

    return InvertibleFunction[Vector3D](f, f_inv)


# doc-region-begin define function stack class
@dataclass
class FunctionStack:
    stack: List[InvertibleFunction[Vector3D]] = field(
        default_factory=lambda: []
    )

    def push(self, o: object):
        self.stack.append(o)

    def pop(self):
        return self.stack.pop()

    def clear(self):
        self.stack.clear()

    def modelspace_to_ndc_fn(self) -> InvertibleFunction[Vector3D]:
        return compose(*self.stack)


fn_stack = FunctionStack()
# doc-region-end define function stack class


@contextmanager
def push_transformation(f):
    try:
        fn_stack.push(f)
        yield fn_stack
    finally:
        fn_stack.pop()
