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
from gacalc.g3 import Vector3
from gacalc.transforms import compose, inverse, translate, uniform_scale

import modelviewprojection.util.colorutils as colorutils
from modelviewprojection.mathutils import fn_stack, rotate_z
from modelviewprojection.util.clipping import draw_in_square_viewport
from modelviewprojection.util.windowing import on_key

zero = Vector3.zero()


if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 16", None, None)
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
    vertices: list[Vector3]
    color: colorutils.Color3
    position: Vector3
    rotation: float = 0.0


# doc-region-begin instantiate paddle 1
paddle1: Paddle = Paddle(
    vertices=[
        -1 * Vector3.e_1 + -3 * Vector3.e_2,
        Vector3.e_1 + -3 * Vector3.e_2,
        Vector3.e_1 + 3 * Vector3.e_2,
        -1 * Vector3.e_1 + 3 * Vector3.e_2,
    ],
    color=colorutils.Color3(r=0.578123, g=0.0, b=1.0),
    position=-9 * Vector3.e_1,
)

paddle2: Paddle = Paddle(
    vertices=[
        -1 * Vector3.e_1 + -3 * Vector3.e_2,
        Vector3.e_1 + -3 * Vector3.e_2,
        Vector3.e_1 + 3 * Vector3.e_2,
        -1 * Vector3.e_1 + 3 * Vector3.e_2,
    ],
    color=colorutils.Color3(r=1.0, g=1.0, b=0.0),
    position=9 * Vector3.e_1,
)
# doc-region-end instantiate paddle 1


# doc-region-begin define camera class
@dataclasses.dataclass
class Camera:
    position_ws: Vector3 = dataclasses.field(default_factory=lambda: zero)


camera: Camera = Camera()
# doc-region-end define camera class

# doc-region-begin instantiate square
square: list[Vector3] = [
    -0.5 * Vector3.e_1 + -0.5 * Vector3.e_2,
    0.5 * Vector3.e_1 + -0.5 * Vector3.e_2,
    0.5 * Vector3.e_1 + 0.5 * Vector3.e_2,
    -0.5 * Vector3.e_1 + 0.5 * Vector3.e_2,
]
# doc-region-end instantiate square

square_rotation: float = 0.0
rotation_around_paddle1: float = 0.0


def handle_inputs() -> None:
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera

    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.position_ws += Vector3.e_2
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_ws -= Vector3.e_2
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.position_ws -= Vector3.e_1
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.position_ws += Vector3.e_1

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position -= Vector3.e_2
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position += Vector3.e_2
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position -= Vector3.e_2
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position += Vector3.e_2

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

    # doc-region-begin stack push camera space to ndc
    # camera space to NDC
    fn_stack.push(uniform_scale(m=1.0 / 10.0))
    # doc-region-end stack push camera space to ndc

    # doc-region-begin world space to camera space
    # world space to camera space
    fn_stack.push(inverse(translate(b=camera.position_ws)))
    # doc-region-end world space to camera space

    # doc-region-begin paddle 1 transformations
    # paddle 1 model space to world space
    fn_stack.push(
        compose([translate(b=paddle1.position), rotate_z(paddle1.rotation)])
    )
    # doc-region-end paddle 1 transformations

    # doc-region-begin draw paddle 1
    GL.glColor3f(*paddle1.color)
    GL.glBegin(GL.GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        paddle1_vector_ndc = fn_stack.modelspace_to_ndc_fn()(p1_v_ms)
        GL.glVertex3f(*paddle1_vector_ndc)
    GL.glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin square space to paddle 1 space
    fn_stack.push(
        compose(
            [
                translate(b=-1 * Vector3.e_3),
                rotate_z(rotation_around_paddle1),
                translate(b=2 * Vector3.e_1),
                rotate_z(square_rotation),
            ]
        )
    )
    # doc-region-end square space to paddle 1 space
    # doc-region-begin draw square
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glBegin(GL.GL_QUADS)
    for ms in square:
        square_vector_ndc = fn_stack.modelspace_to_ndc_fn()(ms)
        GL.glVertex3f(*square_vector_ndc)
    GL.glEnd()
    # doc-region-end draw square

    # doc-region-begin back to world space
    fn_stack.pop()  # pop off square space to paddle 1 space
    # current space is paddle 1 space
    fn_stack.pop()  # # pop off paddle 1 model space to world space
    # current space is world space
    # doc-region-end back to world space

    # doc-region-begin paddle 2 model space to world space
    fn_stack.push(
        compose([translate(b=paddle2.position), rotate_z(paddle2.rotation)])
    )
    # doc-region-end paddle 2 model space to world space

    # doc-region-begin draw paddle 2
    # draw paddle 2
    GL.glColor3f(*paddle2.color)
    GL.glBegin(GL.GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        paddle2_vector_ndc = fn_stack.modelspace_to_ndc_fn()(p2_v_ms)
        GL.glVertex3f(*paddle2_vector_ndc)
    GL.glEnd()
    # doc-region-end draw paddle 2

    # doc-region-begin clear function stack for next iteration of the event loop
    # done rendering everything for this frame, just go ahead and clear all
    # functions
    # off of the stack, back to NDC as current space
    fn_stack.clear()

    # doc-region-end clear function stack for next iteration of the event loop

    # doc-region-begin flush framebuffer
    glfw.swap_buffers(window)
    # doc-region-end flush framebuffer

glfw.terminate()
