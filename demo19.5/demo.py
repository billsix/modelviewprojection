# Copyright (c) 2018-2020 William Emerison Six
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

# PURPOSE
# use a game controller.  Tested with Wired XBOX 360 controller

import sys
import os
import numpy as np
import math
from OpenGL.GL import *
from OpenGL.GLU import *
import glfw
import pyMatrixStack as ms

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 19.5", None, None)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)

# Install a key handler


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0, 0.0, 0.0, 1.0)

# NEW - TODO - talk about opengl matricies and z pos/neg
glEnable(GL_DEPTH_TEST)
glClearDepth(1.0)
glDepthFunc(GL_LEQUAL)


def draw_in_square_viewport():
    glClearColor(0.2, 0.2, 0.2, 1.0)  # r  # g  # b  # a
    glClear(GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)
    min = width if width < height else height

    glEnable(GL_SCISSOR_TEST)
    glScissor(
        int((width - min) / 2.0),  # min x
        int((height - min) / 2.0),  # min y
        min,  # width x
        min,
    )  # width y

    glClearColor(0.0, 0.0, 0.0, 1.0)  # r  # g  # b  # a
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    glViewport(
        int(0.0 + (width - min) / 2.0),  # min x
        int(0.0 + (height - min) / 2.0),  # min y
        min,  # width x
        min,
    )  # width y


class Paddle:
    def __init__(
        self,
        r,
        g,
        b,
        initial_position,
        rotation=0.0,
        input_offset_x=0.0,
        input_offset_y=0.0,
    ):
        self.r = r
        self.g = g
        self.b = b
        self.rotation = rotation
        self.input_offset_x = input_offset_x
        self.input_offset_y = input_offset_y
        self.initial_position = initial_position
        self.vertices = np.array(
            [
                [-10.0, -30.0, 0.0],
                [10.0, -30.0, 0.0],
                [10.0, 30.0, 0.0],
                [-10.0, 30.0, 0.0],
            ],
            dtype=np.float32,
        )


paddle1 = Paddle(r=0.578123, g=0.0, b=1.0, initial_position=np.array([-90.0, 0.0, 0.0]))

paddle2 = Paddle(r=1.0, g=0.0, b=0.0, initial_position=np.array([90.0, 0.0, 0.0]))


# NEW
number_of_controllers = glfw.joystick_present(glfw.JOYSTICK_1)
print(number_of_controllers)

moving_camera_x = 0.0
moving_camera_y = 0.0
moving_camera_z = 400.0
moving_camera_rot_y = 0.0
moving_camera_rot_x = 0.0


square_rotation = 0.0
rotation_around_paddle1 = 0.0


def handle_inputs():
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global moving_camera_x
    global moving_camera_y
    global moving_camera_z
    global moving_camera_rot_x
    global moving_camera_rot_y

    move_multiple = 15.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        moving_camera_rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        moving_camera_rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        moving_camera_rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        moving_camera_rot_x -= 0.03
    # //TODO -  explaing movement on XZ-plane
    # //TODO -  show camera movement in graphviz
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        moving_camera_x -= move_multiple * math.sin(moving_camera_rot_y)
        moving_camera_z -= move_multiple * math.cos(moving_camera_rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        moving_camera_x += move_multiple * math.sin(moving_camera_rot_y)
        moving_camera_z += move_multiple * math.cos(moving_camera_rot_y)

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.input_offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.input_offset_y += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.input_offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.input_offset_y += 10.0

    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1


square_vertices = np.array(
    [[-5.0, -5.0, 0.0], [5.0, -5.0, 0.0], [5.0, 5.0, 0.0], [-5.0, 5.0, 0.0]],
    dtype=np.float32,
)


TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

# Loop until the user closes the window
while not glfw.window_should_close(window):
    # poll the time to try to get a constant framerate
    while (
        glfw.get_time() < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass
    # set for comparison on the next frame
    time_at_beginning_of_previous_frame = glfw.get_time()

    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    draw_in_square_viewport()
    handle_inputs()

    # set the model, view, and projection matrix to the identity
    # matrix.  This just means that the functions (currently)
    # will not transform data.
    # In univariate terms, f(x) = x
    ms.setToIdentityMatrix(ms.MatrixStack.model)
    ms.setToIdentityMatrix(ms.MatrixStack.view)
    ms.setToIdentityMatrix(ms.MatrixStack.projection)

    # change the perspective matrix to convert the frustum
    # to NDC.
    # set the projection matrix to be perspective
    ms.perspective(
        fov=45.0,
        aspectRatio=1.0,  # since the viewport is always square
        nearZ=0.1,
        farZ=10000.0,
    )

    # NEW -- handle controller input
    axes_list = glfw.get_joystick_axes(glfw.JOYSTICK_1)

    # axes_list[0] is controller 1
    # axes_list[0][0] is controller 1's vertical axis

    # the value can be between -1 and 1.  also, there is a dead zone
    # area around 0, meaning that the value of a non-pressed controller
    # may register a random value.  Therefore, set up a gating value
    # (in this case 0.19), which will not register to the application
    # as an input
    if len(axes_list) >= 1 and math.fabs(float(axes_list[0][0])) > 0.19:
        # vertical
        # TODO - show the math
        moving_camera_x += 10.0 * axes_list[0][0] * math.cos(moving_camera_rot_y)
        moving_camera_z -= 10.0 * axes_list[0][0] * math.sin(moving_camera_rot_y)
    # axes_list[0][1] is the horizontal component of the left stick
    if len(axes_list) >= 1 and math.fabs(float(axes_list[0][1])) > 0.19:
        # horizontal
        # TODO - show the math
        moving_camera_x += 10.0 * axes_list[0][1] * math.sin(moving_camera_rot_y)
        moving_camera_z += 10.0 * axes_list[0][1] * math.cos(moving_camera_rot_y)

    # axes_list[0][1] is the horizontal component of the right stick
    if math.fabs(axes_list[0][3]) > 0.19:
        moving_camera_rot_y -= 3.0 * axes_list[0][3] * 0.01
    # axes_list[0][4] is the vertical component of the right stick
    if math.fabs(axes_list[0][4]) > 0.19:
        moving_camera_rot_x += axes_list[0][4] * 0.01

    glMatrixMode(GL_PROJECTION)
    glLoadMatrixf(
        np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.projection).T)
    )

    # The camera's position is described as follows
    # ms.translate(ms.MatrixStack.view,
    #              moving_camera_x,
    #              moving_camera_y,
    #              moving_camera_z)
    # ms.rotate_y(ms.MatrixStack.view,moving_camera_rot_y)
    # ms.rotate_x(ms.MatrixStack.view,moving_camera_rot_x)
    #
    # Therefore, to take the object's world space coordinates
    # and transform them into camera space, we need to
    # do the inverse operations to the view stack.

    ms.rotate_x(ms.MatrixStack.view, -moving_camera_rot_x)
    ms.rotate_y(ms.MatrixStack.view, -moving_camera_rot_y)
    ms.translate(
        ms.MatrixStack.view, -moving_camera_x, -moving_camera_y, -moving_camera_z
    )
    with ms.PushMatrix(ms.MatrixStack.model):

        # draw paddle 1
        glColor3f(paddle1.r, paddle1.g, paddle1.b)

        ms.translate(
            ms.MatrixStack.model, paddle1.input_offset_x, paddle1.input_offset_y, 0.0
        )
        ms.translate(
            ms.MatrixStack.model,
            paddle1.initial_position[0],
            paddle1.initial_position[1],
            0.0,
        )
        ms.rotate_z(ms.MatrixStack.model, paddle1.rotation)

        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(
            np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T)
        )
        glBegin(GL_QUADS)
        for model_space in paddle1.vertices:
            glVertex3f(model_space[0], model_space[1], model_space[2])
        glEnd()

        # # draw the square
        glColor3f(0.0, 0.0, 1.0)  # r  # g  # b

        ms.translate(ms.MatrixStack.model, 0.0, 0.0, -10.0)
        ms.rotate_z(ms.MatrixStack.model, rotation_around_paddle1)
        ms.translate(ms.MatrixStack.model, 20.0, 0.0, 0.0)
        ms.rotate_z(ms.MatrixStack.model, square_rotation)

        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(
            np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T)
        )
        glBegin(GL_QUADS)
        for model_space in square_vertices:
            glVertex3f(model_space[0], model_space[1], model_space[2])
        glEnd()

    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    ms.translate(
        ms.MatrixStack.model, paddle2.input_offset_x, paddle2.input_offset_y, 0.0
    )
    ms.translate(
        ms.MatrixStack.model,
        paddle2.initial_position[0],
        paddle2.initial_position[1],
        0.0,
    )
    ms.rotate_z(ms.MatrixStack.model, paddle2.rotation)

    glMatrixMode(GL_MODELVIEW)
    glLoadMatrixf(np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T))
    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        glVertex3f(model_space[0], model_space[1], model_space[2])
    glEnd()

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
