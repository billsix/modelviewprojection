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


import math
from contextlib import contextmanager
import dataclasses

import modelviewprojection.mathutils as mathutils

from modelviewprojection.mathutils1d import Vector1D
from modelviewprojection.mathutils2d import Vector2D
from modelviewprojection.mathutils2d import rotate as rotate2D
import typing


# doc-region-begin define vector class
@dataclasses.dataclass
class Vector3D(Vector2D):
    z: float  #: The z-component of the 3D Vector
    # doc-region-end define vector class

    def __add__(self, rhs: typing.Self) -> typing.Self:
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

    def __mul__(vector, scalar: float) -> typing.Self:
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

    def cross(self, rhs: typing.Self) -> typing.Self:
        return Vector3D(
            x=self.y * rhs.z - self.z * rhs.y,
            y=self.z * rhs.x - self.x * rhs.z,
            z=self.x * rhs.y - self.y * rhs.x,
        )


def cos(v1: Vector3D, v2: Vector3D) -> float:
    return v1.dot(v2) / (abs(v1) * abs(v2))


def abs_sin(v1: Vector3D, v2: Vector3D) -> float:
    return abs(v1.cross(v2)) / (abs(v1) * abs(v2))


def scale(
    m_x: float, m_y: float, m_z: float
) -> mathutils.InvertibleFunction[Vector3D]:
    def f(vector: Vector3D) -> Vector3D:
        return Vector3D(vector.x * m_x, vector.y * m_y, vector.z * m_z)

    def f_inv(vector: Vector3D) -> Vector3D:
        if m_x == 0.0 or m_y == 0.0 or m_z == 0.0:
            raise ValueError(
                "Note invertible.  Scaling factors cannot be zero."
            )

        return Vector3D(vector.x / m_x, vector.y / m_y, vector.z / m_z)

    return mathutils.InvertibleFunction[Vector3D](f, f_inv)


# doc-region-begin define rotate x
def rotate_x(angle_in_radians: float) -> mathutils.InvertibleFunction[Vector3D]:
    def create_rotate_function(r) -> typing.Callable[[Vector3D], Vector3D]:
        def f(vector: Vector2D) -> Vector2D:
            yz_on_xy: Vector2D = Vector2D(x=vector.y, y=vector.z)
            rotated_yz_on_xy: Vector2D = r(yz_on_xy)
            return Vector3D(
                x=vector.x, y=rotated_yz_on_xy.x, z=rotated_yz_on_xy.y
            )

        return f

    r = rotate2D(angle_in_radians)
    return mathutils.InvertibleFunction[Vector3D](
        create_rotate_function(r), create_rotate_function(mathutils.inverse(r))
    )
    # doc-region-end define rotate x


# doc-region-begin define rotate y
def rotate_y(angle_in_radians: float) -> mathutils.InvertibleFunction[Vector3D]:
    def create_rotate_function(r) -> typing.Callable[[Vector3D], Vector3D]:
        def f(vector: Vector2D) -> Vector2D:
            zx_on_xy: Vector2D = Vector2D(x=vector.z, y=vector.x)
            rotated_zx_on_xy: Vector2D = r(zx_on_xy)
            return Vector3D(
                x=rotated_zx_on_xy.y, y=vector.y, z=rotated_zx_on_xy.x
            )

        return f

    r = rotate2D(angle_in_radians)
    return mathutils.InvertibleFunction[Vector3D](
        create_rotate_function(r), create_rotate_function(mathutils.inverse(r))
    )
    # doc-region-end define rotate y


# doc-region-begin define rotate z
def rotate_z(angle_in_radians: float) -> mathutils.InvertibleFunction[Vector3D]:
    def create_rotate_function(r) -> typing.Callable[[Vector3D], Vector3D]:
        def f(vector: Vector2D) -> Vector2D:
            xy_on_xy: Vector2D = Vector2D(x=vector.x, y=vector.y)
            rotated_xy_on_xy: Vector2D = r(xy_on_xy)
            return Vector3D(
                x=rotated_xy_on_xy.x, y=rotated_xy_on_xy.y, z=vector.z
            )

        return f

    r = rotate2D(angle_in_radians)
    return mathutils.InvertibleFunction[Vector3D](
        create_rotate_function(r), create_rotate_function(mathutils.inverse(r))
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
) -> mathutils.InvertibleFunction[Vector3D]:
    midpoint = Vector3D(
        x=(left + right) / 2.0, y=(bottom + top) / 2.0, z=(near + far) / 2.0
    )
    length_x: float
    length_y: float
    length_z: float
    length_x, length_y, length_z = right - left, top - bottom, far - near

    fn = mathutils.compose(
        scale(
            m_x=(2.0 / length_x),
            m_y=(2.0 / length_y),
            m_z=(2.0 / (-length_z)),
        ),
        mathutils.translate(-midpoint),
    )

    def f(vector: Vector3D) -> Vector3D:
        return fn(vector)

    def f_inv(vector: Vector3D) -> Vector3D:
        return f_inv(fn)(vector)

    return mathutils.InvertibleFunction[Vector3D](f, f_inv)
    # doc-region-end define ortho


# doc-region-begin define perspective
def perspective(
    field_of_view: float, aspect_ratio: float, near_z: float, far_z: float
) -> mathutils.InvertibleFunction[Vector3D]:
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

    def f(vector: Vector3D) -> Vector3D:
        s1d: mathutils.InvertibleFunction[Vector1D] = mathutils.uniform_scale(
            near_z / vector.z
        )
        rectangular_prism: Vector3D = Vector3D(
            s1d(vector.x), s1d(vector.y), vector.z
        )
        return fn(rectangular_prism)

    def f_inv(vector: Vector3D) -> Vector3D:
        rectangular_prism: Vector3D = mathutils.inverse(fn)(vector)

        mathutils.inverse_s1d: mathutils.InvertibleFunction[Vector1D] = (
            mathutils.inverse(mathutils.uniform_scale(near_z / vector.z))
        )
        return Vector3D(
            mathutils.inverse_s1d(rectangular_prism.x),
            mathutils.inverse_s1d(rectangular_prism.y),
            rectangular_prism.z,
        )

    return mathutils.InvertibleFunction[Vector3D](f, f_inv)
    # doc-region-end define perspective


def cs_to_ndc_space_fn(
    vector: Vector3D,
) -> mathutils.InvertibleFunction[Vector3D]:
    return perspective(
        field_of_view=45.0, aspect_ratio=1.0, near_z=-0.1, far_z=-1000.0
    )


# doc-region-begin define function stack class
@dataclasses.dataclass
class FunctionStack:
    stack: typing.List[mathutils.InvertibleFunction[Vector3D]] = (
        dataclasses.field(default_factory=lambda: [])
    )

    def push(self, o: object):
        self.stack.append(o)

    def pop(self):
        return self.stack.pop()

    def clear(self):
        self.stack.clear()

    def modelspace_to_ndc_fn(self) -> mathutils.InvertibleFunction[Vector3D]:
        return mathutils.compose(*self.stack)


fn_stack = FunctionStack()
# doc-region-end define function stack class


@contextmanager
def push_transformation(f):
    try:
        fn_stack.push(f)
        yield fn_stack
    finally:
        fn_stack.pop()
