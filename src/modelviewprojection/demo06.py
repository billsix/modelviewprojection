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


import dataclasses
import sys

import glfw
import OpenGL.GL as GL

import modelviewprojection.colorutils as colorutils
import modelviewprojection.mathutils as mu2d
from modelviewprojection.mathutils import translate as T
from modelviewprojection.mathutils import uniform_scale as S

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 6", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)

GL.glMatrixMode(GL.GL_PROJECTION)
GL.glLoadIdentity()
GL.glMatrixMode(GL.GL_MODELVIEW)
GL.glLoadIdentity()


def draw_in_square_viewport() -> None:
    GL.glClearColor(0.2, 0.2, 0.2, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    w, h = glfw.get_framebuffer_size(window)
    minimal_dimension = w if w < h else h

    GL.glEnable(GL.GL_SCISSOR_TEST)
    GL.glScissor(
        int((w - minimal_dimension) / 2.0),
        int((h - minimal_dimension) / 2.0),
        minimal_dimension,
        minimal_dimension,
    )

    GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glDisable(GL.GL_SCISSOR_TEST)

    GL.glViewport(
        int(0.0 + (w - minimal_dimension) / 2.0),
        int(0.0 + (h - minimal_dimension) / 2.0),
        minimal_dimension,
        minimal_dimension,
    )


@dataclasses.dataclass
class Paddle:
    vertices: list[mu2d.Vector2D]
    color: colorutils.Color3
    position: mu2d.Vector2D


# doc-region-begin instantiate paddles
paddle1: Paddle = Paddle(
    vertices=[
        mu2d.Vector2D(x=-1.0, y=-3.0),
        mu2d.Vector2D(x=1.0, y=-3.0),
        mu2d.Vector2D(x=1.0, y=3.0),
        mu2d.Vector2D(x=-1.0, y=3.0),
    ],
    color=colorutils.Color3(r=0.578123, g=0.0, b=1.0),
    position=mu2d.Vector2D(-9.0, 0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        mu2d.Vector2D(x=-1.0, y=-3.0),
        mu2d.Vector2D(x=1.0, y=-3.0),
        mu2d.Vector2D(x=1.0, y=3.0),
        mu2d.Vector2D(x=-1.0, y=3.0),
    ],
    color=colorutils.Color3(r=1.0, g=1.0, b=0.0),
    position=mu2d.Vector2D(9.0, 0.0),
)
# doc-region-end instantiate paddles


# doc-region-begin define handle movement of paddles
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
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    draw_in_square_viewport()
    handle_movement_of_paddles()
    # doc-region-end begin event loop

    # doc-region-begin draw paddle 1
    GL.glColor3f(*iter(paddle1.color))

    world_space_to_ndc: mu2d.InvertibleFunction = S(1.0 / 10.0)
    p1_space_to_world_space: mu2d.InvertibleFunction = T(paddle1.position)
    p1_to_ndc: mu2d.InvertibleFunction = (
        world_space_to_ndc @ p1_space_to_world_space
    )
    GL.glBegin(GL.GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        paddle1_vector_ndc: mu2d.Vector = p1_to_ndc(p1_v_ms)
        GL.glVertex2f(paddle1_vector_ndc.x, paddle1_vector_ndc.y)

    GL.glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin draw paddle 2
    GL.glColor3f(*iter(paddle2.color))

    world_space_to_ndc: mu2d.InvertibleFunction = S(1.0 / 10.0)
    p2_space_to_world_space: mu2d.InvertibleFunction = T(paddle2.position)
    p2_to_ndc: mu2d.InvertibleFunction = (
        world_space_to_ndc @ p2_space_to_world_space
    )
    GL.glBegin(GL.GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        paddle2_vector_ndc: mu2d.Vector = p2_to_ndc(p2_v_ms)
        GL.glVertex2f(paddle2_vector_ndc.x, paddle2_vector_ndc.y)
    GL.glEnd()
    # doc-region-end draw paddle 2

    # aoeu
    # doc-region-begin flush framebuffer
    glfw.swap_buffers(window)
    # doc-region-end flush framebuffer
glfw.terminate()
