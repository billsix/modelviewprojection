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
from dataclasses import dataclass

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

window = glfw.create_window(500, 500, "ModelViewProjection Demo 7", None, None)
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


# doc-region-begin 0650dc123c5604096222ab7f34523251869be0e3
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

    def rotate_90_degrees(self: Vertex):
        return Vertex(x=-self.y, y=self.x)

    # fmt: off
    def rotate(self: Vertex, angle_in_radians: float) -> Vertex:
        return math.cos(angle_in_radians) * self + math.sin(angle_in_radians) * self.rotate_90_degrees()
    # fmt: on

    # doc-region-end 0650dc123c5604096222ab7f34523251869be0e3


# doc-region-begin cf32927e5bb15098767fad214706f03ddfe49a1c
@dataclass
class Paddle:
    vertices: list[Vertex]
    r: float
    g: float
    b: float
    position: Vertex
    rotation: float = 0.0
    # doc-region-end cf32927e5bb15098767fad214706f03ddfe49a1c


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
    g=0.0,
    b=0.0,
    position=Vertex(9.0, 0.0),
)


# doc-region-begin 1cf68248b869564df5f3133b98adb2e06601ed3b
def handle_movement_of_paddles() -> None:
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
    # doc-region-end 1cf68248b869564df5f3133b98adb2e06601ed3b


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
    handle_movement_of_paddles()

    # doc-region-begin 4ae8b0ebe66cd4de6b0150ac5cd4fa92abdd9985
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        # doc-region-end 4ae8b0ebe66cd4de6b0150ac5cd4fa92abdd9985
        # fmt: off
        # doc-region-begin 1699ece7b62ace3842c391a972f2d27c5e022993
        world_space: Vertex = model_space.translate(translate_amount=paddle1.position) \
                                         .rotate(paddle1.rotation)
        # doc-region-end 1699ece7b62ace3842c391a972f2d27c5e022993
        # fmt: on
        # fmt: off
        # doc-region-begin ff2784cf4a98bfbaa9a63073ec0b915197f34c5d
        ndc_space: Vertex = world_space.scale(scale_x=1.0 / 10.0,
                                              scale_y=1.0 / 10.0)
        # doc-region-end ff2784cf4a98bfbaa9a63073ec0b915197f34c5d
        # fmt: on
        # doc-region-begin 46159451e06ea71fbb3fc270b01f3b755a06040c
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # doc-region-end 46159451e06ea71fbb3fc270b01f3b755a06040c

    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    # doc-region-begin dd17b8cf2992da4f0752dd3f54dba416a5f04d64
    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        # doc-region-end dd17b8cf2992da4f0752dd3f54dba416a5f04d64
        # fmt: off
        # doc-region-begin 2bfcc6ef8f40e5cd45e7f921e9978db7184b860c
        world_space: Vertex = model_space.translate(paddle2.position) \
                                         .rotate(paddle2.rotation)
        # doc-region-end 2bfcc6ef8f40e5cd45e7f921e9978db7184b860c
        # fmt: on
        # fmt: off
        # doc-region-begin 0ae0fb2528f9b972bdb4901b83e93f63266e2ed7
        ndc_space: Vertex = world_space.scale(scale_x=1.0 / 10.0,
                                              scale_y=1.0 / 10.0)
        # doc-region-end 0ae0fb2528f9b972bdb4901b83e93f63266e2ed7
        # fmt: on
        # doc-region-begin 696e8248badabab740bf65566030cf31d8bae2f2
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # doc-region-end 696e8248badabab740bf65566030cf31d8bae2f2
    glfw.swap_buffers(window)

glfw.terminate()
