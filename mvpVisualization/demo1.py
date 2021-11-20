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


import sys
import os
import numpy as np
import math
from OpenGL.GL import *
from OpenGL.GLU import *
import glfw
import pyMatrixStack as ms
import imgui
from imgui.integrations.glfw import GlfwRenderer



if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)

window = glfw.create_window(
    800, 800, "ModelViewProjection Demo of Coordinates", None, None
)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)
imgui.create_context()
impl = GlfwRenderer(window)

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
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    min = width if width < height else height

    glViewport(
        int(0.0 + (width - min) / 2.0),  # min x
        int(0.0 + (height - min) / 2.0),  # min y
        min,  # width x
        min,
    )  # width y

    glEnable(GL_SCISSOR_TEST)
    glScissor(
        int(0.0 + (width - min) / 2.0),  # min x
        int(0.0 + (height - min) / 2.0),  # min y
        min,  # width x
        min,
    )  # width y

    glClearColor(0.0, 0.0, 0.0, 1.0)  # r  # g  # b  # a
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)


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

paddle2 = Paddle(r=1.0, g=1.0, b=0.2, initial_position=np.array([90.0, 0.0, 0.0]))

moving_camera_r = 300
moving_camera_rot_y = math.radians(45.0)
moving_camera_rot_x = math.radians(-35.264)


square_rotation = 0.0
rotation_around_paddle1 = 0.0


def handle_inputs():
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global moving_camera_rot_y
    global moving_camera_rot_x

    move_multiple = 15.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        moving_camera_rot_y -= math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        moving_camera_rot_y += math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        moving_camera_rot_x += math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        moving_camera_rot_x -= math.radians(1.0) % 360.0

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


def draw_ground():
    # ascontiguousarray puts the array in column major order
    glLoadMatrixf(np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T))
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_LINES)
    for x in range(-200, 201, 20):
        for z in range(-200, 201, 20):
            glVertex3f(float(-x), float(-50.0), float(z))
            glVertex3f(float(x), float(-50.0), float(z))
            glVertex3f(float(x), float(-50.0), float(-z))
            glVertex3f(float(x), float(-50.0), float(z))

    glEnd()


def draw_y_axis():

    # ascontiguousarray puts the array in column major order
    glLoadMatrixf(np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T))

    glLineWidth(3.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 1.0, 0.0)

    # arrow
    glVertex3f(0.0, 1.0, 0.0)
    glVertex3f(0.25, 0.75, 0.0)

    glVertex3f(0.0, 1.0, 0.0)
    glVertex3f(-0.25, 0.75, 0.0)
    glEnd()


def draw_axises(grayed_out=False):

    with ms.push_matrix(ms.MatrixStack.model):
        ms.scale(ms.MatrixStack.model, 10.0, 10.0, 10.0)

        # x axis
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_z(ms.MatrixStack.model, math.radians(-90.0))

            glColor3f(1.0, 0.0, 0.0)
            if grayed_out:
                glColor3f(0.5, 0.5, 0.5)
            draw_y_axis()

        # z
        glColor3f(0.0, 0.0, 1.0)  # blue z
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
            ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))

            glColor3f(0.0, 0.0, 1.0)
            if grayed_out:
                glColor3f(0.5, 0.5, 0.5)
            draw_y_axis()

        # y
        glColor3f(0.0, 1.0, 0.0)  # green y
        if grayed_out:
            glColor3f(0.5, 0.5, 0.5)
        draw_y_axis()


TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

animation_time = 0.0
animation_time_multiplier = 1.0
animation_paused = False


# Loop until the user closes the window
while not glfw.window_should_close(window):
    # poll the time to try to get a constant framerate
    while (
        glfw.get_time() < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass
    # set for comparison on the next frame
    time_at_beginning_of_previous_frame = glfw.get_time()

    if not animation_paused:
        animation_time += 1.0 / 60.0 * animation_time_multiplier


    # Poll for and process events
    glfw.poll_events()
    impl.process_inputs()

    imgui.new_frame()

    imgui.begin("Time", True)

    clicked_animation_paused, animation_paused = imgui.checkbox(
        "Pause", animation_paused
    )
    clicked_animation_time_multiplier, animation_time_multiplier = imgui.slider_float(
        "Sim Speed", animation_time_multiplier, 0.1, 10.0
    )
    if imgui.button("Restart"):
        animation_time = 0.0

    imgui.end()


    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    handle_inputs()

    ms.setToIdentityMatrix(ms.MatrixStack.model)
    ms.setToIdentityMatrix(ms.MatrixStack.view)
    ms.setToIdentityMatrix(ms.MatrixStack.projection)

    # set the projection matrix to be perspective
    ms.perspective(
        fov=45.0, aspectRatio=float(width) / float(height), nearZ=0.1, farZ=10000.0
    )
    # ms.ortho(left=-150.0,
    #          right=150.0,
    #          back=-150.0,
    #          top=150.0,
    #          near=1.0,
    #          far=10000.0)

    glMatrixMode(GL_PROJECTION)
    # ascontiguousarray puts the array in column major order
    glLoadMatrixf(
        np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.projection).T)
    )

    # note - opengl matricies use degrees
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -moving_camera_r)
    ms.rotate_x(ms.MatrixStack.view, -moving_camera_rot_x)
    ms.rotate_y(ms.MatrixStack.view, -moving_camera_rot_y)

    glMatrixMode(GL_MODELVIEW)
    draw_ground()
    draw_axises()

    with ms.PushMatrix(ms.MatrixStack.model):

        # draw paddle 1

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

        draw_axises()
        glColor3f(paddle1.r, paddle1.g, paddle1.b)
        # ascontiguousarray puts the array in column major order
        glLoadMatrixf(
            np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T)
        )
        glBegin(GL_QUADS)
        for model_space in paddle1.vertices:
            glVertex3f(model_space[0], model_space[1], model_space[2])
        glEnd()

        # # draw the square

        ms.translate(ms.MatrixStack.model, 0.0, 0.0, -10.0)
        ms.rotate_z(ms.MatrixStack.model, rotation_around_paddle1)
        ms.translate(ms.MatrixStack.model, 20.0, 0.0, 0.0)
        ms.rotate_z(ms.MatrixStack.model, square_rotation)

        draw_axises()

        glColor3f(0.0, 0.0, 1.0)  # r  # g  # b
        # ascontiguousarray puts the array in column major order
        glLoadMatrixf(
            np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T)
        )
        glBegin(GL_QUADS)
        for model_space in square_vertices:
            glVertex3f(model_space[0], model_space[1], model_space[2])
        glEnd()

    # get back to center of global space

    with ms.PushMatrix(ms.MatrixStack.model):

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

        draw_axises()

        # draw paddle 2
        glColor3f(paddle2.r, paddle2.g, paddle2.b)
        # ascontiguousarray puts the array in column major order
        glLoadMatrixf(
            np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T)
        )
        glBegin(GL_QUADS)
        for model_space in paddle2.vertices:
            glVertex3f(model_space[0], model_space[1], model_space[2])
        glEnd()

    imgui.render()
    impl.render(imgui.get_draw_data())

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
