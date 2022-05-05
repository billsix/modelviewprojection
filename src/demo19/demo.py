# Copyright (c) 2018-2022 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from __future__ import annotations  # to appease Python 3.7-3.9
import sys
import os
import numpy as np
import math
import OpenGL.GL
import OpenGL.GLU
import glfw


import dataclasses

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 19", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

OpenGL.GL.glClearColor(0.0, 0.0, 0.0, 1.0)

OpenGL.GL.glEnable(OpenGL.GL.GL_DEPTH_TEST)
OpenGL.GL.glClearDepth(1.0)
OpenGL.GL.glDepthFunc(OpenGL.GL.GL_LEQUAL)


def draw_in_square_viewport() -> None:
    OpenGL.GL.glClearColor(0.2, 0.2, 0.2, 1.0)
    OpenGL.GL.glClear(OpenGL.GL.GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)
    min = width if width < height else height

    OpenGL.GL.glEnable(OpenGL.GL.GL_SCISSOR_TEST)
    OpenGL.GL.glScissor(
        int((width - min) / 2.0),
        int((height - min) / 2.0),
        min,
        min,
    )

    OpenGL.GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    OpenGL.GL.glClear(OpenGL.GL.GL_COLOR_BUFFER_BIT)
    OpenGL.GL.glDisable(OpenGL.GL.GL_SCISSOR_TEST)

    OpenGL.GL.glViewport(
        int(0.0 + (width - min) / 2.0),
        int(0.0 + (height - min) / 2.0),
        min,
        min,
    )


@dataclasses.dataclass
class Paddle:
    r: float
    g: float
    b: float
    position: any
    rotation: float = 0.0
    vertices: np.array = np.array(
        [
            [-10.0, -30.0, 0.0],
            [10.0, -30.0, 0.0],
            [10.0, 30.0, 0.0],
            [-10.0, 30.0, 0.0],
        ],
        dtype=np.float32,
    )


paddle1: Paddle = Paddle(r=0.578123, g=0.0, b=1.0, position=np.array([-90.0, 0.0, 0.0]))

paddle2: Paddle = Paddle(r=1.0, g=0.0, b=0.0, position=np.array([90.0, 0.0, 0.0]))


number_of_controllers = glfw.joystick_present(glfw.JOYSTICK_1)



@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera: Camera = Camera(x=0.0, y=0.0, z=400.0, rot_y=0.0, rot_x=0.0)


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

    move_multiple = 15.0
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
        paddle1.position[1] -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position[1] += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position[1] -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position[1] += 10.0

    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1


square_vertices: np.array = np.array(
    [[-5.0, -5.0, 0.0], [5.0, -5.0, 0.0], [5.0, 5.0, 0.0], [-5.0, 5.0, 0.0]],
    dtype=np.float32,
)


TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()

while not glfw.window_should_close(window):
    while (
        glfw.get_time() < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass
    time_at_beginning_of_previous_frame = glfw.get_time()

    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    OpenGL.GL.glViewport(0, 0, width, height)
    OpenGL.GL.glClear(OpenGL.GL.GL_COLOR_BUFFER_BIT | OpenGL.GL.GL_DEPTH_BUFFER_BIT)

    draw_in_square_viewport()
    handle_inputs()

    axes_list = glfw.get_joystick_axes(glfw.JOYSTICK_1)
    if len(axes_list) >= 1 and axes_list[0]:
        if math.fabs(float(axes_list[0][0])) > 0.19:
            camera.x += 10.0 * axes_list[0][0] * math.cos(camera.rot_y)
            camera.z -= 10.0 * axes_list[0][0] * math.sin(camera.rot_y)
        if math.fabs(float(axes_list[0][1])) > 0.19:
            camera.x += 10.0 * axes_list[0][1] * math.sin(camera.rot_y)
            camera.z += 10.0 * axes_list[0][1] * math.cos(camera.rot_y)

        if math.fabs(axes_list[0][3]) > 0.19:
            camera.rot_y -= 3.0 * axes_list[0][3] * 0.01
        if math.fabs(axes_list[0][4]) > 0.19:
            camera.rot_x += axes_list[0][4] * 0.01

    # just like putting the identity function on the lambda stack
    OpenGL.GL.glMatrixMode(OpenGL.GL.GL_PROJECTION)
    OpenGL.GL.glLoadIdentity()
    OpenGL.GL.glMatrixMode(OpenGL.GL.GL_MODELVIEW)
    OpenGL.GL.glLoadIdentity()


    # projection
    OpenGL.GL.glMatrixMode(OpenGL.GL.GL_PROJECTION)
    OpenGL.GLU.gluPerspective(
        45.0, #fov
        1.0, #aspectRation
        0.1, # nearZ
        10000.0, # farZ
    )




    # view
    OpenGL.GL.glMatrixMode(OpenGL.GL.GL_MODELVIEW)


    OpenGL.GL.glRotatef(math.degrees(-camera.rot_x), 1.0, 0.0, 0.0)
    OpenGL.GL.glRotatef(math.degrees(-camera.rot_y), 0.0, 1.0, 0.0)
    OpenGL.GL.glTranslate(-camera.x, -camera.y, -camera.z)


    #model

    # paddle  1 and square
    # because 2 nodes are drawn off of world space
    # we need to save onto the current "function",
    # aka matrix, for the subsequent geometry
    # the width statement ensures that the matrix is
    # pushed onto a stack, and when the with block ends,
    # it will be automatically popped off of the stack
    OpenGL.GL.glPushMatrix()

    OpenGL.GL.glColor3f(paddle1.r, paddle1.g, paddle1.b)

    OpenGL.GL.glTranslate(
        paddle1.position[0],
        paddle1.position[1],
        0.0,
    )
    OpenGL.GL.glRotatef(math.degrees(paddle1.rotation), 0.0, 0.0, 1.0)

    OpenGL.GL.glBegin(OpenGL.GL.GL_QUADS)
    for model_space in paddle1.vertices:
        OpenGL.GL.glVertex3f(model_space[0], model_space[1], model_space[2])
    OpenGL.GL.glEnd()

    # end of paddle 1

    # draw the square
    # given that no nodes are defined relative to the square, we do not need
    # to push a marix.  Here we will do so anyways, just to clarify what is
    # happening
    OpenGL.GL.glPushMatrix()
    # the current model matrix will be copied and then the copy will be
    # pushed onto the model stack
    OpenGL.GL.glColor3f(0.0, 0.0, 1.0)

    # these functions change the current model matrix
    OpenGL.GL.glTranslate(0.0, 0.0, -10.0)
    OpenGL.GL.glRotatef(math.degrees(rotation_around_paddle1), 0.0, 0.0, 1.0)
    OpenGL.GL.glTranslate(20.0, 0.0, 0.0)
    OpenGL.GL.glRotatef(math.degrees(square_rotation), 0.0, 0.0, 1.0)

    OpenGL.GL.glBegin(OpenGL.GL.GL_QUADS)
    for model_space in square_vertices:
        OpenGL.GL.glVertex3f(model_space[0], model_space[1], model_space[2])
    OpenGL.GL.glEnd()
    OpenGL.GL.glPopMatrix()
    # the mode matrix that was on the model stack before the square
    # was drawn will be restored
    OpenGL.GL.glPopMatrix()


    # draw paddle 2.  Nothing is defined relative to paddle to, so we don't
    # need to push matrix, and on the next iteration of the event loop,
    # all matricies will be cleared to identity, so who cares if we
    # mutate the values for now.
    OpenGL.GL.glColor3f(paddle2.r, paddle2.g, paddle2.b)

    OpenGL.GL.glTranslate(
        paddle2.position[0],
        paddle2.position[1],
        0.0,
    )
    OpenGL.GL.glRotatef(math.degrees(paddle2.rotation), 0.0, 0.0, 1.0)

    OpenGL.GL.glBegin(OpenGL.GL.GL_QUADS)
    for model_space in paddle2.vertices:
        OpenGL.GL.glVertex3f(model_space[0], model_space[1], model_space[2])
    OpenGL.GL.glEnd()

    glfw.swap_buffers(window)


glfw.terminate()
