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

from __future__ import annotations  # to appease Python 3.7-3.9

import ctypes
import math
import os
import sys
from dataclasses import dataclass, field

import glfw
import imgui
import numpy as np

# new - SHADERS
import OpenGL.GL.shaders as shaders
from colorutils import Color4
from imgui.integrations.glfw import GlfwRenderer
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_LEQUAL,
    GL_LINES,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_TRUE,
    GL_VERTEX_SHADER,
    glBindBuffer,
    glBindVertexArray,
    glBlendFunc,
    glBufferData,
    glClear,
    glClearColor,
    glClearDepth,
    glDeleteBuffers,
    glDeleteProgram,
    glDeleteVertexArrays,
    glDepthFunc,
    glDisable,
    glDrawArrays,
    glEnable,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glGetAttribLocation,
    glGetUniformLocation,
    glUniformMatrix4fv,
    glUseProgram,
    glVertexAttribPointer,
    glViewport,
)

import modelviewprojection.pyMatrixStack as ms

if not glfw.init():
    sys.exit()

# NEW - for shader location
pwd = os.path.dirname(os.path.abspath(__file__))

# NEW - for shaders
glfloat_size = 4
floatsPerVector = 3
floatsPerColor = 4


glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
# CORE profile means no fixed functions.
# compatibility profile would mean access to legacy fixed functions
# compatibility mode isn't supported by every graphics driver,
# particulary on laptops which switch between integrated graphics
# and a discrete card over time based off of usage.
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
# for osx
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

imgui.create_context()
window = glfw.create_window(
    500, 500, "ModelViewProjection Demo 21 ", None, None
)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)


impl = GlfwRenderer(window)

# Install a key handler


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0289, 0.071875, 0.0972, 1.0)


glClearDepth(1.0)
glDepthFunc(GL_LEQUAL)
glEnable(GL_DEPTH_TEST)

__enable_blend__ = True
if __enable_blend__:
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


@dataclass
class Paddle:
    position: any
    color: Color4
    rotation: float = 0.0
    vertices: np.array = field(
        default_factory=lambda: np.array(
            [
                [-1.0, -3.0, 0.0],
                [1.0, -3.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 3.0, 0.0],
                [-1.0, 3.0, 0.0],
                [-1.0, -3.0, 0.0],
            ],
            dtype=np.float32,
        )
    )

    vao: int = 0
    vbo: int = 0
    shader: int = 0

    def prepare_to_render(self):
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices
        self.number_of_vertices = np.size(vertices) // floatsPerVector
        # fmt: off
        color = np.array(
            [
                self.color.r, self.color.g, self.color.b, self.color.a,
                self.color.r, self.color.g, self.color.b, self.color.a,
                self.color.r, self.color.g, self.color.b, self.color.a,
                self.color.r, self.color.g, self.color.b, self.color.a,
                self.color.r, self.color.g, self.color.b, self.color.a,
                self.color.r, self.color.g, self.color.b, self.color.a,
            ],
            dtype=np.float32,
        )
        # fmt: on

        self.number_of_colors = np.size(color) // floatsPerColor

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # initialize shaders

        with open(os.path.join(pwd, "triangle.vert"), "r") as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, "triangle.frag"), "r") as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vs, fs)

        # send the modelspace data to the GPU
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        position = glGetAttribLocation(self.shader, "position")
        glEnableVertexAttribArray(position)

        glVertexAttribPointer(
            position, floatsPerVector, GL_FLOAT, False, 0, ctypes.c_void_p(0)
        )

        glBufferData(
            GL_ARRAY_BUFFER,
            glfloat_size * np.size(vertices),
            vertices,
            GL_STATIC_DRAW,
        )

        # send the modelspace data to the GPU
        vbo_color = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_color)

        color_attrib_loc = glGetAttribLocation(self.shader, "color_in")
        glEnableVertexAttribArray(color_attrib_loc)
        glVertexAttribPointer(
            color_attrib_loc,
            floatsPerColor,
            GL_FLOAT,
            False,
            0,
            ctypes.c_void_p(0),
        )

        glBufferData(
            GL_ARRAY_BUFFER,
            glfloat_size * np.size(color),
            color,
            GL_STATIC_DRAW,
        )

        # reset VAO/VBO to default
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    # destructor
    def __del__(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        glDeleteProgram(self.shader)

    def render(self):
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        mvp_matrix_loc = glGetUniformLocation(self.shader, "mvpMatrix")
        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            mvp_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
                dtype=np.float32,
            ),
        )
        glDrawArrays(GL_TRIANGLES, 0, self.number_of_vertices)
        glBindVertexArray(0)


paddle1 = Paddle(
    color=Color4(r=0.578123, g=0.0, b=1.0, a=0.75),
    position=np.array([-9.0, 0.0, 0.0]),
)
paddle1.prepare_to_render()
paddle2 = Paddle(
    color=Color4(r=1.0, g=1.0, b=0.0, a=0.75),
    position=np.array([9.0, 0.0, 0.0]),
)
paddle2.prepare_to_render()


@dataclass
class Square(Paddle):
    rotation_around_paddle1: float = 0.0
    vertices: np.array = field(
        default_factory=lambda: np.array(
            [
                [-0.5, -0.5, 0.0],
                [0.5, -0.5, 0.0],
                [0.5, 0.5, 0.0],
                [0.5, 0.5, 0.0],
                [-0.5, 0.5, 0.0],
                [-0.5, -0.5, 0.0],
            ],
            dtype=np.float32,
        )
    )


square = Square(
    color=Color4(r=0.0, g=0.0, b=1.0, a=0.75), position=[0.0, 0.0, 0.0]
)

square.prepare_to_render()

number_of_controllers = glfw.joystick_present(glfw.JOYSTICK_1)


@dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera = Camera(x=0.0, y=0.0, z=40.0, rot_y=0.0, rot_x=0.0)


class Ground:
    def __init__(self):
        pass

    def vertices(self):
        # glColor3f(0.1,.1,.1)
        verts = []
        for x in range(-600, 601, 20):
            for z in range(-600, 601, 20):
                verts.append(float(-x))
                verts.append(float(-5.0))
                verts.append(float(z))
                verts.append(float(x))
                verts.append(float(-5.0))
                verts.append(float(z))
                verts.append(float(x))
                verts.append(float(-5.0))
                verts.append(float(-z))
                verts.append(float(x))
                verts.append(float(-5.0))
                verts.append(float(z))

        return np.array(verts, dtype=np.float32)

    def prepare_to_render(self):
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices()
        self.number_of_vertices = np.size(vertices) // floatsPerVector

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # initialize shaders

        with open(os.path.join(pwd, "ground.vert"), "r") as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, "ground.frag"), "r") as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vs, fs)

        # send the modelspace data to the GPU
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        position = glGetAttribLocation(self.shader, "position")
        glEnableVertexAttribArray(position)

        glVertexAttribPointer(
            position, floatsPerVector, GL_FLOAT, False, 0, ctypes.c_void_p(0)
        )

        glBufferData(
            GL_ARRAY_BUFFER,
            glfloat_size * np.size(vertices),
            vertices,
            GL_STATIC_DRAW,
        )

        # send the modelspace data to the GPU
        # TODO, send color to the shader

        # reset VAO/VBO to default
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    # destructor
    def __del__(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        glDeleteProgram(self.shader)

    def render(self):
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        mvp_matrix_loc = glGetUniformLocation(self.shader, "mvpMatrix")
        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            mvp_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
                dtype=np.float32,
            ),
        )
        glDrawArrays(GL_LINES, 0, self.number_of_vertices)
        glBindVertexArray(0)


ground = Ground()
ground.prepare_to_render()


def handle_inputs():
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        square.rotation_around_paddle1 += 0.1

    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square.rotation += 0.1

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
    # //TODO -  explain movement on XZ-plane
    # //TODO -  show camera movement in graphviz
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


# fmt: off
# square_vertices = np.array(
#     [[-5.0, -5.0, 0.0],
#      [5.0, -5.0, 0.0],
#      [5.0, 5.0, 0.0],
#      [-5.0, 5.0, 0.0]],
#     dtype=np.float32,
# )
# fmt: on


TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

# Loop until the user closes the window
while not glfw.window_should_close(window):
    # poll the time to try to get a constant framerate
    while (
        glfw.get_time()
        < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass
    # set for comparison on the next frame
    time_at_beginning_of_previous_frame = glfw.get_time()

    # Poll for and process events
    glfw.poll_events()
    impl.process_inputs()

    imgui.new_frame()

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item(
                "Quit", "Cmd+Q", False, True
            )

            if clicked_quit:
                exit(1)

            imgui.end_menu()
        imgui.end_main_menu_bar()

    imgui.begin("Custom window", True)

    changed, __enable_blend__ = imgui.checkbox(
        label="Blend", state=__enable_blend__
    )

    if changed:
        if __enable_blend__:
            glEnable(GL_BLEND)
        else:
            glDisable(GL_BLEND)

    imgui.end()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    # set the projection matrix to be perspective
    ms.perspective(
        field_of_view=45.0,
        aspect_ratio=float(width) / float(height),
        near_z=0.1,
        far_z=1000.0,
    )

    # render scene
    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClearColor(0.0289, 0.071875, 0.0972, 1.0)  # r  # g  # b  # a
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

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
            camera.rot_y -= 3.0 * axes_list[0][2] * 0.01

    # note - opengl matrices use degrees
    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)
    ms.translate(ms.MatrixStack.view, -camera.x, -camera.y, -camera.z)

    ground.render()

    with ms.push_matrix(ms.MatrixStack.model):
        # draw paddle 1
        # Unlike in previous demos, because the transformations
        # are on a stack, the fns on the model stack can
        # be read forwards, where each operation translates/rotates/scales
        # the current space
        ms.translate(
            ms.MatrixStack.model,
            paddle1.position[0],
            paddle1.position[1],
            0.0,
        )
        ms.rotate_z(ms.MatrixStack.model, paddle1.rotation)
        paddle1.render()

        with ms.push_matrix(ms.MatrixStack.model):
            # # draw the square

            # since the modelstack is already in paddle1's space
            # just add the transformations relative to it
            # before paddle 2 is drawn, we need to remove
            # the square's 3 ms transformations

            ms.translate(ms.MatrixStack.model, 0.0, 0.0, -1.0)
            ms.rotate_z(ms.MatrixStack.model, square.rotation_around_paddle1)

            ms.translate(ms.MatrixStack.model, 2.0, 0.0, 0.0)
            ms.rotate_z(ms.MatrixStack.model, square.rotation)

            square.render()
        # back to padde 1 space
    # get back to center of global space

    with ms.push_matrix(ms.MatrixStack.model):
        # draw paddle 2

        ms.translate(
            ms.MatrixStack.model,
            paddle2.position[0],
            paddle2.position[1],
            0.0,
        )
        ms.rotate_z(ms.MatrixStack.model, paddle2.rotation)
        paddle2.render()

    imgui.render()
    impl.render(imgui.get_draw_data())
    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
