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

window = glfw.create_window(500, 500, "ModelViewProjection Demo 11", None, None)
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


@dataclass
class Vertex:
    x: float
    y: float

    def translate(self: Vertex, tx: float, ty: float) -> Vertex:
        return Vertex(x=self.x + tx, y=self.y + ty)

    def scale(self: Vertex, scale_x: float, scale_y: float) -> Vertex:
        return Vertex(x=self.x * scale_x, y=self.y * scale_y)

    def rotate(self: Vertex, angle_in_radians: float) -> Vertex:
        return Vertex(
            x=self.x * math.cos(angle_in_radians) - self.y * math.sin(angle_in_radians),
            y=self.x * math.sin(angle_in_radians) + self.y * math.cos(angle_in_radians),
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
        Vertex(x=-10.0, y=-30.0),
        Vertex(x=10.0, y=-30.0),
        Vertex(x=10.0, y=30.0),
        Vertex(x=-10.0, y=30.0),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
    position=Vertex(-90.0, 0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vertex(x=-10.0, y=-30.0),
        Vertex(x=10.0, y=-30.0),
        Vertex(x=10.0, y=30.0),
        Vertex(x=-10.0, y=30.0),
    ],
    r=1.0,
    g=0.0,
    b=0.0,
    position=Vertex(90.0, 0.0),
)


@dataclass
class Camera:
    position_worldspace: Vertex = field(default_factory=lambda: Vertex(x=0.0, y=0.0))


camera: Camera = Camera()


# doc-region-begin 3bb2c05b4cd66636ad8b8fc18c26f7a64af06b7c
square: Paddle = [
    Vertex(x=-5.0, y=-5.0),
    Vertex(x=5.0, y=-5.0),
    Vertex(x=5.0, y=5.0),
    Vertex(x=-5.0, y=5.0),
]
# doc-region-end 3bb2c05b4cd66636ad8b8fc18c26f7a64af06b7c


def handle_inputs() -> None:
    global camera

    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.position_worldspace.y += 10.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_worldspace.y -= 10.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.position_worldspace.x -= 10.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.position_worldspace.x += 10.0

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position.y -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position.y += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position.y -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position.y += 10.0

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

# doc-region-begin 67ffd7b7adc42d01ca93bacdef858c0d4b678e38
while not glfw.window_should_close(window):
    # doc-region-end 67ffd7b7adc42d01ca93bacdef858c0d4b678e38

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
    # doc-region-begin 7dab1135450b265814f775c59807f77b44273a4e
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        world_space: Vertex = model_space.rotate(paddle1.rotation) \
                                         .translate(tx=paddle1.position.x,
                                                    ty=paddle1.position.y)
        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y)
        ndc_space: Vertex = camera_space.scale(scale_x=1.0 / 100.0,
                                               scale_y=1.0 / 100.0)
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # doc-region-end 7dab1135450b265814f775c59807f77b44273a4e
    # fmt: on

    # fmt: off
    # doc-region-begin 9a0ba48a086f35a4515bf32b4a856888c178b0e8
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_QUADS)
    for model_space in square:
        paddle1space: Vertex = model_space.translate(tx=20.0,
                                                     ty=0.0)
        world_space: Vertex = paddle1space.rotate(paddle1.rotation) \
                                          .translate(tx=paddle1.position.x,
                                                     ty=paddle1.position.y)
        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y)
        ndc_space: Vertex = camera_space.scale(scale_x=1.0 / 100.0,
                                               scale_y=1.0 / 100.0)
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # doc-region-end 9a0ba48a086f35a4515bf32b4a856888c178b0e8
    # fmt: on

    # fmt: off
    # doc-region-begin 12cd2bedfe522c8c192106296c12e8344f1594d4
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        world_space: Vertex = model_space.rotate(paddle2.rotation) \
                                         .translate(tx=paddle2.position.x,
                                                    ty=paddle2.position.y)
        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y)
        ndc_space: Vertex = camera_space.scale(scale_x=1.0 / 100.0,
                                               scale_y=1.0 / 100.0)
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # doc-region-end 12cd2bedfe522c8c192106296c12e8344f1594d4
    # fmt: on

    glfw.swap_buffers(window)

glfw.terminate()
