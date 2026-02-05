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
from modelviewprojection.mathutils import (
    MultiVector,
    compose,
    e_1,
    e_2,
    e_3,
    fn_stack,
    inverse,
    zero,
)
from modelviewprojection.mathutils import rotate_z as RZ
from modelviewprojection.mathutils import translate as T
from modelviewprojection.mathutils import uniform_scale as S

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 16", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)

GL.glClearDepth(-1.0)
GL.glDepthFunc(GL.GL_GREATER)
GL.glEnable(GL.GL_DEPTH_TEST)


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
    vertices: list[MultiVector]
    color: colorutils.Color3
    position: MultiVector
    rotation: float = 0.0


# doc-region-begin instantiate paddle 1
paddle1: Paddle = Paddle(
    vertices=[
        -1.0 * e_1 + -3.0 * e_2,
        1.0 * e_1 + -3.0 * e_2,
        1.0 * e_1 + 3.0 * e_2,
        -1.0 * e_1 + 3.0 * e_2,
    ],
    color=colorutils.Color3(r=0.578123, g=0.0, b=1.0),
    position=(-9.0 * e_1),
)

paddle2: Paddle = Paddle(
    vertices=[
        -1.0 * e_1 + -3.0 * e_2,
        1.0 * e_1 + -3.0 * e_2,
        1.0 * e_1 + 3.0 * e_2,
        -1.0 * e_1 + 3.0 * e_2,
    ],
    color=colorutils.Color3(r=1.0, g=1.0, b=0.0),
    position=(9.0 * e_1),
)
# doc-region-end instantiate paddle 1


# doc-region-begin define camera class
@dataclasses.dataclass
class Camera:
    position_ws: MultiVector = dataclasses.field(default_factory=lambda: zero)


camera: Camera = Camera()
# doc-region-end define camera class

# doc-region-begin instantiate square
square: list[MultiVector] = [
    -0.5 * e_1 + -0.5 * e_2,
    0.5 * e_1 + -0.5 * e_2,
    0.5 * e_1 + 0.5 * e_2,
    -0.5 * e_1 + 0.5 * e_2,
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
        camera.position_ws += 1.0 * e_2
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_ws -= 1.0 * e_2
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.position_ws -= 1.0 * e_1
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.position_ws += 1.0 * e_1

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position -= 1.0 * e_2
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position += 1.0 * e_2
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position -= 1.0 * e_2
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position += 1.0 * e_2

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

    draw_in_square_viewport()
    handle_inputs()

    # doc-region-begin stack push camera space to ndc
    # camera space to NDC
    fn_stack.push(S(1.0 / 10.0))
    # doc-region-end stack push camera space to ndc

    # doc-region-begin world space to camera space
    # world space to camera space
    fn_stack.push(inverse(T(camera.position_ws)))
    # doc-region-end world space to camera space

    # doc-region-begin paddle 1 transformations
    # paddle 1 model space to world space
    fn_stack.push(compose([T(paddle1.position), RZ(paddle1.rotation)]))
    # doc-region-end paddle 1 transformations

    # doc-region-begin draw paddle 1
    GL.glColor3f(*iter(paddle1.color))
    GL.glBegin(GL.GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        paddle1_vector_ndc: MultiVector = fn_stack.modelspace_to_ndc_fn()(
            p1_v_ms
        )
        GL.glVertex3f(
            paddle1_vector_ndc.component(e_1),
            paddle1_vector_ndc.component(e_2),
            paddle1_vector_ndc.component(e_3),
        )
    GL.glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin square space to paddle 1 space
    fn_stack.push(
        compose(
            [
                T(-1.0 * e_3),
                RZ(rotation_around_paddle1),
                T(2.0 * e_1),
                RZ(square_rotation),
            ]
        )
    )
    # doc-region-end square space to paddle 1 space
    # doc-region-begin draw square
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glBegin(GL.GL_QUADS)
    for ms in square:
        square_vector_ndc: MultiVector = fn_stack.modelspace_to_ndc_fn()(ms)
        GL.glVertex3f(
            square_vector_ndc.component(e_1),
            square_vector_ndc.component(e_2),
            square_vector_ndc.component(e_3),
        )
    GL.glEnd()
    # doc-region-end draw square

    # doc-region-begin back to world space
    fn_stack.pop()  # pop off square space to paddle 1 space
    # current space is paddle 1 space
    fn_stack.pop()  # # pop off paddle 1 model space to world space
    # current space is world space
    # doc-region-end back to world space

    # doc-region-begin paddle 2 model space to world space
    fn_stack.push(compose([T(paddle2.position), RZ(paddle2.rotation)]))
    # doc-region-end paddle 2 model space to world space

    # doc-region-begin draw paddle 2
    # draw paddle 2
    GL.glColor3f(*iter(paddle2.color))
    GL.glBegin(GL.GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        paddle2_vector_ndc: MultiVector = fn_stack.modelspace_to_ndc_fn()(
            p2_v_ms
        )
        GL.glVertex3f(
            paddle2_vector_ndc.component(e_1),
            paddle2_vector_ndc.component(e_2),
            paddle2_vector_ndc.component(e_3),
        )
    GL.glEnd()
    # doc-region-end draw paddle 2

    # doc-region-begin clear function stack for next iteration of the event loop
    # done rendering everything for this frame, just go ahead and clear all functions
    # off of the stack, back to NDC as current space
    fn_stack.clear()

    # doc-region-end clear function stack for next iteration of the event loop

    # doc-region-begin flush framebuffer
    glfw.swap_buffers(window)
    # doc-region-end flush framebuffer

glfw.terminate()
