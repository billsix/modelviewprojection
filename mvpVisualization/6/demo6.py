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


import sys
import os
import numpy as np
import math
from OpenGL.GL import *
import OpenGL.GL.shaders as shaders
import glfw
import pyMatrixStack as ms
import atexit
import colorsys
import imgui
from imgui.integrations.glfw import GlfwRenderer
import staticlocal

from dataclasses import dataclass


# NEW - for shader location
pwd = os.path.dirname(os.path.abspath(__file__))

# NEW - for shaders
glfloat_size = 4
floatsPerVertex = 3
floatsPerColor = 3

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
# for osx
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)


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
glClearDepth(1.0)
glDepthFunc(GL_LESS)
glEnable(GL_DEPTH_TEST)


def on_exit():
    # delete the objects
    paddle1.__del__()
    paddle2.__del__()
    square.__del__()

    # normally in Python, you should call "del paddle1",
    # but that would not guarantee that the object would
    # actually be garbage collected at that moment, and
    # the OpenGL context could be destroyed before the garbage
    # collection happens, therefore, force the destruction
    # of the VAO and VBO by immediately calling __del__
    #
    # This is not normal Python practice to call
    # this type of method directly, but oh well.


atexit.register(on_exit)


def draw_in_square_viewport() -> None:
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)
    min = width if width < height else height

    glEnable(GL_SCISSOR_TEST)
    glScissor(
        int((width - min) / 2.0),
        int((height - min) / 2.0),
        min,
        min,
    )

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    glViewport(
        int(0.0 + (width - min) / 2.0),
        int(0.0 + (height - min) / 2.0),
        min,
        min,
    )


@dataclass
class Paddle:
    r: float
    g: float
    b: float
    position: any
    rotation: float = 0.0
    vertices: np.array = np.array(
        [
            -10.0,
            -30.0,
            0.0,
            10.0,
            -30.0,
            0.0,
            10.0,
            30.0,
            0.0,
            10.0,
            30.0,
            0.0,
            -10.0,
            30.0,
            0.0,
            -10.0,
            -30.0,
            0.0,
        ],
        dtype=np.float32,
    )
    vao: int = 0
    vbo: int = 0
    shader: int = 0

    def prepare_to_render(self):
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices
        self.numberOfVertices = np.size(vertices) // floatsPerVertex
        color = np.array(
            [
                self.r,
                self.g,
                self.b,
                self.r,
                self.g,
                self.b,
                self.r,
                self.g,
                self.b,
                self.r,
                self.g,
                self.b,
                self.r,
                self.g,
                self.b,
                self.r,
                self.g,
                self.b,
            ],
            dtype=np.float32,
        )
        self.numberOfColors = np.size(color) // floatsPerColor

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # initialize shaders

        with open(os.path.join(pwd, "triangle.vert"), "r") as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, "triangle.frag"), "r") as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vs, fs)

        self.mMatrixLoc = glGetUniformLocation(self.shader, "mMatrix")
        self.vMatrixLoc = glGetUniformLocation(self.shader, "vMatrix")
        self.pMatrixLoc = glGetUniformLocation(self.shader, "pMatrix")

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

    def render(self, time):
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        fov_loc = glGetUniformLocation(self.shader, "fov")
        glUniform1f(fov_loc, 45.0)
        aspect_loc = glGetUniformLocation(self.shader, "aspectRatio")
        glUniform1f(aspect_loc, 1.0)
        nearZ_loc = glGetUniformLocation(self.shader, "nearZ")
        glUniform1f(nearZ_loc, -5.0)
        farZ_loc = glGetUniformLocation(self.shader, "farZ")
        glUniform1f(farZ_loc, -150.00)

        time_loc = glGetUniformLocation(self.shader, "time")
        glUniform1f(time_loc, animation_time)

        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            self.mMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.getCurrentMatrix(ms.MatrixStack.model), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.vMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.getCurrentMatrix(ms.MatrixStack.view), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.pMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.getCurrentMatrix(ms.MatrixStack.projection), dtype=np.float32
            ),
        )
        glDrawArrays(GL_TRIANGLES, 0, self.numberOfVertices)
        glBindVertexArray(0)


paddle1 = Paddle(
    r=0.578123,
    g=0.0,
    b=1.0,
    position=np.array([-90.0, 10.0, 0.0]),
    rotation=math.radians(45.0),
)
paddle1.prepare_to_render()

paddle2 = Paddle(
    r=1.0,
    g=0.0,
    b=0.0,
    position=np.array([90.0, 5.0, 0.0]),
    rotation=math.radians(-20.0),
)

paddle2.prepare_to_render()


@dataclass
class Square(Paddle):
    rotation_around_paddle1: float = 0.0

    vertices: np.array = np.array(
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


square = Square(r=0.0, g=0.0, b=1.0, position=np.array([0.0, 0.0, 0.0]))

square.prepare_to_render()


class Ground:
    def __init__(self):
        pass

    def vertices(self):

        # glColor3f(0.1,0.1,0.1)
        glBegin(GL_LINES)
        verts = []
        for x in range(-200, 201, 10):
            for z in range(-200, 201, 10):
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

        self.mMatrixLoc = glGetUniformLocation(self.shader, "mMatrix")
        self.vMatrixLoc = glGetUniformLocation(self.shader, "vMatrix")
        self.pMatrixLoc = glGetUniformLocation(self.shader, "pMatrix")

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

    def render(self, time):
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        fov_loc = glGetUniformLocation(self.shader, "fov")
        glUniform1f(fov_loc, 45.0)
        aspect_loc = glGetUniformLocation(self.shader, "aspectRatio")
        glUniform1f(aspect_loc, 1.0)
        nearZ_loc = glGetUniformLocation(self.shader, "nearZ")
        glUniform1f(nearZ_loc, -5.0)
        farZ_loc = glGetUniformLocation(self.shader, "farZ")
        glUniform1f(farZ_loc, -150.00)

        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            self.mMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.getCurrentMatrix(ms.MatrixStack.model), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.vMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.getCurrentMatrix(ms.MatrixStack.view), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.pMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.getCurrentMatrix(ms.MatrixStack.projection), dtype=np.float32
            ),
        )
        glDrawArrays(GL_LINES, 0, self.numberOfVertices)
        glBindVertexArray(0)


ground = Ground()
ground.prepare_to_render()


class Axis:
    def __init__(self):
        pass

    def vertices(self):

        # glColor3f(0.1,0.1,0.1)
        glBegin(GL_LINES)
        verts = []
        verts.append(float(0.0))
        verts.append(float(0.0))
        verts.append(float(0.0))

        verts.append(float(0.0))
        verts.append(float(1.0))
        verts.append(float(0.0))

        # arrow
        verts.append(float(0.0))
        verts.append(float(1.0))
        verts.append(float(0.0))

        verts.append(float(0.25))
        verts.append(float(0.75))
        verts.append(float(0.0))

        verts.append(float(0.0))
        verts.append(float(1.0))
        verts.append(float(0.0))

        verts.append(float(-0.25))
        verts.append(float(0.75))
        verts.append(float(0.0))

        return np.array(verts, dtype=np.float32)

    def prepare_to_render(self):
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices()
        self.numberOfVertices = np.size(vertices) // floatsPerVertex

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # initialize shaders

        with open(os.path.join(pwd, "axis.vert"), "r") as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, "axis.frag"), "r") as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vs, fs)

        self.mMatrixLoc = glGetUniformLocation(self.shader, "mMatrix")
        self.vMatrixLoc = glGetUniformLocation(self.shader, "vMatrix")
        self.pMatrixLoc = glGetUniformLocation(self.shader, "pMatrix")
        self.colorLoc = glGetUniformLocation(self.shader, "color")

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

    def render(self, time, grayed_out=False):
        glDisable(GL_DEPTH_TEST)
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        fov_loc = glGetUniformLocation(self.shader, "fov")
        glUniform1f(fov_loc, 45.0)
        aspect_loc = glGetUniformLocation(self.shader, "aspectRatio")
        glUniform1f(aspect_loc, 1.0)
        nearZ_loc = glGetUniformLocation(self.shader, "nearZ")
        glUniform1f(nearZ_loc, -5.0)
        farZ_loc = glGetUniformLocation(self.shader, "farZ")
        glUniform1f(farZ_loc, -150.00)
        # TODO, set the color

        with ms.push_matrix(ms.MatrixStack.model):

            # x axis
            with ms.push_matrix(ms.MatrixStack.model):
                ms.rotate_z(ms.MatrixStack.model, math.radians(-90.0))

                if enlarged_axis:
                    ms.scale(ms.MatrixStack.model, 10.0, 10.0, 10.0)
                glUniform3f(self.colorLoc, 1.0, 0.0, 0.0)
                if grayed_out:
                    glUniform3f(self.colorLoc, 0.5, 0.5, 0.5)

                # ascontiguousarray puts the array in column major order
                glUniformMatrix4fv(
                    self.mMatrixLoc,
                    1,
                    GL_TRUE,
                    np.ascontiguousarray(
                        ms.getCurrentMatrix(ms.MatrixStack.model), dtype=np.float32
                    ),
                )
                glUniformMatrix4fv(
                    self.vMatrixLoc,
                    1,
                    GL_TRUE,
                    np.ascontiguousarray(
                        ms.getCurrentMatrix(ms.MatrixStack.view), dtype=np.float32
                    ),
                )
                glUniformMatrix4fv(
                    self.pMatrixLoc,
                    1,
                    GL_TRUE,
                    np.ascontiguousarray(
                        ms.getCurrentMatrix(ms.MatrixStack.projection), dtype=np.float32
                    ),
                )
                glDrawArrays(GL_LINES, 0, self.numberOfVertices)

            # y
            if enlarged_axis:
                ms.scale(ms.MatrixStack.model, 10.0, 10.0, 10.0)
            glUniform3f(self.colorLoc, 0.0, 1.0, 0.0)
            # glColor3f(0.0,1.0,0.0) # green y
            if grayed_out:
                glUniform3f(self.colorLoc, 0.5, 0.5, 0.5)
            # ascontiguousarray puts the array in column major order
            glUniformMatrix4fv(
                self.mMatrixLoc,
                1,
                GL_TRUE,
                np.ascontiguousarray(
                    ms.getCurrentMatrix(ms.MatrixStack.model), dtype=np.float32
                ),
            )
            glUniformMatrix4fv(
                self.vMatrixLoc,
                1,
                GL_TRUE,
                np.ascontiguousarray(
                    ms.getCurrentMatrix(ms.MatrixStack.view), dtype=np.float32
                ),
            )
            glUniformMatrix4fv(
                self.pMatrixLoc,
                1,
                GL_TRUE,
                np.ascontiguousarray(
                    ms.getCurrentMatrix(ms.MatrixStack.projection), dtype=np.float32
                ),
            )
            glDrawArrays(GL_LINES, 0, self.numberOfVertices)
            glBindVertexArray(0)
        glEnable(GL_DEPTH_TEST)


axis = Axis()
axis.prepare_to_render()


class NDCCube:
    def __init__(self):
        pass

    def vertices(self):

        # glColor3f(0.1,0.1,0.1)
        glBegin(GL_LINES)
        verts = []
        verts.append(-1.0)
        verts.append(-1.0)
        verts.append(-1.0)

        verts.append(1.0)
        verts.append(-1.0)
        verts.append(-1.0)

        verts.append(1.0)
        verts.append(-1.0)
        verts.append(-1.0)

        verts.append(1.0)
        verts.append(1.0)
        verts.append(-1.0)

        verts.append(1.0)
        verts.append(1.0)
        verts.append(-1.0)

        verts.append(-1.0)
        verts.append(1.0)
        verts.append(-1.0)

        verts.append(-1.0)
        verts.append(1.0)
        verts.append(-1.0)

        verts.append(-1.0)
        verts.append(-1.0)
        verts.append(-1.0)

        verts.append(-1.0)
        verts.append(-1.0)
        verts.append(1.0)

        verts.append(1.0)
        verts.append(-1.0)
        verts.append(1.0)

        verts.append(1.0)
        verts.append(-1.0)
        verts.append(1.0)

        verts.append(1.0)
        verts.append(1.0)
        verts.append(1.0)

        verts.append(1.0)
        verts.append(1.0)
        verts.append(1.0)

        verts.append(-1.0)
        verts.append(1.0)
        verts.append(1.0)

        verts.append(-1.0)
        verts.append(1.0)
        verts.append(1.0)

        verts.append(-1.0)
        verts.append(-1.0)
        verts.append(1.0)

        # connect the squares
        verts.append(1.0)
        verts.append(1.0)
        verts.append(-1.0)

        verts.append(1.0)
        verts.append(1.0)
        verts.append(1.0)

        verts.append(1.0)
        verts.append(-1.0)
        verts.append(-1.0)

        verts.append(1.0)
        verts.append(-1.0)
        verts.append(1.0)

        verts.append(-1.0)
        verts.append(1.0)
        verts.append(-1.0)

        verts.append(-1.0)
        verts.append(1.0)
        verts.append(1.0)

        verts.append(-1.0)
        verts.append(-1.0)
        verts.append(-1.0)

        verts.append(-1.0)
        verts.append(-1.0)
        verts.append(1.0)

        return np.array(verts, dtype=np.float32)

    def prepare_to_render(self):
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices()
        self.numberOfVertices = np.size(vertices) // floatsPerVertex

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # initialize shaders

        with open(os.path.join(pwd, "cube.vert"), "r") as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, "cube.frag"), "r") as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vs, fs)

        self.mMatrixLoc = glGetUniformLocation(self.shader, "mMatrix")
        self.vMatrixLoc = glGetUniformLocation(self.shader, "vMatrix")
        self.pMatrixLoc = glGetUniformLocation(self.shader, "pMatrix")

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

    def render(self, time):
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        fov_loc = glGetUniformLocation(self.shader, "fov")
        glUniform1f(fov_loc, 45.0)
        aspect_loc = glGetUniformLocation(self.shader, "aspectRatio")
        glUniform1f(aspect_loc, 1.0)
        nearZ_loc = glGetUniformLocation(self.shader, "nearZ")
        glUniform1f(nearZ_loc, -5.0)
        farZ_loc = glGetUniformLocation(self.shader, "farZ")
        glUniform1f(farZ_loc, -150.00)

        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            self.mMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.getCurrentMatrix(ms.MatrixStack.model), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.vMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.getCurrentMatrix(ms.MatrixStack.view), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.pMatrixLoc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.getCurrentMatrix(ms.MatrixStack.projection), dtype=np.float32
            ),
        )
        glDrawArrays(GL_LINES, 0, self.numberOfVertices)
        glBindVertexArray(0)


cube = NDCCube()
cube.prepare_to_render()


@dataclass
class Camera:
    r: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera = Camera(r=250.0, rot_y=math.radians(0.0), rot_x=math.radians(0.0))


square_rotation = math.radians(90.0)
rotation_around_paddle1 = math.radians(30.0)


def handle_inputs():
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera

    move_multiple = 15.0

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


virtual_camera_position = np.array([-15.0, 20.0, 85.0], dtype=np.float32)
virtual_camera_relative_offset = np.array([-0.0, 0.0, 0.0], dtype=np.float32)

TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

animation_time = 0.0
animation_time_multiplier = 1.0
animation_paused = False
enlarged_axis = True
NDC = False


def highlighted_button(text, start_time, time):
    highlight = time > start_time and (time - start_time) < 5
    if highlight:
        imgui.push_id(str(3))
        r, g, b = colorsys.hsv_to_rgb(0 / 7.0, 0.6, 0.6)
        imgui.push_style_color(imgui.COLOR_BUTTON, r, g, b)
        r, g, b = colorsys.hsv_to_rgb(0 / 7.0, 0.7, 0.7)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, r, g, b)
        r, g, b = colorsys.hsv_to_rgb(0 / 7.0, 0.8, 0.8)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, r, g, b)
    return_value = imgui.button(label=text)
    if highlight:
        imgui.pop_style_color(3)
        imgui.pop_id()
    return return_value


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

    imgui.set_next_window_bg_alpha(0.05)
    imgui.begin("Time", True)

    clicked_animation_paused, animation_paused = imgui.checkbox(
        "Pause", animation_paused
    )
    clicked_camera, camera.r = imgui.slider_float("Camera Radius", camera.r, 10, 1000.0)
    clicked_animation_time_multiplier, animation_time_multiplier = imgui.slider_float(
        "Sim Speed", animation_time_multiplier, 0.1, 10.0
    )
    if imgui.button("Restart"):
        animation_time = 0.0

    if imgui.tree_node(
        "From World Space, Against Arrows, Read Bottom Up", imgui.TREE_NODE_DEFAULT_OPEN
    ):
        if imgui.tree_node("Paddle 1->World", imgui.TREE_NODE_DEFAULT_OPEN):
            imgui.text("f_paddle1_to_world(x) = ")
            imgui.text(" = (")
            imgui.same_line()
            if highlighted_button("T", 5, animation_time):
                animation_time = 5.0
            imgui.same_line()
            imgui.text(" o ")
            imgui.same_line()
            if highlighted_button("R", 10, animation_time):
                animation_time = 10.0
            imgui.same_line()
            imgui.text(" ) (x) ")
            if imgui.tree_node("Square->World", imgui.TREE_NODE_DEFAULT_OPEN):
                imgui.text("f_square_to_world(x) = ")
                imgui.text(" f_square_to_world o (")
                imgui.text("      ")
                imgui.same_line()
                if highlighted_button("R1", 20, animation_time):
                    animation_time = 20.0
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button("T_X", 25, animation_time):
                    animation_time = 25.0
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button("R2", 30, animation_time):
                    animation_time = 30.0
                imgui.same_line()
                imgui.text(" ) (x) ")
                imgui.tree_pop()
            imgui.tree_pop()
        if imgui.tree_node("Paddle 2->World", imgui.TREE_NODE_DEFAULT_OPEN):
            imgui.text("f_paddle2_to_world(x) = (")
            imgui.same_line()
            if highlighted_button("T", 40, animation_time):
                animation_time = 40.0
            imgui.same_line()
            imgui.text(" o ")
            imgui.same_line()
            if highlighted_button("R", 45, animation_time):
                animation_time = 45.0
            imgui.same_line()
            imgui.text(" ) (x) ")
            imgui.tree_pop()
        if imgui.tree_node("Camera->World", imgui.TREE_NODE_DEFAULT_OPEN):
            imgui.text("f_camera_to_world(x) = ")
            imgui.same_line()
            if highlighted_button("T", 55, animation_time):
                animation_time = 55.0
            imgui.same_line()
            imgui.text("(x) ")
            imgui.tree_pop()
        imgui.tree_pop()
    if imgui.tree_node(
        "Towards NDC, With Arrows, Top Down Reading", imgui.TREE_NODE_DEFAULT_OPEN
    ):
        if imgui.tree_node("World->Camera", imgui.TREE_NODE_DEFAULT_OPEN):
            imgui.text("f_camera_to_world^-1(x) = ")
            imgui.text("     f_world_to_camera(x) = ")
            imgui.same_line()
            if highlighted_button("T^-1", 60, animation_time):
                animation_time = 60.0
            imgui.same_line()
            imgui.text("(x)")
            imgui.tree_pop()
        if imgui.tree_node("Camera->NDC", imgui.TREE_NODE_DEFAULT_OPEN):
            imgui.text("f_camera_to_ndc(x) = ortho(x) = ")
            imgui.same_line()
            if highlighted_button("Scale", 65, animation_time):
                animation_time = 65.0
            imgui.same_line()
            imgui.text("(x)")
            imgui.tree_pop()
        imgui.tree_pop()

    imgui.end()

    imgui.set_next_window_bg_alpha(0.05)
    imgui.begin("Display Options", True)

    clicked_enlarged_axises, enlarged_axis = imgui.checkbox(
        "Enlarged Axises", enlarged_axis
    )
    clicked_NDC, NDC = imgui.checkbox("NDC", NDC)
    imgui.end()

    imgui.set_next_window_bg_alpha(0.05)
    imgui.begin("Camera Options", True)

    (
        clicked_virtual_camera_positionx_clicked,
        virtual_camera_position[0],
    ) = imgui.slider_float(
        "Camera X_Worldspace", virtual_camera_position[0], -250, 250.0
    )
    (
        clicked_virtual_camera_positiony_clicked,
        virtual_camera_position[1],
    ) = imgui.slider_float(
        "Camera Y_Worldspace", virtual_camera_position[1], -250, 250.0
    )
    (
        clicked_virtual_camera_positionz_clicked,
        virtual_camera_position[2],
    ) = imgui.slider_float(
        "Camera Z_Worldspace", virtual_camera_position[2], -250, 250.0
    )

    imgui.push_button_repeat(True)
    if imgui.button("Translate -Z_Cameraspace"):
        virtual_camera_position[0] -= math.sin(virtual_camera_rot_y)
        virtual_camera_position[2] -= math.cos(virtual_camera_rot_y)
    if imgui.button("Translate Z_Cameraspace"):
        virtual_camera_position[0] += math.sin(virtual_camera_rot_y)
        virtual_camera_position[2] += math.cos(virtual_camera_rot_y)
    if imgui.button("Translate X_Cameraspace"):
        virtual_camera_position[0] += math.cos(virtual_camera_rot_y)
        virtual_camera_position[2] -= math.sin(virtual_camera_rot_y)
    if imgui.button("Translate -X_Cameraspace"):
        virtual_camera_position[0] -= math.cos(virtual_camera_rot_y)
        virtual_camera_position[2] += math.sin(virtual_camera_rot_y)
    imgui.pop_button_repeat()

    imgui.end()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    handle_inputs()

    draw_in_square_viewport()

    ms.setToIdentityMatrix(ms.MatrixStack.model)
    ms.setToIdentityMatrix(ms.MatrixStack.view)
    ms.setToIdentityMatrix(ms.MatrixStack.projection)

    # set the projection matrix to be ortho
    if NDC:
        ms.ortho(left=-1.0, right=1.0, back=-1.0, top=1.0, near=0.0, far=550.0)
    else:
        ms.ortho(left=-100.0, right=100.0, back=-100.0, top=100.0, near=0.0, far=550.0)

    # note - opengl matricies use degrees
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -camera.r)
    ms.rotate_x(ms.MatrixStack.view, camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)

    # draw NDC in global space, so that we can see the camera space
    # go to NDC
    with ms.PushMatrix(ms.MatrixStack.model):
        cube.render(animation_time)
    with ms.PushMatrix(ms.MatrixStack.model):
        ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
        ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
        ground.render(animation_time)

    if animation_time > 60.0:
        ms.translate(
            ms.MatrixStack.model,
            -virtual_camera_position[0] * min(1.0, (animation_time - 60.0) / 5.0),
            -virtual_camera_position[1] * min(1.0, (animation_time - 60.0) / 5.0),
            -virtual_camera_position[2] * min(1.0, (animation_time - 60.0) / 5.0),
        )

    # draw virtual camera
    if animation_time > 55.0:
        with ms.push_matrix(ms.MatrixStack.model):
            if animation_time > 55.0:
                ms.translate(
                    ms.MatrixStack.model,
                    virtual_camera_position[0]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                    virtual_camera_position[1]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                    virtual_camera_position[2]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                )

            axis.render(animation_time)
            cube.render(animation_time)

    glClear(GL_DEPTH_BUFFER_BIT)

    if animation_time < 5.0:
        axis.render(animation_time)
    else:
        axis.render(animation_time, grayed_out=True)

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

        if animation_time > 0.0 and animation_time < 15.0:
            axis.render(animation_time)
        if animation_time > 15.0:
            # ascontiguousarray puts the array in column major order
            paddle1.render(animation_time)

        # # draw the square

        if animation_time > 20.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                rotation_around_paddle1 * min(1.0, (animation_time - 20.0) / 5.0),
            )
        if animation_time > 25.0:
            ms.translate(
                ms.MatrixStack.model,
                15.0 * min(1.0, (animation_time - 25.0) / 5.0),
                0.0,
                0.0,
            )
        if animation_time > 30.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                square_rotation * min(1.0, (animation_time - 30.0) / 5.0),
            )

        if animation_time > 10.0 and animation_time < 35.0:
            axis.render(animation_time)

        if animation_time > 35.0:
            square.render(animation_time)

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
            axis.render(animation_time)

        if animation_time > 50.0:
            paddle2.render(animation_time)

    imgui.render()
    impl.render(imgui.get_draw_data())

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
