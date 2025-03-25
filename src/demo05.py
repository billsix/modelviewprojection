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

from mathutils import Vertex2D, translate

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 5", None, None)
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


# doc-region-begin define paddle class
@dataclass
class Paddle:
    vertices: list[Vertex2D]
    r: float
    g: float
    b: float
    position: Vertex2D


# doc-region-end define paddle class

# doc-region-begin instantiate paddles
paddle1: Paddle = Paddle(
    vertices=[
        Vertex2D(x=-0.1, y=-0.3),
        Vertex2D(x=0.1, y=-0.3),
        Vertex2D(x=0.1, y=0.3),
        Vertex2D(x=-0.1, y=0.3),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
    position=Vertex2D(-0.9, 0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vertex2D(-0.1, -0.3),
        Vertex2D(0.1, -0.3),
        Vertex2D(0.1, 0.3),
        Vertex2D(-0.1, 0.3),
    ],
    r=1.0,
    g=1.0,
    b=0.0,
    position=Vertex2D(0.9, 0.0),
)
# doc-region-end instantiate paddles


# doc-region-begin define handle movement of paddles
def handle_movement_of_paddles() -> None:
    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position.y -= 0.1
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position.y += 0.1
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position.y -= 0.1
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position.y += 0.1


# doc-region-end define handle movement of paddles

TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()

# doc-region-begin begin event loop
while not glfw.window_should_close(window):
    while (
        glfw.get_time()
        < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass

    time_at_beginning_of_previous_frame = glfw.get_time()

    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    draw_in_square_viewport()
    handle_movement_of_paddles()
    # doc-region-end begin event loop

    # doc-region-begin draw paddle 1
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        paddle1_vertex_ndc: Vertex2D = translate(paddle1.position)(p1_v_ms)
        glVertex2f(paddle1_vertex_ndc.x, paddle1_vertex_ndc.y)
    glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin draw paddle 2
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        paddle2_vertex_ndc: Vertex2D = translate(paddle2.position)(p2_v_ms)
        glVertex2f(paddle2_vertex_ndc.x, paddle2_vertex_ndc.y)
    glEnd()
    # doc-region-end draw paddle 2

    glfw.swap_buffers(window)

glfw.terminate()
