# Copyright (c) 2018-2021 William Emerison Six
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
#
# Replace lambda stacks with matrix stacks.  This is how preshader
# opengl worked (well, they provided matrix operations, but I replaced
# them with my own to make the matrix operations transparent).
#
# The concepts behind the function stack, in which the first function
# added to the stack is the last function applied, hold true for
# matricies as well.  But matricies are a much more efficient
# representation computationally than the function stack,
# and instead of adding fns and later having to remove them,
# we can save onto the current frame of reference with a "glPushStack",
# and restore the saved state by "glPopStack"
#
# Use glPushMatrix and glPopMatrix to save/restore a local coordinate
# system, that way a tree of objects can be drawn without one child
# destroying the relative coordinate system of the parent node.
#
# In mvpVisualization/demoViewWorldTopLevel.py, the grayed out
# coordinate system is one thas has been pushed onto the stack,
# and it regains it's color when it is reactivated by "glPopMatrix"

from __future__ import annotations  # to appease Python 3.7-3.9
import sys
import os
import numpy as np
import math
from OpenGL.GL import *
from OpenGL.GLU import *
import glfw
import pyMatrixStack as ms

from dataclasses import dataclass

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 21", None, None)
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


def draw_in_square_viewport() -> None:
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


@dataclass
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


@dataclass
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
    # //TODO -  explaing movement on XZ-plane
    # //TODO -  show camera movement in graphviz
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


TARGET_FRAMERATE: int = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame: float = glfw.get_time()

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

    # the ms namespace is pyMatrixStack, located in this folder.
    # we need to send the matrix to OpenGL, by setting the matrix
    # mode to be projection, and then call "loadmatrix", which
    # we get from pyMatrixStack.  (Don't sweat the details
    # of ascontigousarray, just copy and paste)
    glMatrixMode(GL_PROJECTION)
    # ascontiguousarray puts the array in column major order
    glLoadMatrixf(
        np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.projection).T)
    )

    # The camera's position is described as follows
    # ms.translate(ms.MatrixStack.view,
    #              camera.x,
    #              camera.y,
    #              camera.z)
    # ms.rotate_y(ms.MatrixStack.view,camera.rot_y)
    # ms.rotate_x(ms.MatrixStack.view,camera.rot_x)
    #
    # Therefore, to take the object's world space coordinates
    # and transform them into camera space, we need to
    # do the inverse operations to the view stack.

    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)
    ms.translate(ms.MatrixStack.view, -camera.x, -camera.y, -camera.z)
    # Each call above actually modifies the matrix, as matricies
    # can be premultiplied together for efficiency.
    #  |a b|     |e f|         |ae+bg  af+bh|
    #  |c d|  *  |g h|  =      |ce+dg  cf+dh|
    # this means that rotate_x, rotate_y, translate, etc
    # are destructive operations.  Instead of creating a stack
    # of matricies, these operations aggregate the transformations,
    # but add no new matricies to the stack

    #
    # but many times we need to hold onto a transformation stack (matrix),
    # so that we can do something else now, and return to this context later,
    # so we have a stack composed of matricies.
    #
    # This is what GLPushMatrix, and GLPopMatrix do.
    #
    # "with" is a Python keyword which allows for bounded contexts, where
    # the library code can specify what happens before execution of the block,
    # and after.  This is similar to RAII within C++, in which a constructor
    # sets a context, and the destructor destroys it.
    #
    # The author uses a debugger to do dynamic analysis of code, as compared
    # to static, as the language knows its own control flow, and where modules
    # are located in the filesystem.  I recommend using a debugger (PDB on linux/macos,
    # the built in functionality in VS Community), to set a breakpoint here, step in,
    # step out, etc
    #
    # "PushMatrix" describes what the function does, but its purpose is to
    # save onto the current coordinate system for later drawing modelspace
    # data.

    # the model stack is currently the identity matrix, meaning
    # it does nothing.  The view and the projection matrix
    # are set to transform from world space into camera space,
    # and then take the frustum and convert it to NDC.

    # save onto the current model stack
    with ms.PushMatrix(ms.MatrixStack.model):

        # draw paddle 1
        # Unlike in previous demos, because the transformations
        # are on a stack, the fns on the model stack can
        # be read forwards, where each operation translates/rotates/scales
        # the current space
        glColor3f(paddle1.r, paddle1.g, paddle1.b)

        ms.translate(
            ms.MatrixStack.model,
            paddle1.position[0],
            paddle1.position[1],
            0.0,
        )
        ms.rotate_z(ms.MatrixStack.model, paddle1.rotation)

        # load our model and view matrix (premultiplied) to
        # openGL's matrix
        # set the current matrix (as we don't want to load into OpenGL's
        # perspective matrix
        glMatrixMode(GL_MODELVIEW)
        # ascontiguousarray puts the array in column major order
        glLoadMatrixf(
            np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T)
        )
        glBegin(GL_QUADS)
        for model_space in paddle1.vertices:
            # NEW!!! glVertex data is specified in modelspace coordinates,
            # but since we loaded the projection matrix and the modelview
            # matrix into OpenGL, glVertex3f will apply those transformations.
            glVertex3f(model_space[0], model_space[1], model_space[2])
        glEnd()

        # # draw the square
        glColor3f(0.0, 0.0, 1.0)  # r  # g  # b

        # since the modelstack is already in paddle1's space
        # just add the transformations relative to it
        # before paddle 2 is drawn, we need to remove
        # the square's 3 model_space transformations
        ms.translate(ms.MatrixStack.model, 0.0, 0.0, -10.0)
        ms.rotate_z(ms.MatrixStack.model, rotation_around_paddle1)
        ms.translate(ms.MatrixStack.model, 20.0, 0.0, 0.0)
        ms.rotate_z(ms.MatrixStack.model, square_rotation)

        # render just like with paddle 1
        glMatrixMode(GL_MODELVIEW)
        # ascontiguousarray puts the array in column major order
        glLoadMatrixf(
            np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T)
        )
        glBegin(GL_QUADS)
        for model_space in square_vertices:
            glVertex3f(model_space[0], model_space[1], model_space[2])
        glEnd()

    # glPopMatrix was implictly called because of the "with" keyword
    # therefore, our model matrix is set to identity.  view is still
    # configure correctly, and is the projection matrix

    # no Need to push matrix here, as this is the last object that
    # we are drawing, and upon the next iteration of the event loop,
    # all 3 matricies will be reset to the identity
    # draw paddle 2
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    ms.translate(
        ms.MatrixStack.model,
        paddle2.position[0],
        paddle2.position[1],
        0.0,
    )
    ms.rotate_z(ms.MatrixStack.model, paddle2.rotation)

    glMatrixMode(GL_MODELVIEW)
    # ascontiguousarray puts the array in column major order
    glLoadMatrixf(np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T))
    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        glVertex3f(model_space[0], model_space[1], model_space[2])
    glEnd()

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
