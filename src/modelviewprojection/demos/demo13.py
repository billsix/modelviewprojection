# Copyright (c) 2018-2026 William Emerison Six
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

import modelviewprojection.util.colorutils as colorutils
from modelviewprojection.mathutils import (
    InvertibleFunction,
    Vector2,
    compose,
    inverse,
    rotate,
    translate,
    uniform_scale,
)
from modelviewprojection.util.clipping import draw_in_square_viewport
from modelviewprojection.util.windowing import on_key

zero = Vector2.zero()


if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 13", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)


GL.glMatrixMode(GL.GL_PROJECTION)
GL.glLoadIdentity()
GL.glMatrixMode(GL.GL_MODELVIEW)
GL.glLoadIdentity()


@dataclasses.dataclass
class Paddle:
    vertices: list[Vector2]
    color: colorutils.Color3
    position: Vector2
    rotation: float = 0.0


paddle1: Paddle = Paddle(
    vertices=[
        -1 * Vector2.e_1 + -3 * Vector2.e_2,
        Vector2.e_1 + -3 * Vector2.e_2,
        Vector2.e_1 + 3 * Vector2.e_2,
        -1 * Vector2.e_1 + 3 * Vector2.e_2,
    ],
    color=colorutils.Color3(r=0.578123, g=0.0, b=1.0),
    position=-9 * Vector2.e_1,
)

paddle2: Paddle = Paddle(
    vertices=[
        -1 * Vector2.e_1 + -3 * Vector2.e_2,
        Vector2.e_1 + -3 * Vector2.e_2,
        Vector2.e_1 + 3 * Vector2.e_2,
        -1 * Vector2.e_1 + 3 * Vector2.e_2,
    ],
    color=colorutils.Color3(r=1.0, g=1.0, b=0.0),
    position=9 * Vector2.e_1,
)


@dataclasses.dataclass
class Camera:
    position_ws: Vector2 = dataclasses.field(default_factory=lambda: zero)


camera: Camera = Camera()


square: list[Vector2] = [
    -0.5 * Vector2.e_1 + -0.5 * Vector2.e_2,
    0.5 * Vector2.e_1 + -0.5 * Vector2.e_2,
    0.5 * Vector2.e_1 + 0.5 * Vector2.e_2,
    -0.5 * Vector2.e_1 + 0.5 * Vector2.e_2,
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
        camera.position_ws += Vector2.e_2
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_ws -= Vector2.e_2
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.position_ws -= Vector2.e_1
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.position_ws += Vector2.e_1

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position -= Vector2.e_2
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position += Vector2.e_2
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position -= Vector2.e_2
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position += Vector2.e_2

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
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    draw_in_square_viewport(window)
    handle_inputs()

    GL.glColor3f(*iter(paddle1.color))

    GL.glBegin(GL.GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        ms_to_ndc: InvertibleFunction[Vector2] = compose(
            [
                # camera space to NDC
                uniform_scale(1.0 / 10.0),
                # world space to camera space
                inverse(translate(camera.position_ws)),
                # model space to world space
                compose(
                    [
                        translate(paddle1.position),
                        rotate(paddle1.rotation),
                    ]
                ),
            ]
        )

        paddle1_vector_ndc: Vector2 = ms_to_ndc(p1_v_ms)

        GL.glVertex2f(paddle1_vector_ndc.coeff_e_1, paddle1_vector_ndc.coeff_e_2)
    GL.glEnd()

    # doc-region-begin draw square
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glBegin(GL.GL_QUADS)
    for ms in square:
        ms_to_ndc: InvertibleFunction[Vector2] = compose(
            [
                # camera space to NDC
                uniform_scale(1.0 / 10.0),
                # world space to camera space
                inverse(translate(camera.position_ws)),
                # model space to world space
                compose(
                    [
                        translate(paddle1.position),
                        rotate(paddle1.rotation),
                    ]
                ),
                # square space to paddle 1 space
                compose(
                    [
                        rotate(rotation_around_paddle1),
                        translate(2 * Vector2.e_1),
                        rotate(square_rotation),
                    ]
                ),
            ]
        )
        square_vector_ndc: Vector2 = ms_to_ndc(ms)
        GL.glVertex2f(square_vector_ndc.coeff_e_1, square_vector_ndc.coeff_e_2)
    GL.glEnd()
    # doc-region-end draw square

    GL.glColor3f(*iter(paddle2.color))

    GL.glBegin(GL.GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        ms_to_ndc: InvertibleFunction[Vector2] = compose(
            [
                # camera space to NDC
                uniform_scale(1.0 / 10.0),
                # world space to camera space
                inverse(translate(camera.position_ws)),
                # model space to world space
                compose(
                    [
                        translate(paddle2.position),
                        rotate(paddle2.rotation),
                    ]
                ),
            ]
        )

        paddle2_vector_ndc: Vector2 = ms_to_ndc(p2_v_ms)

        GL.glVertex2f(paddle2_vector_ndc.coeff_e_1, paddle2_vector_ndc.coeff_e_2)
    GL.glEnd()

    glfw.swap_buffers(window)
glfw.terminate()
