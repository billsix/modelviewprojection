
# Copyright (c) 2018-2024 William Emerison Six
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
import sys
from dataclasses import dataclass, field

import glfw
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    GL_SCISSOR_TEST,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glLoadIdentity,
    glMatrixMode,
    glScissor,
    glVertex2f,
    glVertex3f,
    glViewport,
)

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 14", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0289, 0.071875, 0.0972, 1.0)


glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()


def draw_in_square_viewport() -> None:
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)
    min = width if width < height else height

    glEnable(GL_SCISSOR_TEST)
    glScissor(
        int((width - min) / 2.0),
        int((height - min) / 2.0),
        min,
        min,
    )

    glClearColor(0.0289, 0.071875, 0.0972, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    glViewport(
        int(0.0 + (width - min) / 2.0),
        int(0.0 + (height - min) / 2.0),
        min,
        min,
    )


# doc-region-begin d38e00f1c19bce775ae4216e4ed95a31a814eee0
@dataclass
class Vertex2D:
    x: float
    y: float

    def __add__(self, rhs: Vertex2D) -> Vertex2D:
        return Vertex2D(x=self.x + rhs.x, y=self.y + rhs.y)

    def translate(self: Vertex2D, translate_amount: Vertex2D) -> Vertex2D:
        return self + translate_amount

    def __mul__(self, scalar: float) -> Vertex2D:
        return Vertex2D(x=self.x * scalar, y=self.y * scalar)

    def __rmul__(self, scalar: float) -> Vertex2D:
        return self * scalar

    def uniform_scale(self: Vertex2D, scalar: float) -> Vertex2D:
        return self * scalar

    def scale(self: Vertex2D, scale_x: float, scale_y: float) -> Vertex2D:
        return Vertex2D(x=self.x * scale_x, y=self.y * scale_y)

    def __neg__(self):
        return -1.0 * self

    def rotate_90_degrees(self: Vertex2D):
        return Vertex2D(x=-self.y, y=self.x)

    def rotate(self: Vertex2D, angle_in_radians: float) -> Vertex2D:
        return (
            math.cos(angle_in_radians) * self
            + math.sin(angle_in_radians) * self.rotate_90_degrees()
        )


@dataclass
class Vertex:
    x: float
    y: float
    z: float

    def __add__(self, rhs: Vertex) -> Vertex:
        return Vertex(x=self.x + rhs.x, y=self.y + rhs.y, z=self.z + rhs.z)

    def translate(self: Vertex, translate_amount: Vertex) -> Vertex:
        return self + translate_amount

    # doc-region-end d38e00f1c19bce775ae4216e4ed95a31a814eee0

    # doc-region-begin 3e09ecd4a77c68066fe97bfa4f06e89afb583f9d
    def rotate_x(self: Vertex, angle_in_radians: float) -> Vertex:
        yz_on_xy: Vertex2D = Vertex2D(x=self.y, y=self.z).rotate(angle_in_radians)
        return Vertex(x=self.x, y=yz_on_xy.x, z=yz_on_xy.y)

    # doc-region-end 3e09ecd4a77c68066fe97bfa4f06e89afb583f9d

    # doc-region-begin 256be1d4ab5b90068be656bb99ff1115268d8925
    def rotate_y(self: Vertex, angle_in_radians: float) -> Vertex:
        zx_on_xy: Vertex2D = Vertex2D(x=self.z, y=self.x).rotate(angle_in_radians)
        return Vertex(x=zx_on_xy.y, y=self.y, z=zx_on_xy.y)

    # doc-region-end 256be1d4ab5b90068be656bb99ff1115268d8925

    # doc-region-begin 1b96b48e7e572197721cad2a7d082f167159f2d8
    def rotate_z(self: Vertex, angle_in_radians: float) -> Vertex:
        xy_on_xy: Vertex2D = Vertex2D(x=self.x, y=self.y).rotate(angle_in_radians)
        return Vertex(x=xy_on_xy.x, y=xy_on_xy.y, z=self.z)

    # doc-region-end 1b96b48e7e572197721cad2a7d082f167159f2d8

    # doc-region-begin dd45247963bb4a02bf2430d98a7f52e707c9e15a

    def __mul__(self, scalar: float) -> Vertex:
        return Vertex(x=self.x * scalar, y=self.y * scalar, z=self.z * scalar)

    def __rmul__(self, scalar: float) -> Vertex:
        return self * scalar

    def uniform_scale(self: Vertex, scalar: float) -> Vertex:
        return self * scalar

    def scale(self: Vertex, scale_x: float, scale_y: float, scale_z: float) -> Vertex:
        return Vertex(x=self.x * scale_x, y=self.y * scale_y, z=self.z * scale_z)

    def __neg__(self):
        return -1.0 * self

    # doc-region-end dd45247963bb4a02bf2430d98a7f52e707c9e15a


@dataclass
class Paddle:
    vertices: list[Vertex]
    r: float
    g: float
    b: float
    position: Vertex
    rotation: float = 0.0


# doc-region-begin d5bd9d04649181c42a65f8a7d52125a0ef86a928
paddle1: Paddle = Paddle(
    vertices=[
        Vertex(x=-1.0, y=-3.0, z=0.0),
        Vertex(x=1.0, y=-3.0, z=0.0),
        Vertex(x=1.0, y=3.0, z=0.0),
        Vertex(x=-1.0, y=3.0, z=0.0),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
    position=Vertex(x=-9.0, y=0.0, z=0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vertex(x=-1.0, y=-3.0, z=0.0),
        Vertex(x=1.0, y=-3.0, z=0.0),
        Vertex(x=1.0, y=3.0, z=0.0),
        Vertex(x=-1.0, y=3.0, z=0.0),
    ],
    r=1.0,
    g=1.0,
    b=0.0,
    position=Vertex(x=9.0, y=0.0, z=0.0),
)
# doc-region-end d5bd9d04649181c42a65f8a7d52125a0ef86a928


# doc-region-begin 89d28adbbb797e4128facc7ee1497e4f2d469eff
@dataclass
class Camera:
    position_worldspace: Vertex = field(
        default_factory=lambda: Vertex(x=0.0, y=0.0, z=0.0)
    )


camera: Camera = Camera()
# doc-region-end 89d28adbbb797e4128facc7ee1497e4f2d469eff

# doc-region-begin 603eda05b403ac6bd756d050f26d9e6497bf748a
square: Paddle = [
    Vertex(x=-0.5, y=-0.5, z=0.0),
    Vertex(x=0.5, y=-0.5, z=0.0),
    Vertex(x=0.5, y=0.5, z=0.0),
    Vertex(x=-0.5, y=0.5, z=0.0),
]
# doc-region-end 603eda05b403ac6bd756d050f26d9e6497bf748a

square_rotation: float = 0.0
rotation_around_paddle1: float = 0.0


def handle_inputs() -> None:
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera

    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.position_worldspace.y += 1.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_worldspace.y -= 1.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.position_worldspace.x -= 1.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.position_worldspace.x += 1.0

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position.y -= 1.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position.y += 1.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position.y -= 1.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position.y += 1.0

    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1


TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()

# doc-region-begin ee882a76ee2962c327841e2a952998acce07cc2a
while not glfw.window_should_close(window):
    # doc-region-end ee882a76ee2962c327841e2a952998acce07cc2a
    while (
        glfw.get_time() < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass

    time_at_beginning_of_previous_frame = glfw.get_time()

    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    draw_in_square_viewport()
    handle_inputs()

    # fmt: off
    # doc-region-begin 2f5cb93361c42475b16dec8246c81c711b1a2db3
    glColor3f(paddle1.r, paddle1.g, paddle1.b)
    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        world_space: Vertex = model_space.rotate_z(paddle1.rotation) \
                                         .translate(paddle1.position)
        camera_space: Vertex = world_space.translate(-camera.position_worldspace)
        ndc_space: Vertex = camera_space.uniform_scale(scalar=1.0 / 10.0)
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # doc-region-end 2f5cb93361c42475b16dec8246c81c711b1a2db3
    # fmt: on

    # fmt: off
    # doc-region-begin 485064c9e30f4471b74d11b8cca3c8f0d142b552
    # draw square
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_QUADS)
    for model_space in square:
        paddle_1_space: Vertex =  model_space.rotate_z(square_rotation) \
                                             .translate(Vertex(x=2.0,
                                                               y=0.0,
                                                               z=0.0)) \
                                             .rotate_z(rotation_around_paddle1) \
                                             .translate(Vertex(x=0.0,
                                                               y=0.0,
                                                               z=-1.0))
        world_space: Vertex = paddle_1_space.rotate_z(paddle1.rotation) \
                                            .translate(paddle1.position)
        camera_space: Vertex = world_space.translate(-camera.position_worldspace)
        ndc_space: Vertex = camera_space.uniform_scale(scalar=1.0 / 10.0)
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end 485064c9e30f4471b74d11b8cca3c8f0d142b552
    # fmt: on

    # fmt: off
    # doc-region-begin 79bca06683ced2f641ea47f14d22bc330f75979f
    # draw paddle 2
    glColor3f(paddle2.r, paddle2.g, paddle2.b)
    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        world_space: Vertex = model_space.rotate_z(paddle2.rotation) \
                                         .translate(paddle2.position)
        camera_space: Vertex = world_space.translate(-camera.position_worldspace)
        ndc_space: Vertex = camera_space.uniform_scale(scalar=1.0 / 10.0)
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end 79bca06683ced2f641ea47f14d22bc330f75979f
    # fmt: off

    glfw.swap_buffers(window)

glfw.terminate()
