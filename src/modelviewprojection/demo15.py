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
import modelviewprojection.mathutils as mu
import modelviewprojection.mathutils3d as mu3d

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 15", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)

# doc-region-begin enable depth buffer
GL.glClearDepth(-1.0)
GL.glDepthFunc(GL.GL_GREATER)
GL.glEnable(GL.GL_DEPTH_TEST)
# doc-region-end enable depth buffer


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
    vertices: list[mu3d.Vector3D]
    color: colorutils.Color3
    position: mu3d.Vector3D
    rotation: float = 0.0


# doc-region-begin instantiate paddle 1
paddle1: Paddle = Paddle(
    vertices=[
        mu3d.Vector3D(x=-1.0, y=-3.0, z=0.0),
        mu3d.Vector3D(x=1.0, y=-3.0, z=0.0),
        mu3d.Vector3D(x=1.0, y=3.0, z=0.0),
        mu3d.Vector3D(x=-1.0, y=3.0, z=0.0),
    ],
    color=colorutils.Color3(r=0.578123, g=0.0, b=1.0),
    position=mu3d.Vector3D(x=-9.0, y=0.0, z=0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        mu3d.Vector3D(x=-1.0, y=-3.0, z=0.0),
        mu3d.Vector3D(x=1.0, y=-3.0, z=0.0),
        mu3d.Vector3D(x=1.0, y=3.0, z=0.0),
        mu3d.Vector3D(x=-1.0, y=3.0, z=0.0),
    ],
    color=colorutils.Color3(r=1.0, g=1.0, b=0.0),
    position=mu3d.Vector3D(x=9.0, y=0.0, z=0.0),
)
# doc-region-end instantiate paddle 1


# doc-region-begin define camera class
@dataclasses.dataclass
class Camera:
    position_ws: mu3d.Vector3D = dataclasses.field(
        default_factory=lambda: mu3d.Vector3D(x=0.0, y=0.0, z=0.0)
    )


camera: Camera = Camera()
# doc-region-end define camera class

# doc-region-begin instantiate square
square: list[mu3d.Vector3D] = [
    mu3d.Vector3D(x=-0.5, y=-0.5, z=0.0),
    mu3d.Vector3D(x=0.5, y=-0.5, z=0.0),
    mu3d.Vector3D(x=0.5, y=0.5, z=0.0),
    mu3d.Vector3D(x=-0.5, y=0.5, z=0.0),
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
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    draw_in_square_viewport()
    handle_inputs()

    # doc-region-begin draw paddle 1
    GL.glColor3f(*iter(paddle1.color))
    GL.glBegin(GL.GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        ms_to_ndc: mu.InvertibleFunction[mu3d.Vector3D] = mu.compose(
            [
                # camera space to NDC
                mu.uniform_scale(1.0 / 10.0),
                # world space to camera space
                mu.inverse(mu.translate(camera.position_ws)),
                # model space to world space
                mu.compose(
                    [
                        mu.translate(paddle1.position),
                        mu3d.rotate_z(paddle1.rotation),
                    ]
                ),
            ]
        )

        paddle1_vector_ndc: mu3d.Vector3D = ms_to_ndc(p1_v_ms)
        GL.glVertex3f(
            paddle1_vector_ndc.x, paddle1_vector_ndc.y, paddle1_vector_ndc.z
        )
    GL.glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin draw square
    # draw square
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glBegin(GL.GL_QUADS)
    for ms in square:
        ms_to_ndc: mu.InvertibleFunction[mu3d.Vector3D] = mu.compose(
            [
                # camera space to NDC
                mu.uniform_scale(1.0 / 10.0),
                # world space to camera space
                mu.inverse(mu.translate(camera.position_ws)),
                # model space to world space
                mu.compose(
                    [
                        mu.translate(paddle1.position),
                        mu3d.rotate_z(paddle1.rotation),
                    ]
                ),
                # square space to paddle 1 space
                mu.compose(
                    [
                        mu.translate(mu3d.Vector3D(x=0.0, y=0.0, z=-1.0)),
                        mu3d.rotate_z(rotation_around_paddle1),
                        mu.translate(mu3d.Vector3D(x=2.0, y=0.0, z=0.0)),
                        mu3d.rotate_z(square_rotation),
                    ]
                ),
            ]
        )
        square_vector_ndc: mu3d.Vector3D = ms_to_ndc(ms)
        GL.glVertex3f(
            square_vector_ndc.x, square_vector_ndc.y, square_vector_ndc.z
        )
    GL.glEnd()
    # doc-region-end draw square

    # doc-region-begin draw paddle 2
    # draw paddle 2
    GL.glColor3f(*iter(paddle2.color))
    GL.glBegin(GL.GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        ms_to_ndc: mu.InvertibleFunction[mu3d.Vector3D] = mu.compose(
            [
                # camera space to NDC
                mu.uniform_scale(1.0 / 10.0),
                # world space to camera space
                mu.inverse(mu.translate(camera.position_ws)),
                # model space to world space
                mu.compose(
                    [
                        mu.translate(paddle2.position),
                        mu3d.rotate_z(paddle2.rotation),
                    ]
                ),
            ]
        )

        paddle2_vector_ndc: mu3d.Vector3D = ms_to_ndc(p2_v_ms)
        GL.glVertex3f(
            paddle2_vector_ndc.x, paddle2_vector_ndc.y, paddle2_vector_ndc.z
        )
    GL.glEnd()
    # doc-region-end draw paddle 2

    glfw.swap_buffers(window)

glfw.terminate()
