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


import math
import os
import sys
import dataclasses
import glfw
import numpy as np
import OpenGL.GL.shaders as shaders
import modelviewprojection.colorutils as colorutils
from modelviewprojection.glhelper import clear_mask

# doc-region-begin new imports
import OpenGL.GL as GL
import OpenGL.GLU as GLU

# doc-region-end new imports


if not glfw.init():
    sys.exit()

# doc-region-begin open gl version 2.1
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
# doc-region-end open gl version 2.1

window = glfw.create_window(500, 500, "ModelViewProjection Demo 20", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)

GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)


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
    position: any
    color: colorutils.Color3
    rotation: float = 0.0
    vertices: np.array = dataclasses.field(
        default_factory=lambda: np.array(
            [
                [-1.0, -3.0, 0.0],
                [1.0, -3.0, 0.0],
                [1.0, 3.0, 0.0],
                [-1.0, 3.0, 0.0],
            ],
            dtype=np.float32,
        )
    )


paddle1: Paddle = Paddle(
    color=colorutils.Color3(r=0.578123, g=0.0, b=1.0),
    position=np.array([-9.0, 0.0, 0.0]),
)

paddle2: Paddle = Paddle(
    color=colorutils.Color3(r=1.0, g=1.0, b=0.0),
    position=np.array([9.0, 0.0, 0.0]),
)


number_of_controllers = glfw.joystick_present(glfw.JOYSTICK_1)


@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera: Camera = Camera(x=0.0, y=0.0, z=40.0, rot_y=0.0, rot_x=0.0)


square_rotation: float = 0.0
rotation_around_paddle1: float = 0.0


def handle_inputs():
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera

    move_multiple = 1.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera.rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera.rot_x -= 0.03
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.x -= move_multiple * math.sin(camera.rot_y)
        camera.z -= move_multiple * math.cos(camera.rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.x += move_multiple * math.sin(camera.rot_y)
        camera.z += move_multiple * math.cos(camera.rot_y)

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position[1] += 1.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position[1] += 1.0

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1


square_vertices: np.array = np.array(
    [[-0.5, -0.5, 0.0], [0.5, -0.5, 0.0], [0.5, 0.5, 0.0], [-0.5, 0.5, 0.0]],
    dtype=np.float32,
)


TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()


# doc-region-begin compile shaders
# compile shaders

# initialize shaders
pwd = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(pwd, "triangle.vert"), "r") as f:
    vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)

with open(os.path.join(pwd, "triangle.frag"), "r") as f:
    fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)

shader = shaders.compileProgram(vs, fs)
GL.glUseProgram(shader)
# doc-region-end compile shaders

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
    GL.glClear(clear_mask(GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT))

    draw_in_square_viewport()
    handle_inputs()

    axes_list = glfw.get_joystick_axes(glfw.JOYSTICK_1)
    if len(axes_list) >= 1 and axes_list[0]:
        if math.fabs(float(axes_list[0][0])) > 0.1:
            camera.x += 1.0 * axes_list[0][0] * math.cos(camera.rot_y)
            camera.z -= 1.0 * axes_list[0][0] * math.sin(camera.rot_y)
        if math.fabs(float(axes_list[0][1])) > 0.1:
            camera.x += 1.0 * axes_list[0][1] * math.sin(camera.rot_y)
            camera.z += 1.0 * axes_list[0][1] * math.cos(camera.rot_y)

        # print(axes_list[0][4])
        if math.fabs(axes_list[0][3]) > 0.10:
            camera.rot_x -= 3.0 * axes_list[0][3] * 0.01
        if math.fabs(axes_list[0][2]) > 0.10:
            camera.rot_y -= axes_list[0][2] * 0.01

    # just like putting the identity function on the lambda stack
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

    # projection
    GL.glMatrixMode(GL.GL_PROJECTION)
    GLU.gluPerspective(
        45.0,  # field_of_view
        1.0,  # aspect_ration
        0.1,  # near_z
        1000.0,  # far_z
    )

    # view
    GL.glMatrixMode(GL.GL_MODELVIEW)

    GL.glRotatef(math.degrees(-camera.rot_x), 1.0, 0.0, 0.0)
    GL.glRotatef(math.degrees(-camera.rot_y), 0.0, 1.0, 0.0)
    GL.glTranslate(-camera.x, -camera.y, -camera.z)

    # model

    # paddle  1 and square
    # because 2 nodes are drawn off of world space
    # we need to save onto the current "function",
    # aka matrix, for the subsequent geometry
    # the width statement ensures that the matrix is
    # pushed onto a stack, and when the with block doc-region-ends,
    # it will be automatically popped off of the stack
    GL.glPushMatrix()

    GL.glColor3f(*iter(paddle1.color))

    GL.glTranslate(
        paddle1.position[0],
        paddle1.position[1],
        0.0,
    )
    GL.glRotatef(math.degrees(paddle1.rotation), 0.0, 0.0, 1.0)

    GL.glBegin(GL.GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        GL.glVertex3f(
            p1_v_ms[0],
            p1_v_ms[1],
            p1_v_ms[2],
        )
    GL.glEnd()
    # doc-region-end of paddle 1

    # draw the square
    # given that no nodes are defined relative to the square, we do not need
    # to push a matrix.  Here we will do so anyway, just to clarify what is
    # happening
    GL.glPushMatrix()
    # the current model matrix will be copied and then the copy will be
    # pushed onto the model stack
    GL.glColor3f(0.0, 0.0, 1.0)

    # these functions change the current model matrix
    GL.glTranslate(0.0, 0.0, -1.0)
    GL.glRotatef(math.degrees(rotation_around_paddle1), 0.0, 0.0, 1.0)
    GL.glTranslate(2.0, 0.0, 0.0)
    GL.glRotatef(math.degrees(square_rotation), 0.0, 0.0, 1.0)

    GL.glBegin(GL.GL_QUADS)
    for ms in square_vertices:
        GL.glVertex3f(ms[0], ms[1], ms[2])
    GL.glEnd()
    GL.glPopMatrix()
    # the mode matrix that was on the model stack before the square
    # was drawn will be restored
    GL.glPopMatrix()

    # draw paddle 2.  Nothing is defined relative to paddle to, so we don't
    # need to push matrix, and on the next iteration of the event loop,
    # all matrices will be cleared to identity, so who cares if we
    # mutate the values for now.
    GL.glColor3f(*iter(paddle2.color))

    GL.glTranslate(
        paddle2.position[0],
        paddle2.position[1],
        0.0,
    )
    GL.glRotatef(math.degrees(paddle2.rotation), 0.0, 0.0, 1.0)

    GL.glBegin(GL.GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        GL.glVertex3f(
            p2_v_ms[0],
            p2_v_ms[1],
            p2_v_ms[2],
        )
    GL.glEnd()

    glfw.swap_buffers(window)


glfw.terminate()
