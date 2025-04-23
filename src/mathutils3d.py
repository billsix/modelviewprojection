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

import math
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, List

from mathutils import InvertibleFunction, Vector2D, compose, inverse
from mathutils import rotate as rotate2D


# doc-region-begin define vector class
@dataclass
class Vector3D:
    x: float
    y: float
    z: float

    def __add__(self, rhs: Vector3D) -> Vector3D:
        return Vector3D(
            x=(self.x + rhs.x), y=(self.y + rhs.y), z=(self.z + rhs.z)
        )

    def __sub__(self, rhs: Vector3D) -> Vector3D:
        return Vector3D(
            x=(self.x - rhs.x), y=(self.y - rhs.y), z=(self.z - rhs.z)
        )

    def __mul__(vector, scalar: float) -> Vector3D:
        return Vector3D(
            x=(vector.x * scalar), y=(vector.y * scalar), z=(vector.z * scalar)
        )

    def __rmul__(vector, scalar: float) -> Vector3D:
        return vector * scalar

    def __neg__(vector):
        return -1.0 * vector


def translate(translate_amount: Vector3D) -> InvertibleFunction:
    def f(vector: Vector3D) -> Vector3D:
        return vector + translate_amount

    def f_inv(vector: Vector3D) -> Vector3D:
        return vector - translate_amount

    return InvertibleFunction(f, f_inv)


# doc-region-end define vector class


# doc-region-begin define rotate x
def rotate_x(angle_in_radians: float) -> Vector3D:
    fn = rotate2D(angle_in_radians)

    def f(vector: Vector3D) -> Vector3D:
        yz_on_xy: Vector2D = fn(Vector2D(x=vector.y, y=vector.z))
        return Vector3D(x=vector.x, y=yz_on_xy.x, z=yz_on_xy.y)

    def f_inv(vector: Vector3D) -> Vector3D:
        yz_on_xy: Vector2D = inverse(fn)(Vector2D(x=vector.y, y=vector.z))
        return Vector3D(x=vector.x, y=yz_on_xy.x, z=yz_on_xy.y)

    return InvertibleFunction(f, f_inv)


# doc-region-end define rotate x


# doc-region-begin define rotate y
def rotate_y(angle_in_radians: float) -> Vector3D:
    fn = rotate2D(angle_in_radians)

    def f(vector: Vector3D) -> Vector3D:
        zx_on_xy: Vector2D = fn(Vector2D(x=vector.z, y=vector.x))
        return Vector3D(x=zx_on_xy.y, y=vector.y, z=zx_on_xy.x)

    def f_inv(vector: Vector3D) -> Vector3D:
        zx_on_xy: Vector2D = inverse(fn)(Vector2D(x=vector.z, y=vector.x))
        return Vector3D(x=zx_on_xy.y, y=vector.y, z=zx_on_xy.x)

    return InvertibleFunction(f, f_inv)


# doc-region-end define rotate y


# doc-region-begin define rotate z
def rotate_z(angle_in_radians: float) -> Vector3D:
    fn = rotate2D(angle_in_radians)

    def f(vector: Vector3D) -> Vector3D:
        xy_on_xy: Vector2D = fn(Vector2D(x=vector.x, y=vector.y))
        return Vector3D(x=xy_on_xy.x, y=xy_on_xy.y, z=vector.z)

    def f_inv(vector: Vector3D) -> Vector3D:
        xy_on_xy: Vector2D = inverse(fn)(Vector2D(x=vector.x, y=vector.y))
        return Vector3D(x=xy_on_xy.x, y=xy_on_xy.y, z=vector.z)

    return InvertibleFunction(f, f_inv)


# doc-region-end define rotate z


# doc-region-begin define uniform scale
def uniform_scale(scalar: float) -> InvertibleFunction:
    if scalar == 0:
        raise ValueError("Scaling factor cannot be zero.")

    def f(vector: Vector3D) -> Vector3D:
        return vector * scalar

    def f_inv(vector: Vector3D) -> Vector3D:
        return vector / scalar

    return InvertibleFunction(f, f_inv)


# doc-region-end define uniform scale


def scale(scale_x: float, scale_y: float, scale_z: float) -> Vector3D:
    if scale_x == 0:
        raise ValueError("Scale_x cannot be zero.")
    if scale_y == 0:
        raise ValueError("Scale_y cannot be zero.")
    if scale_z == 0:
        raise ValueError("Scale_z cannot be zero.")

    def f(vector: Vector3D) -> Vector3D:
        return Vector3D(
            x=(vector.x * scale_x),
            y=(vector.y * scale_y),
            z=(vector.z * scale_z),
        )

    def f_inv(vector: Vector3D) -> Vector3D:
        return Vector3D(
            x=(vector.x / scale_x),
            y=(vector.y / scale_y),
            z=(vector.z / scale_z),
        )

    return InvertibleFunction(f, f_inv)


# doc-region-begin define ortho
def ortho(
    left: float,
    right: float,
    bottom: float,
    top: float,
    near: float,
    far: float,
) -> Vector3D:
    # fmt: off
    midpoint = Vector3D(x=(left + right) / 2.0,
                        y=(bottom + top) / 2.0,
                        z=(near + far) / 2.0)
    # fmt: on
    length_x: float
    length_y: float
    length_z: float
    length_x, length_y, length_z = right - left, top - bottom, far - near

    # fmt: off
    fn = compose(scale(scale_x=(2.0 / length_x),
                       scale_y=(2.0 / length_y),
                       scale_z=(2.0 / (-length_z))),
                 translate(-midpoint))
    # fmt: on

    def f(vector: Vector3D) -> Vector3D:
        return fn(vector)

    def f_inv(vector: Vector3D) -> Vector3D:
        return f_inv(fn)(vector)

    return InvertibleFunction(f, f_inv)


# doc-region-end define ortho


def perspective(
    field_of_view: float, aspect_ratio: float, near_z: float, far_z: float
) -> Vector3D:
    # field_of_view, field of view, is angle of y
    # aspect_ratio is x_width / y_width

    top: float = -near_z * math.tan(math.radians(field_of_view) / 2.0)
    right: float = top * aspect_ratio

    def f(vector: Vector3D) -> Vector3D:
        scaled_x: float = vector.x / vector.z * near_z
        scaled_y: float = vector.y / vector.z * near_z
        rectangular_prism: Vector3D = Vector3D(scaled_x, scaled_y, vector.z)

        fn = ortho(
            left=-right,
            right=right,
            bottom=-top,
            top=top,
            near=near_z,
            far=far_z,
        )
        return fn(rectangular_prism)

    def f_inv(vector: Vector3D) -> Vector3D:
        raise ValueError("Inverse_Inner Perspective not yet implement")

    return InvertibleFunction(f, f_inv)


def cs_to_ndc_space_fn(vector: Vector3D) -> Vector3D:
    def f(vector: Vector3D) -> Vector3D:
        fn = perspective(
            field_of_view=45.0, aspect_ratio=1.0, near_z=-0.1, far_z=-1000.0
        )
        return fn(vector)

    def f_inv(vector: Vector3D) -> Vector3D:
        raise ValueError("Inverse_Inner cs_to_ndc_spcae_fn not yet implement")

    return InvertibleFunction(f, f_inv)


# doc-region-begin define function stack class
@dataclass
class FunctionStack:
    stack: List[Callable[Vector3D, Vector3D]] = field(
        default_factory=lambda: []
    )

    def push(self, o: object):
        self.stack.append(o)

    def pop(self):
        return self.stack.pop()

    def clear(self):
        self.stack.clear()

    def modelspace_to_ndc_fn(self) -> Callable[Vector3D, Vector3D]:
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
