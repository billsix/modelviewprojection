# Copyright (c) 2018-2023 William Emerison Six
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


import math
import sys
from dataclasses import dataclass, field

import glfw
import numpy as np
import pyMatrixStack as ms
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_LEQUAL,
    GL_LINES,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    glBegin,
    glClear,
    glClearColor,
    glClearDepth,
    glColor3f,
    glDepthFunc,
    glEnable,
    glEnd,
    glLineWidth,
    glLoadMatrixf,
    glMatrixMode,
    glVertex3f,
    glViewport,
)
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


imguiio = imgui.get_io()

# Install a key handler


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)


def scroll_callback(window, xoffset, yoffset):
    camera.r = camera.r + -1 * (yoffset * math.log(camera.r))
    if camera.r < 3.0:
        camera.r = 3.0


glfw.set_scroll_callback(window, scroll_callback)


glClearColor(0.0, 0.0, 0.0, 1.0)

# NEW - TODO - talk about opengl matricies and z pos/neg
glEnable(GL_DEPTH_TEST)
glClearDepth(1.0)
glDepthFunc(GL_LEQUAL)


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
                [-10.0, -30.0, 0.0],
                [10.0, -30.0, 0.0],
                [10.0, 30.0, 0.0],
                [-10.0, 30.0, 0.0],
            ],
            dtype=np.float32,
        )
    )


paddle1 = Paddle(
    r=0.578123,
    g=0.0,
    b=1.0,
    position=np.array([-90.0, 10.0, 0.0]),
    rotation=math.radians(45.0),
)

paddle2 = Paddle(
    r=1.0,
    g=0.0,
    b=0.0,
    position=np.array([90.0, 5.0, 0.0]),
    rotation=math.radians(-45.0),
)


@dataclass
class Camera:
    r: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera = Camera(r=300.0, rot_y=math.radians(45.0), rot_x=math.radians(35.264))


square_rotation = math.radians(90.0)
rotation_around_paddle1 = math.radians(30.0)


def handle_inputs(previous_mouse_position) -> None:
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera

    move_multiple = 15.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.rot_x -= math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.rot_x += math.radians(1.0) % 360.0

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

    global animation_time
    if glfw.get_key(window, glfw.KEY_1) == glfw.PRESS:
        animation_time = 5.0
    if glfw.get_key(window, glfw.KEY_2) == glfw.PRESS:
        animation_time = 15.0
    if glfw.get_key(window, glfw.KEY_3) == glfw.PRESS:
        animation_time = 35.0
    if glfw.get_key(window, glfw.KEY_4) == glfw.PRESS:
        animation_time = 55.0
    if glfw.get_key(window, glfw.KEY_5) == glfw.PRESS:
        animation_time = 70.0
    if glfw.get_key(window, glfw.KEY_6) == glfw.PRESS:
        animation_time = 85.0

    new_mouse_position = glfw.get_cursor_pos(window)
    return_none = False
    if glfw.PRESS == glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT):
        if not imguiio.want_capture_mouse:
            if previous_mouse_position:
                camera.rot_y -= 0.2 * math.radians(
                    new_mouse_position[0] - previous_mouse_position[0]
                )
                camera.rot_x += 0.2 * math.radians(
                    new_mouse_position[1] - previous_mouse_position[1]
                )
    else:
        return_none = True

    if camera.rot_x > math.pi / 2.0:
        camera.rot_x = math.pi / 2.0
    if camera.rot_x < -math.pi / 2.0:
        camera.rot_x = -math.pi / 2.0

    return None if return_none else new_mouse_position


square_vertices = np.array(
    [[-5.0, -5.0, 0.0], [5.0, -5.0, 0.0], [5.0, 5.0, 0.0], [-5.0, 5.0, 0.0]],
    dtype=np.float32,
)
virtual_camera_position = np.array([-40.0, 0.0, 80.0], dtype=np.float32)
virtual_camera_rot_y = math.radians(-30.0)
virtual_camera_rot_x = math.radians(15.0)


def draw_ground() -> None:
    # ascontiguousarray puts the array in column major order
    glLoadMatrixf(
        np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.modelview).T)
    )
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_LINES)
    for x in range(-200, 201, 20):
        for z in range(-200, 201, 20):
            glVertex3f(float(-x), float(-50.0), float(z))
            glVertex3f(float(x), float(-50.0), float(z))
            glVertex3f(float(x), float(-50.0), float(-z))
            glVertex3f(float(x), float(-50.0), float(z))

    glEnd()


def draw_y_axis() -> None:
    # ascontiguousarray puts the array in column major order
    glLoadMatrixf(
        np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.modelview).T)
    )

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


def draw_axises(grayed_out: bool = False) -> None:
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


# this isn't really NDC, I scaled it so that it looks good, not be correct
def draw_ndc() -> None:
    glLoadMatrixf(
        np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.modelview).T)
    )

    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(3.0)
    glBegin(GL_LINES)
    glVertex3f(-1.0, -1.0, -1.0)
    glVertex3f(1.0, -1.0, -1.0)

    glVertex3f(1.0, -1.0, -1.0)
    glVertex3f(1.0, 1.0, -1.0)

    glVertex3f(1.0, 1.0, -1.0)
    glVertex3f(-1.0, 1.0, -1.0)

    glVertex3f(-1.0, 1.0, -1.0)
    glVertex3f(-1.0, -1.0, -1.0)

    glVertex3f(-1.0, -1.0, 1.0)
    glVertex3f(1.0, -1.0, 1.0)

    glVertex3f(1.0, -1.0, 1.0)
    glVertex3f(1.0, 1.0, 1.0)

    glVertex3f(1.0, 1.0, 1.0)
    glVertex3f(-1.0, 1.0, 1.0)

    glVertex3f(-1.0, 1.0, 1.0)
    glVertex3f(-1.0, -1.0, 1.0)

    # connect the squares
    glVertex3f(1.0, 1.0, -1.0)
    glVertex3f(1.0, 1.0, 1.0)
    glVertex3f(1.0, -1.0, -1.0)
    glVertex3f(1.0, -1.0, 1.0)
    glVertex3f(-1.0, 1.0, -1.0)
    glVertex3f(-1.0, 1.0, 1.0)
    glVertex3f(-1.0, -1.0, -1.0)
    glVertex3f(-1.0, -1.0, 1.0)

    glEnd()


TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

animation_time = 0.0
animation_time_multiplier = 1.0
animation_paused = False


# local variable for event loop
previous_mouse_position = None

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

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    previous_mouse_position = handle_inputs(previous_mouse_position)

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    # set the projection matrix to be perspective
    ms.perspective(
        fov=45.0,
        aspectRatio=float(width) / float(height),
        nearZ=0.1,
        farZ=10000.0,
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
        np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.projection).T)
    )

    # note - opengl matricies use degrees
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -camera.r)
    ms.rotate_x(ms.MatrixStack.view, camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)

    glMatrixMode(GL_MODELVIEW)

    # draw NDC in global space, so that we can see the camera space
    # go to NDC
    with ms.PushMatrix(ms.MatrixStack.model):
        ms.scale(ms.MatrixStack.model, 5.0, 5.0, 5.0)

        draw_ndc()
    draw_ground()

    if animation_time > 80.0:
        ms.rotate_x(
            ms.MatrixStack.model,
            -virtual_camera_rot_x * min(1.0, (animation_time - 80.0) / 5.0),
        )
    if animation_time > 75.0:
        ms.rotate_y(
            ms.MatrixStack.model,
            -virtual_camera_rot_y * min(1.0, (animation_time - 75.0) / 5.0),
        )
    if animation_time > 70.0:
        ms.translate(
            ms.MatrixStack.model,
            -virtual_camera_position[0] * min(1.0, (animation_time - 70.0) / 5.0),
            -virtual_camera_position[1] * min(1.0, (animation_time - 70.0) / 5.0),
            -virtual_camera_position[2] * min(1.0, (animation_time - 70.0) / 5.0),
        )

    # draw virtual camera
    if animation_time > 55:
        with ms.push_matrix(ms.MatrixStack.model):
            if animation_time > 55:
                ms.translate(
                    ms.MatrixStack.model,
                    virtual_camera_position[0]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                    virtual_camera_position[1]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                    virtual_camera_position[2]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                )
            if animation_time > 60:
                ms.rotate_y(
                    ms.MatrixStack.model,
                    virtual_camera_rot_y * min(1.0, (animation_time - 60.0) / 5.0),
                )
            if animation_time > 65:
                ms.rotate_x(
                    ms.MatrixStack.model,
                    virtual_camera_rot_x * min(1.0, (animation_time - 65.0) / 5.0),
                )

            draw_axises()
            ms.scale(ms.MatrixStack.model, 5.0, 5.0, 5.0)

            draw_ndc()

    if (
        animation_time < 5.0
        or (animation_time > 35.0 and animation_time < 40.0)
        or (animation_time > 50.0 and animation_time < 55.0)
    ):
        draw_axises()
    else:
        draw_axises(grayed_out=True)

    with ms.PushMatrix(ms.MatrixStack.model):
        if animation_time > 5.0:
            ms.translate(
                ms.MatrixStack.model,
                paddle1.position[0] * min(1.0, (animation_time - 5.0) / 5.0),
                paddle1.position[1] * min(1.0, (animation_time - 5.0) / 5.0),
                0.0,
            )
        if animation_time > 10.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle1.rotation * min(1.0, (animation_time - 10.0) / 5.0),
            )

        if animation_time > 5.0 and animation_time < 15.0:
            draw_axises()
        glColor3f(paddle1.r, paddle1.g, paddle1.b)
        if animation_time > 15.0:
            # ascontiguousarray puts the array in column major order
            glLoadMatrixf(
                np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.modelview).T)
            )
            glBegin(GL_QUADS)
            for model_space in paddle1.vertices:
                glVertex3f(model_space[0], model_space[1], model_space[2])
            glEnd()

        # # draw the square

        if animation_time > 15.0:
            ms.translate(
                ms.MatrixStack.model,
                0.0,
                0.0,
                -10.0 * min(1.0, (animation_time - 15.0) / 5.0),
            )
        if animation_time > 20.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                rotation_around_paddle1 * min(1.0, (animation_time - 20.0) / 5.0),
            )
        if animation_time > 25.0:
            ms.translate(
                ms.MatrixStack.model,
                20.0 * min(1.0, (animation_time - 25.0) / 5.0),
                0.0,
                0.0,
            )
        if animation_time > 30.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                square_rotation * min(1.0, (animation_time - 30.0) / 5.0),
            )

        if animation_time > 10.0 and animation_time < 35.0:
            draw_axises()

        glColor3f(0.0, 0.0, 1.0)  # r  # g  # b
        if animation_time > 35.0:
            # ascontiguousarray puts the array in column major order
            glLoadMatrixf(
                np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.modelview).T)
            )
            glBegin(GL_QUADS)
            for model_space in square_vertices:
                glVertex3f(model_space[0], model_space[1], model_space[2])
            glEnd()

    # get back to center of global space

    with ms.PushMatrix(ms.MatrixStack.model):
        # draw paddle 2

        if animation_time > 40.0:
            ms.translate(
                ms.MatrixStack.model,
                paddle2.position[0] * min(1.0, (animation_time - 40.0) / 5.0),
                paddle2.position[1] * min(1.0, (animation_time - 40.0) / 5.0),
                0.0,
            )
        if animation_time > 45.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle2.rotation * min(1.0, (animation_time - 45.0) / 5.0),
            )

        if animation_time > 40.0 and animation_time < 50.0:
            draw_axises()

        glColor3f(paddle2.r, paddle2.g, paddle2.b)
        if animation_time > 50.0:
            # ascontiguousarray puts the array in column major order
            glLoadMatrixf(
                np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.modelview).T)
            )
            glBegin(GL_QUADS)
            for model_space in paddle2.vertices:
                glVertex3f(model_space[0], model_space[1], model_space[2])
            glEnd()

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
