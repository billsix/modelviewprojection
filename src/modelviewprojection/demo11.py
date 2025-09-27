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
import dataclasses

import glfw
import colorutils
import OpenGL.GL as GL


import modelviewprojection.mathutils as mu
import modelviewprojection.mathutils2d as mu2d

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 11", None, None)
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
    rotation: float = 0.0


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


@dataclasses.dataclass
class Camera:
    position_ws: mu2d.Vector2D = dataclasses.field(
        default_factory=lambda: mu2d.Vector2D(x=0.0, y=0.0)
    )


camera: Camera = Camera()


# doc-region-begin define square
square: list[mu2d.Vector2D] = [
    mu2d.Vector2D(x=-0.5, y=-0.5),
    mu2d.Vector2D(x=0.5, y=-0.5),
    mu2d.Vector2D(x=0.5, y=0.5),
    mu2d.Vector2D(x=-0.5, y=0.5),
]
# doc-region-end define square


def handle_inputs() -> None:
    global camera

    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.position_ws.y += 1.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_ws.y -= 1.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.position_ws.x -= 1.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.position_ws.x += 1.0

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
    GL.glViewport(0, 0, width, height)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    draw_in_square_viewport()
    handle_inputs()

    # doc-region-begin draw paddle 1
    GL.glColor3f(*dataclasses.astuple(paddle1.color))

    GL.glBegin(GL.GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        ms_to_ndc: mu.InvertibleFunction[mu2d.Vector2D] = mu.compose(
            # camera space to NDC
            mu.uniform_scale(1.0 / 10.0),
            # world space to camera space
            mu.inverse(mu.translate(camera.position_ws)),
            # model space to world space
            mu.compose(
                mu.translate(paddle1.position),
                mu2d.rotate(paddle1.rotation),
            ),
        )

        paddle1_vector_ndc: mu2d.Vector2D = ms_to_ndc(p1_v_ms)

        GL.glVertex2f(paddle1_vector_ndc.x, paddle1_vector_ndc.y)
    GL.glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin draw square
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glBegin(GL.GL_QUADS)
    for ms in square:
        ms_to_ndc: mu.InvertibleFunction[mu2d.Vector2D] = mu.compose(
            # camera space to NDC
            mu.uniform_scale(1.0 / 10.0),
            # world space to camera space
            mu.inverse(mu.translate(camera.position_ws)),
            # model space to world space
            mu.compose(
                mu.translate(paddle1.position),
                mu2d.rotate(paddle1.rotation),
            ),
            # square space to paddle 1 space
            mu.translate(mu2d.Vector2D(x=2.0, y=0.0)),
        )
        square_vector_ndc: mu2d.Vector2D = ms_to_ndc(ms)
        GL.glVertex2f(square_vector_ndc.x, square_vector_ndc.y)
    GL.glEnd()
    # doc-region-end draw square

    # doc-region-begin draw paddle 2
    GL.glColor3f(*dataclasses.astuple(paddle2.color))

    GL.glBegin(GL.GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        ms_to_ndc: mu.InvertibleFunction[mu2d.Vector2D] = mu.compose(
            # camera space to NDC
            mu.uniform_scale(1.0 / 10.0),
            # world space to camera space
            mu.inverse(mu.translate(camera.position_ws)),
            # model space to world space
            mu.compose(
                mu.translate(paddle2.position),
                mu2d.rotate(paddle2.rotation),
            ),
        )

        paddle2_vector_ndc: mu2d.Vector2D = ms_to_ndc(p2_v_ms)

        GL.glVertex2f(paddle2_vector_ndc.x, paddle2_vector_ndc.y)
    GL.glEnd()
    # doc-region-end draw paddle 2
    glfw.swap_buffers(window)
glfw.terminate()
