# Copyright (c) 2018-2025 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from __future__ import annotations  # to appease Python 3.7-3.9

import math
import os
import sys
from dataclasses import dataclass, field

import glfw
import numpy as np
import OpenGL.GL.shaders as shaders

# doc-region-begin new imports
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FRAGMENT_SHADER,
    GL_LEQUAL,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    GL_SCISSOR_TEST,
    GL_VERTEX_SHADER,
    glBegin,
    glClear,
    glClearColor,
    glClearDepth,
    glColor3f,
    glDepthFunc,
    glDisable,
    glEnable,
    glEnd,
    glLoadIdentity,
    glMatrixMode,
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glScissor,
    glTranslate,
    glUseProgram,
    glVertex3f,
    glViewport,
)
from OpenGL.GLU import gluPerspective

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

glClearColor(0.0289, 0.071875, 0.0972, 1.0)

glEnable(GL_DEPTH_TEST)
glClearDepth(1.0)
glDepthFunc(GL_LEQUAL)


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
    r: float
    g: float
    b: float
    position: any
    rotation: float = 0.0
    vertices: np.array = field(
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


paddle1: Paddle = Paddle(r=0.578123, g=0.0, b=1.0, position=np.array([-9.0, 0.0, 0.0]))

paddle2: Paddle = Paddle(r=1.0, g=1.0, b=0.0, position=np.array([9.0, 0.0, 0.0]))


number_of_controllers = glfw.joystick_present(glfw.JOYSTICK_1)


@dataclass
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
    vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

with open(os.path.join(pwd, "triangle.frag"), "r") as f:
    fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

shader = shaders.compileProgram(vs, fs)
glUseProgram(shader)
# doc-region-end compile shaders

while not glfw.window_should_close(window):
    while (
        glfw.get_time() < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass
    time_at_beginning_of_previous_frame = glfw.get_time()

    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

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
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # projection
    glMatrixMode(GL_PROJECTION)
    gluPerspective(
        45.0,  # field_of_view
        1.0,  # aspect_ration
        0.1,  # near_z
        1000.0,  # far_z
    )

    # view
    glMatrixMode(GL_MODELVIEW)

    glRotatef(math.degrees(-camera.rot_x), 1.0, 0.0, 0.0)
    glRotatef(math.degrees(-camera.rot_y), 0.0, 1.0, 0.0)
    glTranslate(-camera.x, -camera.y, -camera.z)

    # model

    # paddle  1 and square
    # because 2 nodes are drawn off of world space
    # we need to save onto the current "function",
    # aka matrix, for the subsequent geometry
    # the width statement ensures that the matrix is
    # pushed onto a stack, and when the with block doc-region-ends,
    # it will be automatically popped off of the stack
    glPushMatrix()

    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glTranslate(
        paddle1.position[0],
        paddle1.position[1],
        0.0,
    )
    glRotatef(math.degrees(paddle1.rotation), 0.0, 0.0, 1.0)

    glBegin(GL_QUADS)
    for paddle1_vertex_ms in paddle1.vertices:
        glVertex3f(
            paddle1_vertex_ms[0],
            paddle1_vertex_ms[1],
            paddle1_vertex_ms[2],
        )
    glEnd()
    # doc-region-end of paddle 1

    # draw the square
    # given that no nodes are defined relative to the square, we do not need
    # to push a matrix.  Here we will do so anyway, just to clarify what is
    # happening
    glPushMatrix()
    # the current model matrix will be copied and then the copy will be
    # pushed onto the model stack
    glColor3f(0.0, 0.0, 1.0)

    # these functions change the current model matrix
    glTranslate(0.0, 0.0, -1.0)
    glRotatef(math.degrees(rotation_around_paddle1), 0.0, 0.0, 1.0)
    glTranslate(2.0, 0.0, 0.0)
    glRotatef(math.degrees(square_rotation), 0.0, 0.0, 1.0)

    glBegin(GL_QUADS)
    for model_space in square_vertices:
        glVertex3f(model_space[0], model_space[1], model_space[2])
    glEnd()
    glPopMatrix()
    # the mode matrix that was on the model stack before the square
    # was drawn will be restored
    glPopMatrix()

    # draw paddle 2.  Nothing is defined relative to paddle to, so we don't
    # need to push matrix, and on the next iteration of the event loop,
    # all matrices will be cleared to identity, so who cares if we
    # mutate the values for now.
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glTranslate(
        paddle2.position[0],
        paddle2.position[1],
        0.0,
    )
    glRotatef(math.degrees(paddle2.rotation), 0.0, 0.0, 1.0)

    glBegin(GL_QUADS)
    for paddle2_vertex_ms in paddle2.vertices:
        glVertex3f(
            paddle2_vertex_ms[0],
            paddle2_vertex_ms[1],
            paddle2_vertex_ms[2],
        )
    glEnd()

    glfw.swap_buffers(window)


glfw.terminate()
