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

import sys
from dataclasses import astuple, dataclass

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

from colorutils import Color3
from mathutils import InvertibleFunction
from mathutils2d import (
    Vector2D,
    compose,
    rotate_around,
    translate,
    uniform_scale,
)

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 8", None, None)
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
class Paddle:
    vertices: list[Vector2D]
    color: Color3
    position: Vector2D
    rotation: float = 0.0


paddle1: Paddle = Paddle(
    vertices=[
        Vector2D(x=-1.0, y=-3.0),
        Vector2D(x=1.0, y=-3.0),
        Vector2D(x=1.0, y=3.0),
        Vector2D(x=-1.0, y=3.0),
    ],
    color=Color3(r=0.578123, g=0.0, b=1.0),
    position=Vector2D(-9.0, 0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vector2D(x=-1.0, y=-3.0),
        Vector2D(x=1.0, y=-3.0),
        Vector2D(x=1.0, y=3.0),
        Vector2D(x=-1.0, y=3.0),
    ],
    color=Color3(r=1.0, g=1.0, b=0.0),
    position=Vector2D(9.0, 0.0),
)


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

    # draw paddle 1
    # doc-region-begin draw paddle 1
    glColor3f(*astuple(paddle1.color))

    glBegin(GL_QUADS)
    rotatePoint: Vector2D = paddle1.position
    for p1_v_ms in paddle1.vertices:
        fn: InvertibleFunction[Vector2D] = compose(
            uniform_scale(1.0 / 10.0),
            rotate_around(paddle1.rotation, rotatePoint),
            translate(paddle1.position),
        )
        paddle1_vector_ndc: Vector2D = fn(p1_v_ms)
        glVertex2f(paddle1_vector_ndc.x, paddle1_vector_ndc.y)
        # doc-region-end draw paddle 1
    glEnd()

    # doc-region-begin draw paddle 2
    # draw paddle 2
    glColor3f(*astuple(paddle2.color))

    glBegin(GL_QUADS)
    rotatePoint: Vector2D = paddle2.position
    for p2_v_ms in paddle2.vertices:
        fn: InvertibleFunction[Vector2D] = compose(
            uniform_scale(1.0 / 10.0),
            rotate_around(paddle2.rotation, rotatePoint),
            translate(paddle2.position),
        )
        paddle2_vector_ndc: Vector2D = fn(p2_v_ms)
        glVertex2f(paddle2_vector_ndc.x, paddle2_vector_ndc.y)
    glEnd()
    # doc-region-end draw paddle 2

    glfw.swap_buffers(window)

glfw.terminate()
