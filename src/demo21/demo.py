# Copyright (c) 2018-2024 William Emerison Six
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
import sys
import os
import numpy as np
import math
from OpenGL.GL import (
    glClear,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    glViewport,
    glClearColor,
    glEnable,
    glDisable,
    glClearDepth,
    glDepthFunc,
    GL_DEPTH_TEST,
    GL_LEQUAL,
    GL_TRUE,
    GL_BLEND,
    glBlendFunc,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
    glGenVertexArrays,
    glBindVertexArray,
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    glGenBuffers,
    glBindBuffer,
    GL_ARRAY_BUFFER,
    glGetAttribLocation,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    GL_FLOAT,
    glBufferData,
    GL_STATIC_DRAW,
    glUseProgram,
    glGetUniformLocation,
    glUniformMatrix4fv,
    glDrawArrays,
    GL_LINES,
    GL_TRIANGLES,
    glDeleteVertexArrays,
    glDeleteShader,
    glDeleteBuffers,
    glDeleteProgram
)

from dataclasses import dataclass, field

import ctypes

# new - SHADERS
import OpenGL.GL.shaders as shaders
import glfw
import pyMatrixStack as ms

import imgui
from imgui.integrations.glfw import GlfwRenderer
import staticlocal

if not glfw.init():
    sys.exit()

# NEW - for shader location
pwd = os.path.dirname(os.path.abspath(__file__))

# NEW - for shaders
glfloat_size = 4
floatsPerVertex = 3
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
window = glfw.create_window(500, 500, "ModelViewProjection Demo 26 ", None, None)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)


impl = GlfwRenderer(window)

# Install a key handler


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0, 0.0, 0.0, 1.0)


glClearDepth(1.0)
glDepthFunc(GL_LEQUAL)
glEnable(GL_DEPTH_TEST)

__enable_blend__ = True
if __enable_blend__:
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


def _default_paddle_verticies() -> np.array:
    return np.array(
        [
            [-10.0, -30.0, 0.0],
            [10.0, -30.0, 0.0],
            [10.0, 30.0, 0.0],
            [10.0, 30.0, 0.0],
            [-10.0, 30.0, 0.0],
            [-10.0, -30.0, 0.0],
        ],
        dtype=np.float32,
    )


@dataclass
class Paddle:
    r: float
    g: float
    b: float
    position: any
    rotation: float = 0.0
    vertices: np.array = field(default_factory=_default_paddle_verticies)

    vao: int = 0
    vbo: int = 0
    shader: int = 0

    def prepare_to_render(self):
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices
        self.numberOfVertices = np.size(vertices) // floatsPerVertex
        # fmt: off
        color = np.array(
            [
                self.r, self.g, self.b, 0.75,
                self.r, self.g, self.b, 0.75,
                self.r, self.g, self.b, 0.75,
                self.r, self.g, self.b, 0.75,
                self.r, self.g, self.b, 0.75,
                self.r, self.g, self.b, 0.75,
            ],
            dtype=np.float32,
        )
        # fmt: on

        self.numberOfColors = np.size(color) // floatsPerColor

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
            position, floatsPerVertex, GL_FLOAT, False, 0, ctypes.c_void_p(0)
        )

        glBufferData(
            GL_ARRAY_BUFFER, glfloat_size * np.size(vertices), vertices, GL_STATIC_DRAW
        )

        # send the modelspace data to the GPU
        vboColor = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vboColor)

        colorAttribLoc = glGetAttribLocation(self.shader, "color_in")
        glEnableVertexAttribArray(colorAttribLoc)
        glVertexAttribPointer(
            colorAttribLoc, floatsPerColor, GL_FLOAT, False, 0, ctypes.c_void_p(0)
        )

        glBufferData(
            GL_ARRAY_BUFFER, glfloat_size * np.size(color), color, GL_STATIC_DRAW
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

        mvpMatrixLoc = glGetUniformLocation(self.shader, "mvpMatrix")
        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            mvpMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
                dtype=np.float32,
            ),
        )
        glDrawArrays(GL_TRIANGLES, 0, self.numberOfVertices)
        glBindVertexArray(0)


paddle1 = Paddle(r=0.578123, g=0.0, b=1.0, position=np.array([-90.0, 0.0, 0.0]))
paddle1.prepare_to_render()
paddle2 = Paddle(r=1.0, g=0.0, b=0.0, position=np.array([90.0, 0.0, 0.0]))
paddle2.prepare_to_render()



def _default_square_verticies() -> np.array:
    return np.array(
        [
            [-5.0, -5.0, 0.0],
            [5.0, -5.0, 0.0],
            [5.0, 5.0, 0.0],
            [5.0, 5.0, 0.0],
            [-5.0, 5.0, 0.0],
            [-5.0, -5.0, 0.0],
        ],
        dtype=np.float32,
    )


@dataclass
class Square(Paddle):
    rotation_around_paddle1: float = 0.0
    vertices: np.array = field(default_factory=_default_square_verticies)


square = Square(r=0.0, g=0.0, b=1.0, position=[0.0, 0.0, 0.0])

square.prepare_to_render()

number_of_controllers = glfw.joystick_present(glfw.JOYSTICK_1)


@dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera = Camera(x=0.0, y=0.0, z=400.0, rot_y=0.0, rot_x=0.0)


class Ground:
    def __init__(self):
        pass

    def vertices(self):
        # glColor3f(0.1,0.1,0.1)
        verts = []
        for x in range(-600, 601, 20):
            for z in range(-600, 601, 20):
                verts.append(float(-x))
                verts.append(float(-50.0))
                verts.append(float(z))
                verts.append(float(x))
                verts.append(float(-50.0))
                verts.append(float(z))
                verts.append(float(x))
                verts.append(float(-50.0))
                verts.append(float(-z))
                verts.append(float(x))
                verts.append(float(-50.0))
                verts.append(float(z))

        return np.array(verts, dtype=np.float32)

    def prepare_to_render(self):
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices()
        self.numberOfVertices = np.size(vertices) // floatsPerVertex

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
            position, floatsPerVertex, GL_FLOAT, False, 0, ctypes.c_void_p(0)
        )

        glBufferData(
            GL_ARRAY_BUFFER, glfloat_size * np.size(vertices), vertices, GL_STATIC_DRAW
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
        mvpMatrixLoc = glGetUniformLocation(self.shader, "mvpMatrix")
        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            mvpMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
                dtype=np.float32,
            ),
        )
        glDrawArrays(GL_LINES, 0, self.numberOfVertices)
        glBindVertexArray(0)


ground = Ground()
ground.prepare_to_render()


def handle_inputs():
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        square.rotation_around_paddle1 += 0.1

    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square.rotation += 0.1

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


# fmt: off
square_vertices = np.array(
    [[-5.0, -5.0, 0.0],
     [5.0, -5.0, 0.0],
     [5.0, 5.0, 0.0],
     [-5.0, 5.0, 0.0]],
    dtype=np.float32,
)
# fmt: on



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
    impl.process_inputs()

    imgui.new_frame()

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item("Quit", "Cmd+Q", False, True)

            if clicked_quit:
                exit(1)

            imgui.end_menu()
        imgui.end_main_menu_bar()

    imgui.begin("Custom window", True)

    changed, __enable_blend__ = imgui.checkbox(label="Blend", state=__enable_blend__)

    if changed:
        if __enable_blend__:
            glEnable(GL_BLEND)
        else:
            glDisable(GL_BLEND)

    imgui.text("Bar")
    imgui.text_colored("Eggs", 0.2, 1.0, 0.0)

    # use static local istead of try: except
    # normally you would pass the present function name to staticlocal.var
    # , but since we are not in a function, pass the current module
    staticlocal.var(sys.modules[__name__], test_bool=True, test_float=1.0)
    clicked_test_bool, test_bool = imgui.checkbox("test_bool", test_bool)
    clicked_test_float, test_float = imgui.slider_float("float", test_float, 0.0, 1.0)

    imgui.end()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    # set the projection matrix to be perspective
    ms.perspective(
        fov=45.0, aspectRatio=float(width) / float(height), nearZ=0.1, farZ=10000.0
    )

    # render scene
    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClearColor(0.0, 0.0, 0.0, 1.0)  # r  # g  # b  # a
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    handle_inputs()

    axes_list = glfw.get_joystick_axes(glfw.JOYSTICK_1)
    if len(axes_list) >= 1 and axes_list[0]:
        if math.fabs(float(axes_list[0][0])) > 0.1:
            camera.x += (
                10.0 * axes_list[0][0] * math.cos(camera.rot_y)
            )
            camera.z -= (
                10.0 * axes_list[0][0] * math.sin(camera.rot_y)
            )
        if math.fabs(float(axes_list[0][1])) > 0.1:
            camera.x += (
                10.0 * axes_list[0][1] * math.sin(camera.rot_y)
            )
            camera.z += (
                10.0 * axes_list[0][1] * math.cos(camera.rot_y)
            )

        #print(axes_list[0][4])
        if math.fabs(axes_list[0][3]) > 0.10:
            camera.rot_x -= 3.0 * axes_list[0][3] * 0.01
        if math.fabs(axes_list[0][2]) > 0.10:
            camera.rot_y -= axes_list[0][2] * 0.01

    # note - opengl matricies use degrees
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
            # the square's 3 model_space transformations

            ms.translate(ms.MatrixStack.model, 0.0, 0.0, -10.0)
            ms.rotate_z(ms.MatrixStack.model, square.rotation_around_paddle1)

            ms.translate(ms.MatrixStack.model, 20.0, 0.0, 0.0)
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
