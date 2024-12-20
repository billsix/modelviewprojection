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
    glViewport,
)

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 13", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0289, 0.071875, 0.0972, 1.0)


glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()


def draw_in_square_viewport() -> None:
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    w, h = glfw.get_framebuffer_size(window)
    minimal_dimension = w if w < h else h

    glEnable(GL_SCISSOR_TEST)
    glScissor(
        int((w - minimal_dimension) / 2.0),
        int((h - minimal_dimension) / 2.0),
        minimal_dimension,
        minimal_dimension,
    )

    glClearColor(0.0289, 0.071875, 0.0972, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    glViewport(
        int(0.0 + (w - minimal_dimension) / 2.0),
        int(0.0 + (h - minimal_dimension) / 2.0),
        minimal_dimension,
        minimal_dimension,
    )


@dataclass
class Vertex:
    x: float
    y: float

    def __add__(self, rhs: Vertex) -> Vertex:
        return Vertex(x=self.x + rhs.x, y=self.y + rhs.y)

    def translate(self: Vertex, translate_amount: Vertex) -> Vertex:
        return self + translate_amount

    def __mul__(self, scalar: float) -> Vertex:
        return Vertex(x=self.x * scalar, y=self.y * scalar)

    def __rmul__(self, scalar: float) -> Vertex:
        return self * scalar

    def uniform_scale(self: Vertex, scalar: float) -> Vertex:
        return self * scalar

    def scale(self: Vertex, scale_x: float, scale_y: float) -> Vertex:
        return Vertex(x=self.x * scale_x, y=self.y * scale_y)

    def __neg__(self):
        return -1.0 * self

    def rotate_90_degrees(self: Vertex):
        return Vertex(x=-self.y, y=self.x)

    def rotate(self: Vertex, angle_in_radians: float) -> Vertex:
        return (
            math.cos(angle_in_radians) * self
            + math.sin(angle_in_radians) * self.rotate_90_degrees()
        )


@dataclass
class Paddle:
    vertices: list[Vertex]
    r: float
    g: float
    b: float
    position: Vertex
    rotation: float = 0.0


paddle1: Paddle = Paddle(
    vertices=[
        Vertex(x=-1.0, y=-3.0),
        Vertex(x=1.0, y=-3.0),
        Vertex(x=1.0, y=3.0),
        Vertex(x=-1.0, y=3.0),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
    position=Vertex(-9.0, 0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vertex(x=-1.0, y=-3.0),
        Vertex(x=1.0, y=-3.0),
        Vertex(x=1.0, y=3.0),
        Vertex(x=-1.0, y=3.0),
    ],
    r=1.0,
    g=1.0,
    b=0.0,
    position=Vertex(9.0, 0.0),
)


@dataclass
class Camera:
    position_worldspace: Vertex = field(default_factory=lambda: Vertex(x=0.0, y=0.0))


camera: Camera = Camera()


square: list[Vertex] = [
    Vertex(x=-0.5, y=-0.5),
    Vertex(x=0.5, y=-0.5),
    Vertex(x=0.5, y=0.5),
    Vertex(x=-0.5, y=0.5),
]
square_rotation: float = 0.0
# doc-region-begin define variable for square rotation around paddle's center
rotation_around_paddle1: float = 0.0
# doc-region-end define variable for square rotation around paddle's center


def handle_inputs():
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

# doc-region-begin begin event loop
while not glfw.window_should_close(window):
    # doc-region-end begin event loop
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

    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for paddle1_vertex_in_model_space in paddle1.vertices:
        paddle1_vertex_in_world_space: Vertex = paddle1_vertex_in_model_space.rotate(
            paddle1.rotation
        ).translate(paddle1.position)
        paddle1_vertex_in_camera_space: Vertex = (
            paddle1_vertex_in_world_space.translate(-camera.position_worldspace)
        )
        paddle1_vertex_in_ndc_space: Vertex = (
            paddle1_vertex_in_camera_space.uniform_scale(scalar=1.0 / 10.0)
        )
        glVertex2f(paddle1_vertex_in_ndc_space.x, paddle1_vertex_in_ndc_space.y)
    glEnd()

    # fmt: off
    # doc-region-begin draw square
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_QUADS)
    for square_vertex_in_model_space in square:
        paddle_1_space: Vertex = square_vertex_in_model_space.rotate(square_rotation) \
                                                             .translate(Vertex(x=2.0, y=0.0)) \
                                                             .rotate(rotation_around_paddle1)
        world_space: Vertex = paddle_1_space.rotate(paddle1.rotation) \
                                            .translate(paddle1.position)
        camera_space: Vertex = world_space.translate(-camera.position_worldspace)
        ndc_space: Vertex = camera_space.uniform_scale(scalar=1.0/10.0)
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # doc-region-end draw square
    # fmt: on

    # fmt: off
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for paddle2_vertex_model_space in paddle2.vertices:
        paddle2_vertex_world_space: Vertex = paddle2_vertex_model_space.rotate(paddle2.rotation) \
                                                                       .translate(paddle2.position)
        paddle2_vertex_camera_space: Vertex = paddle2_vertex_world_space.translate(-camera.position_worldspace)
        paddle2_vertex_ndc_space: Vertex = paddle2_vertex_camera_space.uniform_scale(scalar=1.0/10.0)
        glVertex2f(paddle2_vertex_ndc_space.x, paddle2_vertex_ndc_space.y)
    glEnd()
    # fmt: on

    glfw.swap_buffers(window)

glfw.terminate()
