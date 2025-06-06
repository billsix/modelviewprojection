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


import sys
from dataclasses import astuple, dataclass

import glfw
from colorutils import Color3
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

window = glfw.create_window(500, 500, "ModelViewProjection Demo 4", None, None)
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


# doc-region-begin define vector class
@dataclass
class Vector:
    x: float
    y: float


# doc-region-end define vector class


# doc-region-begin define paddle class
@dataclass
class Paddle:
    vertices: list[Vector]
    color: Color3


# doc-region-end define paddle class

# doc-region-begin instantiate paddles
paddle1 = Paddle(
    vertices=[
        Vector(x=-1.0, y=-0.3),
        Vector(x=-0.8, y=-0.3),
        Vector(x=-0.8, y=0.3),
        Vector(x=-1.0, y=0.3),
    ],
    color=Color3(r=0.578123, g=0.0, b=1.0),
)

paddle2 = Paddle(
    vertices=[
        Vector(0.8, -0.3),
        Vector(1.0, -0.3),
        Vector(1.0, 0.3),
        Vector(0.8, 0.3),
    ],
    color=Color3(r=1.0, g=1.0, b=0.0),
)
# doc-region-end instantiate paddles


# doc-region-begin handle user input for paddle movement
def handle_movement_of_paddles() -> None:
    global paddle1, paddle2
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        for v in paddle1.vertices:
            v.x += 0.0
            v.y -= 0.1
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        for v in paddle1.vertices:
            v.x += 0.0
            v.y += 0.1
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        for v in paddle2.vertices:
            v.x += 0.0
            v.y -= 0.1
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        for v in paddle2.vertices:
            v.x += 0.0
            v.y += 0.1


# doc-region-end handle user input for paddle movement

# doc-region-begin limit framerate to 60 fps
TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()
# doc-region-end limit framerate to 60 fps

# doc-region-begin begin event loop
while not glfw.window_should_close(window):
    while (
        glfw.get_time()
        < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass

    time_at_beginning_of_previous_frame = glfw.get_time()
    # doc-region-end begin event loop

    # doc-region-begin poll events and get framebuffer size
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # doc-region-end poll events and get framebuffer size

    # doc-region-begin call draw in square viewport
    draw_in_square_viewport()
    # doc-region-end call draw in square viewport

    # doc-region-begin call handle movement of paddles
    handle_movement_of_paddles()
    # doc-region-end call handle movement of paddles

    # doc-region-begin draw paddle 1
    glColor3f(*astuple(paddle1.color))

    glBegin(GL_QUADS)
    for vector in paddle1.vertices:
        glVertex2f(vector.x, vector.y)
    glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin draw paddle 2
    glColor3f(*astuple(paddle2.color))

    glBegin(GL_QUADS)
    for vector in paddle2.vertices:
        glVertex2f(vector.x, vector.y)
    glEnd()
    # doc-region-end draw paddle 2

    # doc-region-begin flush framebuffer
    glfw.swap_buffers(window)
    # doc-region-end flush framebuffer

glfw.terminate()
