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
from dataclasses import dataclass


def compose(*functions):
    def inner(arg):
        for f in reversed(functions):
            arg = f(arg)
        return arg

    return inner


@dataclass
class Vertex3D:
    x: float
    y: float
    z: float

    def __add__(self, rhs: Vertex3D) -> Vertex3D:
        return Vertex3D(x=(self.x + rhs.x), y=(vertex.y + rhs.y), z=(vertex.z + rhs.z))

    def __mul__(vertex, scalar: float) -> Vertex3D:
        return Vertex3D(
            x=(vertex.x * scalar), y=(vertex.y * scalar), z=(vertex.z * scalar)
        )

    def __rmul__(vertex, scalar: float) -> Vertex3D:
        return vertex * scalar

    def __neg__(vertex):
        return -1.0 * vertex


def translate(vertex: Vertex3D, translate_amount: Vertex3D) -> Vertex3D:
    return vertex + translate_amount


def rotate_x(vertex: Vertex3D, angle_in_radians: float) -> Vertex3D:
    yz_on_xy: Vertex3D = Vertex3D(x=vertex.y, y=vertex.z).rotate(angle_in_radians)
    return Vertex3D(x=vertex.x, y=yz_on_xy.x, z=yz_on_xy.y)


def rotate_y(vertex: Vertex3D, angle_in_radians: float) -> Vertex3D:
    zx_on_xy: Vertex3D = Vertex3D(x=vertex.z, y=vertex.x).rotate(angle_in_radians)
    return Vertex3D(x=zx_on_xy.y, y=vertex.y, z=zx_on_xy.x)


def rotate_z(vertex: Vertex3D, angle_in_radians: float) -> Vertex3D:
    xy_on_xy: Vertex3D = Vertex3D(x=vertex.x, y=vertex.y).rotate(angle_in_radians)
    return Vertex3D(x=xy_on_xy.x, y=xy_on_xy.y, z=vertex.z)


def uniform_scale(vertex: Vertex3D, scalar: float) -> Vertex3D:
    return vertex * scalar


def scale(vertex: Vertex3D, scale_x: float, scale_y: float, scale_z: float) -> Vertex3D:
    return Vertex3D(
        x=(vertex.x * scale_x), y=(vertex.y * scale_y), z=(vertex.z * scale_z)
    )


# fmt: off
def ortho(vertex: Vertex3D,
          left: float,
          right: float,
          bottom: float,
          top: float,
          near: float,
          far: float,
          ) -> Vertex3D:
    midpoint = Vertex3D(
        x=(left + right) / 2.0,
        y=(bottom + top) / 2.0,
        z=(near + far) / 2.0
    )
    length_x: float
    length_y: float
    length_z: float
    length_x, length_y, length_z = right - left, top - bottom, far - near
    return vertex.translate(-midpoint) \
                 .scale(2.0 / length_x,
                        2.0 / length_y,
                        2.0 / (-length_z))
# fmt: on


# fmt: off
def perspective(vertex: Vertex3D,
                field_of_view: float,
                aspect_ratio: float,
                near_z: float,
                far_z: float) -> Vertex3D:
    # field_of_view, field of view, is angle of y
    # aspect_ratio is x_width / y_width

    top: float = -near_z * math.tan(math.radians(field_of_view) / 2.0)
    right: float = top * aspect_ratio

    scaled_x: float = vertex.x / vertex.z * near_z
    scaled_y: float = vertex.y / vertex.z * near_z
    rectangular_prism: Vertex3D = Vertex3D(scaled_x,
                                           scaled_y,
                                           vertex.z)

    return rectangular_prism.ortho(left=-right,
                                   right=right,
                                   bottom=-top,
                                   top=top,
                                   near=near_z,
                                   far=far_z)

def cs_to_ndc_space_fn(vertex: Vertex3D) -> Vertex3D:
    return vertex.perspective(field_of_view=45.0,
                              aspect_ratio=1.0,
                              near_z=-.1,
                              far_z=-1000.0)
# fmt: on
