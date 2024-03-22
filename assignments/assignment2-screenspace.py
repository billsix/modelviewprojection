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
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glEnd,
    glLoadIdentity,
    glMatrixMode,
    glVertex2f,
    glViewport,
)
from OpenGL.GLU import gluOrtho2D

KEEP_ASPECT_RATIO = False

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Assignment 2", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0289, 0.071875, 0.0972, 1.0)


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

    def ndc_to_screenspace_full_screen(self: Vertex, width: float, height: float):
        return self

    def ndc_to_screenspace_aspect_not_distorted(
        self: Vertex, width: float, height: float
    ):
        return self


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


# doc-region-begin 808b49966faf68394a1e4def233df33c08e37b27
def _default_camera_position() -> Vertex:
    return Vertex(x=0.0, y=0.0)


@dataclass
class Camera:
    position_worldspace: Vertex = field(default_factory=_default_camera_position)
    # doc-region-end 808b49966faf68394a1e4def233df33c08e37b27


camera: Camera = Camera()


# doc-region-begin e705ab925d5c7f3219b065cdf16eb13268f17ef9
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
    # doc-region-end e705ab925d5c7f3219b065cdf16eb13268f17ef9
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

# doc-region-begin 6d86d07154c99ed6e1c3feab73545d184153f9ae
while not glfw.window_should_close(window):
    # doc-region-end 6d86d07154c99ed6e1c3feab73545d184153f9ae
    while (
        glfw.get_time() < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass

    time_at_beginning_of_previous_frame = glfw.get_time()

    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    minimum_framebuffer_dimension = width if width < height else height

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluOrtho2D(0.0, float(width), 0.0, float(height))

    handle_inputs()

    # fmt: off
    # doc-region-begin c1994fe03bc9e4428893f63706e07eb1d3bb14b5
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        world_space: Vertex = model_space.rotate(paddle1.rotation) \
                                         .translate(tx=paddle1.position.x,ty=paddle1.position.y)
        # doc-region-end c1994fe03bc9e4428893f63706e07eb1d3bb14b5
        # doc-region-begin 9624d3a2dd009e3850cd5dce4470272fb9d9b4e0
        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y)
        # doc-region-end 9624d3a2dd009e3850cd5dce4470272fb9d9b4e0
        # doc-region-begin 4db386e7523575f5ab67841165a5297c8c0e1500
        ndc_space: Vertex = camera_space.scale(scale_x=1.0 / 100.0,
                                               scale_y=1.0 / 100.0)
        if not KEEP_ASPECT_RATIO:
            screen_space: Vertex = ndc_space.ndc_to_screenspace_full_screen(width, height)
        else:
            screen_space: Vertex = ndc_space.ndc_to_screenspace_aspect_not_distorted(width, height)
        glVertex2f(screen_space.x, screen_space.y)
    glEnd()
    # doc-region-end 4db386e7523575f5ab67841165a5297c8c0e1500
    # fmt: on

    # fmt: off
    # doc-region-begin 63cbaad0dbecc69f52bc428648308a48337e43c6
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        world_space: Vertex = model_space.rotate(paddle2.rotation) \
                                         .translate(tx=paddle2.position.x,
                                                    ty=paddle2.position.y)
        # doc-region-end 63cbaad0dbecc69f52bc428648308a48337e43c6
        # doc-region-begin ad53fd8251cc2c93fffec19223c3e70270e31410
        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y)
        # doc-region-end ad53fd8251cc2c93fffec19223c3e70270e31410
        ndc_space: Vertex = camera_space.scale(scale_x=1.0 / 100.0,
                                               scale_y=1.0 / 100.0)
        # fmt: on
        # doc-region-begin 46159451e06ea71fbb3fc270b01f3b755a06040c
        if not KEEP_ASPECT_RATIO:
            screen_space: Vertex = ndc_space.ndc_to_screenspace_full_screen(width, height)
        else:
            screen_space: Vertex = ndc_space.ndc_to_screenspace_aspect_not_distorted(width, height)
        glVertex2f(screen_space.x, screen_space.y)
    glEnd()
    # doc-region-end 46159451e06ea71fbb3fc270b01f3b755a06040c

    glfw.swap_buffers(window)

glfw.terminate()
