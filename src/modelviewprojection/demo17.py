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

import modelviewprojection.colorutils as colorutils
from modelviewprojection.mathutils import (
    Vector3D,
    compose,
    fn_stack,
    inverse,
    ortho,
    push_transformation,
    rotate_x,
    rotate_y,
    rotate_z,
    translate,
)

e_1 = Vector3D.e_1()
e_2 = Vector3D.e_2()
e_3 = Vector3D.e_3()


if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 17", None, None)
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
    vertices: list[Vector3D]
    color: colorutils.Color3
    position: Vector3D
    rotation: float = 0.0


paddle1: Paddle = Paddle(
    vertices=[
        -1.0 * e_1 + -3.0 * e_2 + 0.0 * e_3,
        1.0 * e_1 + -3.0 * e_2 + 0.0 * e_3,
        1.0 * e_1 + 3.0 * e_2 + 0.0 * e_3,
        -1.0 * e_1 + 3.0 * e_2 + 0.0 * e_3,
    ],
    color=colorutils.Color3(r=0.578123, g=0.0, b=1.0),
    position=-9.0 * e_1 + 0.0 * e_2 + 0.0 * e_3,
)

paddle2: Paddle = Paddle(
    vertices=[
        -1.0 * e_1 + -3.0 * e_2 + 0.0 * e_3,
        1.0 * e_1 + -3.0 * e_2 + 0.0 * e_3,
        1.0 * e_1 + 3.0 * e_2 + 0.0 * e_3,
        -1.0 * e_1 + 3.0 * e_2 + 0.0 * e_3,
    ],
    color=colorutils.Color3(r=1.0, g=1.0, b=0.0),
    position=9.0 * e_1 + 0.0 * e_2 + 0.0 * e_3,
)


# doc-region-begin define camera class


@dataclasses.dataclass
class Camera:
    position_ws: Vector3D = dataclasses.field(
        default_factory=lambda: 0.0 * e_1 + 0.0 * e_2 + 15.0 * e_3
    )
    rot_y: float = 0.0
    rot_x: float = 0.0
    # doc-region-end define camera class


camera: Camera = Camera()


square: list[Vector3D] = [
    -0.5 * e_1 + -0.5 * e_2 + 0.0 * e_3,
    0.5 * e_1 + -0.5 * e_2 + 0.0 * e_3,
    0.5 * e_1 + 0.5 * e_2 + 0.0 * e_3,
    -0.5 * e_1 + 0.5 * e_2 + 0.0 * e_3,
]
square_rotation: float = 0.0
rotation_around_paddle1: float = 0.0


# doc-region-begin define handle inputs
def handle_inputs() -> None:
    # doc-region-end define handle inputs
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera

    # doc-region-begin handle key inputs
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera.rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera.rot_x -= 0.03
    # doc-region-end handle key inputs

    # doc-region-begin handle key input keys
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        forwards_cs = 0.0 * e_1 + 0.0 * e_2 + -1.0 * e_3
        forward_ws = compose(
            [translate(camera.position_ws), rotate_y(camera.rot_y)]
        )(forwards_cs)
        camera.position_ws = forward_ws
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        forwards_cs = 0.0 * e_1 + 0.0 * e_2 + 1.0 * e_3
        forward_ws = compose(
            [translate(camera.position_ws), rotate_y(camera.rot_y)]
        )(forwards_cs)
        camera.position_ws = forward_ws
    # doc-region-end handle key input keys

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

    # doc-region-begin draw scene
    # cameraspace to NDC
    with push_transformation(
        ortho(
            left=-10.0, right=10.0, bottom=-10.0, top=10.0, near=-0.1, far=-30.0
        )
    ):
        # world space to camera space, which is inverse of camera space
        # to world space
        with push_transformation(
            inverse(
                compose(
                    [
                        translate(camera.position_ws),
                        rotate_y(camera.rot_y),
                        rotate_x(camera.rot_x),
                    ]
                )
            )
        ):
            # paddle 1 space to world space
            with push_transformation(
                compose(
                    [
                        translate(paddle1.position),
                        rotate_z(paddle1.rotation),
                    ]
                )
            ):
                GL.glColor3f(*iter(paddle1.color))
                GL.glBegin(GL.GL_QUADS)
                for p1_v_ms in paddle1.vertices:
                    paddle1_vector_ndc = fn_stack.modelspace_to_ndc_fn()(
                        p1_v_ms
                    )
                    GL.glVertex3f(
                        paddle1_vector_ndc.x,
                        paddle1_vector_ndc.y,
                        paddle1_vector_ndc.z,
                    )
                GL.glEnd()

                # square space to paddle 1 space
                with push_transformation(
                    compose(
                        [
                            translate(0.0 * e_1 + 0.0 * e_2 + -1.0 * e_3),
                            rotate_z(rotation_around_paddle1),
                            translate(2.0 * e_1 + 0.0 * e_2 + 0.0 * e_3),
                            rotate_z(square_rotation),
                        ]
                    )
                ):
                    # draw square
                    GL.glColor3f(0.0, 0.0, 1.0)
                    GL.glBegin(GL.GL_QUADS)
                    for ms in square:
                        square_vector_ndc = fn_stack.modelspace_to_ndc_fn()(ms)
                        GL.glVertex3f(
                            square_vector_ndc.x,
                            square_vector_ndc.y,
                            square_vector_ndc.z,
                        )
                    GL.glEnd()

            # paddle 2 space to world space
            with push_transformation(
                compose(
                    [
                        translate(paddle2.position),
                        rotate_z(paddle2.rotation),
                    ]
                )
            ):
                # draw paddle 2
                GL.glColor3f(*iter(paddle2.color))
                GL.glBegin(GL.GL_QUADS)
                for p2_v_ms in paddle2.vertices:
                    paddle2_vector_ndc = fn_stack.modelspace_to_ndc_fn()(
                        p2_v_ms
                    )
                    GL.glVertex3f(
                        paddle2_vector_ndc.x,
                        paddle2_vector_ndc.y,
                        paddle2_vector_ndc.z,
                    )
                GL.glEnd()

    glfw.swap_buffers(window)
    # doc-region-end draw scene

glfw.terminate()
