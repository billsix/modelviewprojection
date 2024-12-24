# Copyright (c) 2018-2024 William Emerison Six
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


import colorsys
import ctypes
import math
import os
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple, Type

import glfw
import imgui
import numpy as np
import OpenGL.GL.shaders as shaders
import pyMatrixStack as ms
from imgui.integrations.glfw import GlfwRenderer
from numpy import ndarray
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_GEOMETRY_SHADER,
    GL_LESS,
    GL_LINES,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_TRUE,
    GL_VERTEX_SHADER,
    glBindBuffer,
    glBindVertexArray,
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
    glUniform1f,
    glUniform2f,
    glUniform3f,
    glUniformMatrix4fv,
    glUseProgram,
    glVertexAttribPointer,
    glViewport,
)

# NEW - for shader location
pwd = os.path.dirname(os.path.abspath(__file__))

# NEW - for shaders
glfloat_size = 4
floatsPerVertex = 3
floatsPerColor = 3

line_thickness = 2.0


@dataclass
class State:
    name: str
    duration: float
    start_time: float = 0.0

    def interpolate(self, time):
        return min(
            1.0,
            (time - self.start_time) / self.duration,
        )


class StepNumber(Enum):
    beginning = State("Beginning", 2.0)
    paddle_1_translate = State("Paddle 1 Translate", 5.0)
    paddle_1_rotate = State("Paddle 1 Rotate", 5.0)
    square_translate_z = State("Square Translate z", 5.0)
    square_rotate_z_first = State("Square Rotate Z First", 5.0)
    square_translate_x = State("Square Translate X", 5.0)
    square_rotate_z_second = State("Square Rotate Z Second", 5.0)
    paddle_2_translate = State("Paddle 2 Translate", 5.0)
    paddle_2_rotate = State("Paddle 2 Rotate", 5.0)
    camera_pre_placement_pause = State("Camera Pre Placement Pause", 5.0)
    camera_translate = State("Camera Translate", 5.0)
    camera_rotate_y = State("Camera Rotate Y", 5.0)
    camera_rotate_x = State("Camera Rotate X", 5.0)
    camera_inverse_translate = State("Camera Inverse Translate", 5.0)
    camera_inverse_rotate_y = State("Camera Inverse Rotate Y", 5.0)
    camera_inverse_rotate_x = State("Camera Inverse Rotate X", 5.0)
    camera_frustum_pause = State("Camera Frustum Pause", 10.0)
    camera_frustum_squash_x = State("Camera Frustum Squash X", 5.0)
    camera_frustum_squash_y = State("Camera Frustum Squash Y", 5.0)
    camera_frustum_translate = State("Camera Frustum Translate", 5.0)
    camera_frustum_scale = State("Camera Frustum Scale", 5.0)
    end = State("End", 5.0)


def calculate_start_times(states_enum: Type[StepNumber]) -> List[State]:
    """Calculate start times for all states."""
    start_time = 0.0
    _updated_states = []
    for state in states_enum:
        current_state = state.value
        current_state.start_time = start_time
        _updated_states.append(current_state)
        start_time += current_state.duration
    return _updated_states


updated_states = calculate_start_times(StepNumber)


# possible things that the viewer may want to center the camera on
class CenterViewOn(Enum):
    ndc = auto()
    paddle1 = auto()
    square = auto()
    paddle2 = auto()
    camera = auto()


# the current object to focus on
center_view_on = CenterViewOn.ndc

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
# for osx
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)


window = glfw.create_window(1920, 1080, "Model View Perspective Projection", None, None)
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


def scroll_callback(win, x_offset, y_offset):
    camera.r = camera.r + -1 * (y_offset * math.log(camera.r))
    if camera.r < 3.0:
        camera.r = 3.0


glfw.set_scroll_callback(window, scroll_callback)


glClearColor(0.0, 18.4 / 255.0, 2.0 / 255.0, 1.0)

# NEW - TODO - talk about opengl matricies and z pos/neg
glClearDepth(1.0)
glDepthFunc(GL_LESS)
glEnable(GL_DEPTH_TEST)


@dataclass
class Paddle:
    r: float
    g: float
    b: float
    position: any
    rotation: float = 0.0
    # fmt: off
    vertices: np.array = field(default_factory=lambda: np.array(
        [
            -1.0, -3.0, 0.0,
            1.0, -3.0, 0.0,
            1.0, 3.0, 0.0,
            1.0, 3.0, 0.0,
            -1.0, 3.0, 0.0,
            -1.0, -3.0, 0.0,
        ],
        dtype=np.float32,
    ))
    # fmt: on
    vao: int = 0
    vbo: int = 0
    shader: int = 0

    def prepare_to_render(self) -> None:
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices
        self.number_of_vertices = np.size(vertices) // floatsPerVertex
        # fmt: off
        color = np.array(
            [self.r, self.g, self.b,
             self.r, self.g, self.b,
             self.r, self.g, self.b,
             self.r, self.g, self.b,
             self.r, self.g, self.b,
             self.r, self.g, self.b,
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

        self.m_matrix_loc = glGetUniformLocation(self.shader, "mMatrix")
        self.v_matrix_loc = glGetUniformLocation(self.shader, "vMatrix")
        self.p_matrix_loc = glGetUniformLocation(self.shader, "pMatrix")

        # send the modelspace data to the GPU
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        position = glGetAttribLocation(self.shader, "position")
        glEnableVertexAttribArray(position)

        glVertexAttribPointer(
            position, floatsPerVertex, GL_FLOAT, False, 0, ctypes.c_void_p(0)
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

    def render(self, time: float) -> None:
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        field_of_view_loc = glGetUniformLocation(self.shader, "field_of_view")
        glUniform1f(field_of_view_loc, 45.0)
        aspect_loc = glGetUniformLocation(self.shader, "aspect_ratio")
        glUniform1f(aspect_loc, 1.0)
        near_z_loc = glGetUniformLocation(self.shader, "near_z")
        glUniform1f(near_z_loc, frustum.near_z)
        far_z_loc = glGetUniformLocation(self.shader, "far_z")
        glUniform1f(far_z_loc, frustum.far_z)

        time_loc = glGetUniformLocation(self.shader, "time")
        glUniform1f(time_loc, animation_time)

        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            self.m_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.model), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.v_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.view), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.p_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.projection),
                dtype=np.float32,
            ),
        )
        glDrawArrays(GL_TRIANGLES, 0, self.number_of_vertices)
        glBindVertexArray(0)


paddle1 = Paddle(
    r=0.578123,
    g=0.0,
    b=1.0,
    position=np.array([-9.0, 1.0, 0.0]),
    rotation=math.radians(45.0),
)
paddle1.prepare_to_render()

paddle2 = Paddle(
    r=1.0,
    g=1.0,
    b=0.0,
    position=np.array([9.0, 0.5, 0.0]),
    rotation=math.radians(-20.0),
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


square = Square(r=0.0, g=0.0, b=1.0, position=np.array([0.0, 0.0, 0.0]))

square.prepare_to_render()


class Ground:
    def __init__(self) -> None:
        pass

    def vertices(self) -> ndarray:
        # glColor3f(0.1,0.1,0.1)
        verts = []
        for x in range(-20, 21, 1):
            for z in range(-20, 21, 1):
                verts.extend([float(-x), -0.0, float(z)])
                verts.extend([float(x), -0.0, float(z)])
                verts.extend([float(x), -0.0, float(-z)])
                verts.extend([float(x), -0.0, float(z)])

        return np.array(verts, dtype=np.float32)

    def prepare_to_render(self) -> None:
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices()
        self.number_of_vertices = np.size(vertices) // floatsPerVertex

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # initialize shaders

        with open(os.path.join(pwd, "ground.vert"), "r") as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, "ground.frag"), "r") as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        with open(os.path.join(pwd, "ground.geom"), "r") as f:
            gs = shaders.compileShader(f.read(), GL_GEOMETRY_SHADER)

        self.shader = shaders.compileProgram(vs, gs, fs)

        self.m_matrix_loc = glGetUniformLocation(self.shader, "mMatrix")
        self.v_matrix_loc = glGetUniformLocation(self.shader, "vMatrix")
        self.p_matrix_loc = glGetUniformLocation(self.shader, "pMatrix")

        self.thickness_loc = glGetUniformLocation(self.shader, "u_thickness")
        self.viewport_loc = glGetUniformLocation(self.shader, "u_viewport_size")

        # send the modelspace data to the GPU
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        position = glGetAttribLocation(self.shader, "position")
        glEnableVertexAttribArray(position)

        glVertexAttribPointer(
            position, floatsPerVertex, GL_FLOAT, False, 0, ctypes.c_void_p(0)
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

    def render(self, time: float) -> None:
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        field_of_view_loc = glGetUniformLocation(self.shader, "field_of_view")
        glUniform1f(field_of_view_loc, 45.0)
        aspect_loc = glGetUniformLocation(self.shader, "aspect_ratio")
        glUniform1f(aspect_loc, 1.0)
        near_z_loc = glGetUniformLocation(self.shader, "near_z")
        glUniform1f(near_z_loc, frustum.near_z)
        far_z_loc = glGetUniformLocation(self.shader, "far_z")
        glUniform1f(far_z_loc, frustum.far_z)

        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            self.m_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.model), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.v_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.view), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.p_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.projection),
                dtype=np.float32,
            ),
        )

        glUniform1f(self.thickness_loc, line_thickness)
        glUniform2f(self.viewport_loc, width, height)

        glDrawArrays(GL_LINES, 0, self.number_of_vertices)
        glBindVertexArray(0)

        if show_ground_axis:
            glDisable(GL_DEPTH_TEST)
            with ms.PushMatrix(ms.MatrixStack.model):
                ms.translate(ms.MatrixStack.model, 0.0, -50.0, 0.0)
                ms.scale(ms.MatrixStack.model, 2.0, 2.0, 2.0)
                axis.render(animation_time)
            glEnable(GL_DEPTH_TEST)


ground = Ground()
ground.prepare_to_render()


class Axis:
    def __init__(self) -> None:
        pass

    def vertices(self) -> ndarray:
        # glColor3f(0.1,0.1,0.1)
        verts = []
        verts.extend([0.0, 0.0, 0.0])
        verts.extend([0.0, 1.0, 0.0])

        # arrow
        verts.extend([0.0, 1.0, 0.0])

        verts.extend([0.25, 0.75, 0.0])

        verts.extend([0.0, 1.0, 0.0])

        verts.extend([-0.25, 0.75, 0.0])

        return np.array(verts, dtype=np.float32)

    def prepare_to_render(self) -> None:
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices()
        self.number_of_vertices = np.size(vertices) // floatsPerVertex

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # initialize shaders

        with open(os.path.join(pwd, "axis.vert"), "r") as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, "axis.frag"), "r") as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        with open(os.path.join(pwd, "axis.geom"), "r") as f:
            gs = shaders.compileShader(f.read(), GL_GEOMETRY_SHADER)

        self.shader = shaders.compileProgram(vs, gs, fs)

        self.m_matrix_loc = glGetUniformLocation(self.shader, "mMatrix")
        self.v_matrix_loc = glGetUniformLocation(self.shader, "vMatrix")
        self.p_matrix_loc = glGetUniformLocation(self.shader, "pMatrix")
        self.colorLoc = glGetUniformLocation(self.shader, "color")

        self.thickness_loc = glGetUniformLocation(self.shader, "u_thickness")
        self.viewport_loc = glGetUniformLocation(self.shader, "u_viewport_size")

        # send the modelspace data to the GPU
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        position = glGetAttribLocation(self.shader, "position")
        glEnableVertexAttribArray(position)

        glVertexAttribPointer(
            position, floatsPerVertex, GL_FLOAT, False, 0, ctypes.c_void_p(0)
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

    def render(self, time: float, grayed_out: bool = False) -> None:
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        field_of_view_loc = glGetUniformLocation(self.shader, "field_of_view")
        glUniform1f(field_of_view_loc, 45.0)
        aspect_loc = glGetUniformLocation(self.shader, "aspect_ratio")
        glUniform1f(aspect_loc, 1.0)
        near_z_loc = glGetUniformLocation(self.shader, "near_z")
        glUniform1f(near_z_loc, frustum.near_z)
        far_z_loc = glGetUniformLocation(self.shader, "far_z")
        glUniform1f(far_z_loc, frustum.far_z)
        # TODO, set the color

        with ms.push_matrix(ms.MatrixStack.model):
            # x axis
            with ms.push_matrix(ms.MatrixStack.model):
                ms.rotate_z(ms.MatrixStack.model, math.radians(-90.0))

                glUniform3f(self.colorLoc, 1.0, 0.0, 0.0)
                if grayed_out:
                    glUniform3f(self.colorLoc, 0.5, 0.5, 0.5)

                # ascontiguousarray puts the array in column major order
                glUniformMatrix4fv(
                    self.m_matrix_loc,
                    1,
                    GL_TRUE,
                    np.ascontiguousarray(
                        ms.get_current_matrix(ms.MatrixStack.model),
                        dtype=np.float32,
                    ),
                )
                glUniformMatrix4fv(
                    self.v_matrix_loc,
                    1,
                    GL_TRUE,
                    np.ascontiguousarray(
                        ms.get_current_matrix(ms.MatrixStack.view),
                        dtype=np.float32,
                    ),
                )
                glUniformMatrix4fv(
                    self.p_matrix_loc,
                    1,
                    GL_TRUE,
                    np.ascontiguousarray(
                        ms.get_current_matrix(ms.MatrixStack.projection),
                        dtype=np.float32,
                    ),
                )
                glUniform1f(self.thickness_loc, line_thickness)
                glUniform2f(self.viewport_loc, width, height)

                glDrawArrays(GL_LINES, 0, self.number_of_vertices)

            # z
            # glColor3f(0.0,0.0,1.0) # blue z
            with ms.push_matrix(ms.MatrixStack.model):
                ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
                ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))

                glUniform3f(self.colorLoc, 0.0, 0.0, 1.0)
                if grayed_out:
                    glUniform3f(self.colorLoc, 0.5, 0.5, 0.5)
                # ascontiguousarray puts the array in column major order
                glUniformMatrix4fv(
                    self.m_matrix_loc,
                    1,
                    GL_TRUE,
                    np.ascontiguousarray(
                        ms.get_current_matrix(ms.MatrixStack.model),
                        dtype=np.float32,
                    ),
                )
                glUniformMatrix4fv(
                    self.v_matrix_loc,
                    1,
                    GL_TRUE,
                    np.ascontiguousarray(
                        ms.get_current_matrix(ms.MatrixStack.view),
                        dtype=np.float32,
                    ),
                )
                glUniformMatrix4fv(
                    self.p_matrix_loc,
                    1,
                    GL_TRUE,
                    np.ascontiguousarray(
                        ms.get_current_matrix(ms.MatrixStack.projection),
                        dtype=np.float32,
                    ),
                )

                glUniform1f(self.thickness_loc, line_thickness)
                glUniform2f(self.viewport_loc, width, height)
                glDrawArrays(GL_LINES, 0, self.number_of_vertices)

            # y
            glUniform3f(self.colorLoc, 0.0, 1.0, 0.0)
            # glColor3f(0.0,1.0,0.0) # green y
            if grayed_out:
                glUniform3f(self.colorLoc, 0.5, 0.5, 0.5)
            # ascontiguousarray puts the array in column major order
            glUniformMatrix4fv(
                self.m_matrix_loc,
                1,
                GL_TRUE,
                np.ascontiguousarray(
                    ms.get_current_matrix(ms.MatrixStack.model),
                    dtype=np.float32,
                ),
            )
            glUniformMatrix4fv(
                self.v_matrix_loc,
                1,
                GL_TRUE,
                np.ascontiguousarray(
                    ms.get_current_matrix(ms.MatrixStack.view), dtype=np.float32
                ),
            )
            glUniformMatrix4fv(
                self.p_matrix_loc,
                1,
                GL_TRUE,
                np.ascontiguousarray(
                    ms.get_current_matrix(ms.MatrixStack.projection),
                    dtype=np.float32,
                ),
            )
            glUniform1f(self.thickness_loc, line_thickness)
            glUniform2f(self.viewport_loc, width, height)
            glDrawArrays(GL_LINES, 0, self.number_of_vertices)
            glBindVertexArray(0)


axis = Axis()
axis.prepare_to_render()


class NDCCube:
    def __init__(self) -> None:
        pass

    def vertices(self) -> ndarray:
        # glColor3f(0.1,0.1,0.1)
        verts = []
        verts.extend([-1.0, -1.0, -1.0])
        verts.extend([1.0, -1.0, -1.0])
        verts.extend([1.0, -1.0, -1.0])
        verts.extend([1.0, 1.0, -1.0])
        verts.extend([1.0, 1.0, -1.0])
        verts.extend([-1.0, 1.0, -1.0])
        verts.extend([-1.0, 1.0, -1.0])
        verts.extend([-1.0, -1.0, -1.0])
        verts.extend([-1.0, -1.0, 1.0])
        verts.extend([1.0, -1.0, 1.0])
        verts.extend([1.0, -1.0, 1.0])
        verts.extend([1.0, 1.0, 1.0])
        verts.extend([1.0, 1.0, 1.0])
        verts.extend([-1.0, 1.0, 1.0])
        verts.extend([-1.0, 1.0, 1.0])
        verts.extend([-1.0, -1.0, 1.0])

        # connect the squares
        verts.extend([1.0, 1.0, -1.0])
        verts.extend([1.0, 1.0, 1.0])
        verts.extend([1.0, -1.0, -1.0])
        verts.extend([1.0, -1.0, 1.0])
        verts.extend([-1.0, 1.0, -1.0])
        verts.extend([-1.0, 1.0, 1.0])
        verts.extend([-1.0, -1.0, -1.0])
        verts.extend([-1.0, -1.0, 1.0])

        return np.array(verts, dtype=np.float32)

    def prepare_to_render(self) -> None:
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices()
        self.number_of_vertices = np.size(vertices) // floatsPerVertex

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # initialize shaders

        with open(os.path.join(pwd, "cube.vert"), "r") as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, "cube.frag"), "r") as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        with open(os.path.join(pwd, "cube.geom"), "r") as f:
            gs = shaders.compileShader(f.read(), GL_GEOMETRY_SHADER)

        self.shader = shaders.compileProgram(vs, gs, fs)

        self.m_matrix_loc = glGetUniformLocation(self.shader, "mMatrix")
        self.v_matrix_loc = glGetUniformLocation(self.shader, "vMatrix")
        self.p_matrix_loc = glGetUniformLocation(self.shader, "pMatrix")

        self.thickness_loc = glGetUniformLocation(self.shader, "u_thickness")
        self.viewport_loc = glGetUniformLocation(self.shader, "u_viewport_size")

        # send the modelspace data to the GPU
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        position = glGetAttribLocation(self.shader, "position")
        glEnableVertexAttribArray(position)

        glVertexAttribPointer(
            position, floatsPerVertex, GL_FLOAT, False, 0, ctypes.c_void_p(0)
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

    def render(self, time: float) -> None:
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        field_of_view_loc = glGetUniformLocation(self.shader, "field_of_view")
        glUniform1f(field_of_view_loc, 45.0)
        aspect_loc = glGetUniformLocation(self.shader, "aspect_ratio")
        glUniform1f(aspect_loc, 1.0)
        near_z_loc = glGetUniformLocation(self.shader, "near_z")
        glUniform1f(near_z_loc, frustum.near_z)
        far_z_loc = glGetUniformLocation(self.shader, "far_z")
        glUniform1f(far_z_loc, frustum.far_z)

        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            self.m_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.model), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.v_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.view), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.p_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.projection),
                dtype=np.float32,
            ),
        )
        glUniform1f(self.thickness_loc, line_thickness)
        glUniform2f(self.viewport_loc, width, height)
        glDrawArrays(GL_LINES, 0, self.number_of_vertices)
        glBindVertexArray(0)


cube = NDCCube()
cube.prepare_to_render()


class Frustum:
    def __init__(
        self, field_of_view: float, aspect_ratio: float, near_z: float, far_z: float
    ) -> None:
        self.field_of_view = field_of_view
        self.aspect_ratio = aspect_ratio
        self.near_z = near_z
        self.far_z = far_z

        # initialize shaders
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        with open(os.path.join(pwd, "frustum.vert"), "r") as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, "frustum.frag"), "r") as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        with open(os.path.join(pwd, "frustum.geom"), "r") as f:
            gs = shaders.compileShader(f.read(), GL_GEOMETRY_SHADER)

        self.shader = shaders.compileProgram(vs, gs, fs)

        self.m_matrix_loc = glGetUniformLocation(self.shader, "mMatrix")
        self.v_matrix_loc = glGetUniformLocation(self.shader, "vMatrix")
        self.p_matrix_loc = glGetUniformLocation(self.shader, "pMatrix")

        self.thickness_loc = glGetUniformLocation(self.shader, "u_thickness")
        self.viewport_loc = glGetUniformLocation(self.shader, "u_viewport_size")

    def prepare_to_render(self) -> None:
        def create_vertices_of_frustum() -> np.array:
            vertices = []

            # front face
            front_top: float = -self.near_z * math.tan(
                math.radians(self.field_of_view) / 2.0
            )
            front_right: float = front_top * self.aspect_ratio

            front_left = -front_right
            front_bottom = -front_top

            vertices.extend([front_left, front_top, self.near_z])
            vertices.extend([front_right, front_top, self.near_z])

            vertices.extend([front_right, front_top, self.near_z])
            vertices.extend([front_right, front_bottom, self.near_z])

            vertices.extend([front_right, front_bottom, self.near_z])
            vertices.extend([front_left, front_bottom, self.near_z])

            vertices.extend([front_left, front_bottom, self.near_z])
            vertices.extend([front_left, front_top, self.near_z])

            # back face
            back_top: float = -self.far_z * math.tan(
                math.radians(self.field_of_view) / 2.0
            )
            back_right: float = back_top * self.aspect_ratio

            back_left = -back_right
            back_bottom = -back_top

            vertices.extend([back_left, back_top, self.far_z])
            vertices.extend([back_right, back_top, self.far_z])

            vertices.extend([back_right, back_top, self.far_z])
            vertices.extend([back_right, back_bottom, self.far_z])

            vertices.extend([back_right, back_bottom, self.far_z])
            vertices.extend([back_left, back_bottom, self.far_z])

            vertices.extend([back_left, back_bottom, self.far_z])
            vertices.extend([back_left, back_top, self.far_z])

            # connect the faces
            vertices.extend([front_left, front_top, self.near_z])
            vertices.extend([back_left, back_top, self.far_z])

            vertices.extend([front_right, front_top, self.near_z])
            vertices.extend([back_right, back_top, self.far_z])

            vertices.extend([front_left, front_bottom, self.near_z])
            vertices.extend([back_left, back_bottom, self.far_z])

            vertices.extend([front_right, front_bottom, self.near_z])
            vertices.extend([back_right, back_bottom, self.far_z])

            # turn vertices into numpy array
            return np.array(vertices, dtype=np.float32)

        vertices = create_vertices_of_frustum()

        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        self.number_of_vertices = np.size(vertices) // floatsPerVertex

        if hasattr(self, "vbo"):
            glDeleteBuffers(1, [self.vbo])
        glBindVertexArray(self.vao)

        # send the modelspace data to the GPU
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        position = glGetAttribLocation(self.shader, "position")
        glEnableVertexAttribArray(position)

        glVertexAttribPointer(
            position, floatsPerVertex, GL_FLOAT, False, 0, ctypes.c_void_p(0)
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

    def render(self, time: float) -> None:
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        field_of_view_loc = glGetUniformLocation(self.shader, "field_of_view")
        glUniform1f(field_of_view_loc, self.field_of_view)
        aspect_loc = glGetUniformLocation(self.shader, "aspect_ratio")
        glUniform1f(aspect_loc, self.aspect_ratio)
        near_z_loc = glGetUniformLocation(self.shader, "near_z")
        glUniform1f(near_z_loc, self.near_z)
        far_z_loc = glGetUniformLocation(self.shader, "far_z")
        glUniform1f(far_z_loc, self.far_z)
        time_loc = glGetUniformLocation(self.shader, "time")
        glUniform1f(time_loc, animation_time)

        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(
            self.m_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.model), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.v_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.view), dtype=np.float32
            ),
        )
        glUniformMatrix4fv(
            self.p_matrix_loc,
            1,
            GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.projection),
                dtype=np.float32,
            ),
        )

        glUniform1f(self.thickness_loc, line_thickness)
        glUniform2f(self.viewport_loc, width, height)

        glDrawArrays(GL_LINES, 0, self.number_of_vertices)
        glBindVertexArray(0)


frustum = Frustum(field_of_view=45.0, aspect_ratio=16.0 / 9.0, near_z=-2.0, far_z=-50.0)
frustum.prepare_to_render()


@dataclass
class Camera:
    r: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera = Camera(r=25.0, rot_y=math.radians(45.0), rot_x=math.radians(35.264))


square_rotation = math.radians(90.0)
rotation_around_paddle1 = math.radians(30.0)


def handle_inputs(previous_mouse_position: Optional[Tuple[float, float]]) -> None:
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera

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
        paddle1.position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position[1] += 1.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position[1] += 1.0

    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1

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


virtual_camera_position = np.array([-1.5, 0.0, 8.5], dtype=np.float32)
virtual_camera_rot_y = math.radians(25.0)
virtual_camera_rot_x = math.radians(15.0)
virtual_camera_relative_offset = np.array([-0.0, 0.0, 0.0], dtype=np.float32)

TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

animation_time = 0.0
animation_time_multiplier = 1.0
animation_paused = False
show_ground_axis = False


def highlighted_button(text: str, start_time: float, time: float) -> bool:
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
    impl.process_inputs()

    imgui.new_frame()

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item("Quit", "Cmd+Q", False, True)

            if clicked_quit:
                exit(0)

            imgui.end_menu()
        imgui.end_main_menu_bar()

    imgui.set_next_window_size(453, 564, imgui.FIRST_USE_EVER)
    imgui.set_next_window_position(15, 30, imgui.FIRST_USE_EVER)
    imgui.set_next_window_bg_alpha(0.05)

    imgui.begin("Options", True)
    show, _ = imgui.collapsing_header("Time")
    if show:
        clicked_animation_paused, animation_paused = imgui.checkbox(
            "Pause", animation_paused
        )
        clicked_camera, camera.r = imgui.slider_float(
            "Camera Radius", camera.r, 10, 1000.0
        )
        (
            clicked_animation_time_multiplier,
            animation_time_multiplier,
        ) = imgui.slider_float("Sim Speed", animation_time_multiplier, -10.0, 10.0)
        if imgui.button("Restart"):
            animation_time = 0.0

        if imgui.tree_node(
            "From World Space, Against Arrows, Read Bottom Up",
            imgui.TREE_NODE_DEFAULT_OPEN,
        ):
            if imgui.tree_node("Paddle 1->World", imgui.TREE_NODE_DEFAULT_OPEN):
                imgui.text("f_paddle1_to_world(x) = ")
                imgui.text(" = (")
                imgui.same_line()
                if highlighted_button(
                    "T",
                    StepNumber.paddle_1_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.paddle_1_translate.value.start_time
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button(
                    "R_z",
                    StepNumber.paddle_1_rotate.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.paddle_1_rotate.value.start_time
                imgui.same_line()
                imgui.text(" ) (x) ")
                if imgui.tree_node("Square->World", imgui.TREE_NODE_DEFAULT_OPEN):
                    imgui.text("f_square_to_world(x) = ")
                    imgui.text(" f_paddle1_to_world o (")
                    imgui.text("      ")
                    imgui.same_line()
                    if highlighted_button(
                        "T_-Z",
                        StepNumber.square_translate_z.value.start_time,
                        animation_time,
                    ):
                        animation_time = StepNumber.square_translate_z.value.start_time
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button(
                        "R_Z",
                        StepNumber.square_rotate_z_first.value.start_time,
                        animation_time,
                    ):
                        animation_time = (
                            StepNumber.square_rotate_z_first.value.start_time
                        )
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button(
                        "T_X",
                        StepNumber.square_translate_x.value.start_time,
                        animation_time,
                    ):
                        animation_time = StepNumber.square_translate_x.value.start_time
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button(
                        "R2_Z",
                        StepNumber.square_rotate_z_second.value.start_time,
                        animation_time,
                    ):
                        animation_time = (
                            StepNumber.square_rotate_z_second.value.start_time
                        )
                    imgui.same_line()
                    imgui.text(" ) (x) ")
                    imgui.tree_pop()
                imgui.tree_pop()
            if imgui.tree_node("Paddle 2->World", imgui.TREE_NODE_DEFAULT_OPEN):
                imgui.text("f_paddle2_to_world(x) = (")
                imgui.same_line()
                if highlighted_button(
                    "T",
                    StepNumber.paddle_2_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.paddle_2_translate.value.start_time
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button(
                    "R",
                    StepNumber.paddle_2_rotate.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.paddle_2_rotate.value.start_time
                imgui.same_line()
                imgui.text(" ) (x) ")
                imgui.tree_pop()
            if imgui.tree_node("Camera->World", imgui.TREE_NODE_DEFAULT_OPEN):
                imgui.text("f_camera_to_world(x) = (")
                imgui.same_line()
                if highlighted_button(
                    "T",
                    StepNumber.camera_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_translate.value.start_time
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button(
                    "R_Y",
                    StepNumber.camera_rotate_y.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_rotate_y.value.start_time
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button(
                    "R_X",
                    StepNumber.camera_rotate_x.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_rotate_x.value.start_time
                imgui.same_line()
                imgui.text(" ) (x) ")
                imgui.tree_pop()
            imgui.tree_pop()
        if imgui.tree_node(
            "Towards NDC, With Arrows, Top Down Reading",
            imgui.TREE_NODE_DEFAULT_OPEN,
        ):
            if imgui.tree_node("World->Camera", imgui.TREE_NODE_DEFAULT_OPEN):
                imgui.text("f_camera_to_world^-1(x) = f_world_to_camera(x) = ")
                imgui.text("   ")
                imgui.same_line()
                if highlighted_button(
                    "R^-1_X",
                    StepNumber.camera_inverse_rotate_x.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_inverse_rotate_x.value.start_time
                imgui.same_line()
                imgui.text(" (")
                imgui.same_line()
                if highlighted_button(
                    "R^-1_Y",
                    StepNumber.camera_inverse_rotate_y.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_inverse_rotate_y.value.start_time
                imgui.same_line()
                imgui.text(" (")
                imgui.same_line()
                if highlighted_button(
                    "T^-1",
                    StepNumber.camera_inverse_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_inverse_translate.value.start_time
                    )
                imgui.same_line()
                imgui.text("* x))")
                imgui.tree_pop()
            if imgui.tree_node(
                "Frustum->Rectangular Prism", imgui.TREE_NODE_DEFAULT_OPEN
            ):
                imgui.text("f_frustum_to_prism(x) = ")
                imgui.same_line()
                if highlighted_button(
                    "Squash Y",
                    StepNumber.camera_frustum_squash_y.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_frustum_squash_y.value.start_time
                imgui.same_line()
                imgui.text(" (")
                imgui.same_line()
                if highlighted_button(
                    "Squash X",
                    StepNumber.camera_frustum_squash_x.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_frustum_squash_x.value.start_time
                imgui.same_line()
                imgui.text(" * x)")
                imgui.tree_pop()
            if imgui.tree_node(
                "Ortho, Rectangular Prism->NDC", imgui.TREE_NODE_DEFAULT_OPEN
            ):
                imgui.text("f_ortho(x) = ")
                imgui.same_line()
                if highlighted_button(
                    "Scale",
                    StepNumber.camera_frustum_scale.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_frustum_scale.value.start_time
                imgui.same_line()
                imgui.text(" (")
                imgui.same_line()
                if highlighted_button(
                    "T - Center",
                    StepNumber.camera_frustum_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_frustum_translate.value.start_time
                    )
                imgui.same_line()
                imgui.text(" * x)")
                imgui.tree_pop()
            imgui.tree_pop()

    show, _ = imgui.collapsing_header("Camera Options")
    if show:
        (
            clicked_virtual_camera_positionx_clicked,
            virtual_camera_position[0],
        ) = imgui.slider_float(
            "Camera X_Worldspace", virtual_camera_position[0], -200, 200.0
        )
        (
            clicked_virtual_camera_positiony_clicked,
            virtual_camera_position[1],
        ) = imgui.slider_float(
            "Camera Y_Worldspace", virtual_camera_position[1], -200, 200.0
        )
        (
            clicked_virtual_camera_positionz_clicked,
            virtual_camera_position[2],
        ) = imgui.slider_float(
            "Camera Z_Worldspace", virtual_camera_position[2], -200, 200.0
        )
        (
            clicked_virtual_camera_positionrotx_clicked,
            virtual_camera_rot_x,
        ) = imgui.slider_float("Camera Rot X", virtual_camera_rot_x, -math.pi, math.pi)
        (
            clicked_virtual_camera_positionroty_clicked,
            virtual_camera_rot_y,
        ) = imgui.slider_float("Camera Rot Y", virtual_camera_rot_y, -math.pi, math.pi)

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

        (
            clicked_virtual_camera_field_of_view,
            frustum.field_of_view,
        ) = imgui.slider_float("Camera FOV", frustum.field_of_view, 5.0, 120.0)

        if clicked_virtual_camera_field_of_view:
            frustum.prepare_to_render()

        (
            clicked_virtual_camera_aspect_ratio,
            frustum.aspect_ratio,
        ) = imgui.slider_float("Camera AspectRatio", frustum.aspect_ratio, 0.1, 3.0)

        if clicked_virtual_camera_aspect_ratio:
            frustum.prepare_to_render()

        (
            clicked_virtual_camera_near_z,
            frustum.near_z,
        ) = imgui.slider_float("Camera near_z", frustum.near_z, -200.0, -1.0)

        if clicked_virtual_camera_near_z:
            frustum.prepare_to_render()

        (
            clicked_virtual_camera_far_z,
            frustum.far_z,
        ) = imgui.slider_float(
            "Camera far_z", frustum.far_z, frustum.near_z, frustum.near_z - 500.0
        )

        if clicked_virtual_camera_far_z:
            frustum.prepare_to_render()

    show, _ = imgui.collapsing_header("Display Options")
    if show:
        clicked_show_ground_axises, show_ground_axis = imgui.checkbox(
            "Show Ground Axises", show_ground_axis
        )

        (
            clicked_line_thickness,
            line_thickness,
        ) = imgui.slider_float("Line Width", line_thickness, 1.0, 10.0)

        if imgui.button("NDC"):
            center_view_on = CenterViewOn.ndc
        imgui.same_line()
        if imgui.button("Paddle 1"):
            center_view_on = CenterViewOn.paddle1
        imgui.same_line()
        if imgui.button("Square"):
            center_view_on = CenterViewOn.square
        imgui.same_line()
        if imgui.button("Paddle 2"):
            center_view_on = CenterViewOn.paddle2
        imgui.same_line()
        if imgui.button("Camera"):
            center_view_on = CenterViewOn.camera

    imgui.end()

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
        field_of_view=45.0,
        aspect_ratio=float(width) / float(height),
        near_z=0.1,
        far_z=10000.0,
    )

    # draw around center of world space, like being centered
    # on a player running around a world in a 3D, 3rd person
    # camera
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -camera.r)
    ms.rotate_x(ms.MatrixStack.view, camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)

    # but if the user selected view paddle 1 or view square, add
    # center on them
    if (
        center_view_on == CenterViewOn.paddle1
        or center_view_on == center_view_on.square
    ):
        # center on square
        if center_view_on == CenterViewOn.square:
            # if i do this rotation, the camera rotates in a weird looking way
            # ms.rotate_z(
            #     ms.MatrixStack.model,
            #     -square_rotation,
            # )
            ms.translate(
                ms.MatrixStack.model,
                -15.0,
                0.0,
                0.0,
            )
            # if i do this rotation, the camera rotates in a weird looking way
            # ms.rotate_z(
            #     ms.MatrixStack.model,
            #     -rotation_around_paddle1,
            # )
            ms.translate(
                ms.MatrixStack.model,
                0.0,
                0.0,
                5.0,
            )

        # center on paddle 1
        # if i do this rotation, the camera rotates in a weird looking way
        # ms.rotate_z(
        #     ms.MatrixStack.model,
        #     -paddle1.rotation,
        # )
        ms.translate(
            ms.MatrixStack.model,
            -paddle1.position[0],
            -paddle1.position[1],
            0.0,
        )

    # center on paddle
    if center_view_on == CenterViewOn.paddle2:
        # if i do this rotation, the camera rotates in a weird looking way
        # ms.rotate_z(
        #     ms.MatrixStack.model,
        #     -paddle2.rotation,
        # )
        ms.translate(
            ms.MatrixStack.model,
            -paddle2.position[0],
            -paddle2.position[1],
            0.0,
        )
    if center_view_on == CenterViewOn.camera:
        if animation_time > (StepNumber.camera_inverse_translate.value.start_time):
            (
                ms.translate(
                    ms.MatrixStack.model,
                    virtual_camera_position[0]
                    * StepNumber.camera_inverse_translate.value.interpolate(
                        animation_time
                    ),
                    virtual_camera_position[1]
                    * StepNumber.camera_inverse_translate.value.interpolate(
                        animation_time
                    ),
                    virtual_camera_position[2]
                    * StepNumber.camera_inverse_translate.value.interpolate(
                        animation_time
                    ),
                )
            )

        if animation_time > (StepNumber.camera_translate.value.start_time):
            if animation_time > (StepNumber.camera_translate.value.start_time):
                (
                    ms.translate(
                        ms.MatrixStack.model,
                        -virtual_camera_position[0]
                        * StepNumber.camera_translate.value.interpolate(animation_time),
                        -virtual_camera_position[1]
                        * StepNumber.camera_translate.value.interpolate(animation_time),
                        -virtual_camera_position[2]
                        * StepNumber.camera_translate.value.interpolate(animation_time),
                    ),
                )

    # draw NDC in global space, so that we can see the camera space
    # go to NDC
    ground.render(animation_time)
    glClear(GL_DEPTH_BUFFER_BIT)
    with ms.PushMatrix(ms.MatrixStack.model):
        cube.render(animation_time)
    glClear(GL_DEPTH_BUFFER_BIT)

    if animation_time > (StepNumber.camera_inverse_rotate_x.value.start_time):
        ms.rotate_x(
            ms.MatrixStack.model,
            -virtual_camera_rot_x
            * StepNumber.camera_inverse_rotate_x.value.interpolate(animation_time),
        )
    if animation_time > (StepNumber.camera_inverse_rotate_y.value.start_time):
        ms.rotate_y(
            ms.MatrixStack.model,
            -virtual_camera_rot_y
            * StepNumber.camera_inverse_rotate_y.value.interpolate(animation_time),
        )
    if animation_time > (StepNumber.camera_inverse_translate.value.start_time):
        ms.translate(
            ms.MatrixStack.model,
            -virtual_camera_position[0]
            * StepNumber.camera_inverse_translate.value.interpolate(animation_time),
            -virtual_camera_position[1]
            * StepNumber.camera_inverse_translate.value.interpolate(animation_time),
            -virtual_camera_position[2]
            * StepNumber.camera_inverse_translate.value.interpolate(animation_time),
        )

    # draw virtual camera
    if animation_time > (StepNumber.camera_translate.value.start_time):
        with ms.push_matrix(ms.MatrixStack.model):
            if animation_time > (StepNumber.camera_translate.value.start_time):
                ms.translate(
                    ms.MatrixStack.model,
                    virtual_camera_position[0]
                    * StepNumber.camera_translate.value.interpolate(animation_time),
                    virtual_camera_position[1]
                    * StepNumber.camera_translate.value.interpolate(animation_time),
                    virtual_camera_position[2]
                    * StepNumber.camera_translate.value.interpolate(animation_time),
                )
            if animation_time > (StepNumber.camera_rotate_y.value.start_time):
                ms.rotate_y(
                    ms.MatrixStack.model,
                    virtual_camera_rot_y
                    * StepNumber.camera_rotate_y.value.interpolate(animation_time),
                )
            if animation_time > (StepNumber.camera_rotate_x.value.start_time):
                ms.rotate_x(
                    ms.MatrixStack.model,
                    virtual_camera_rot_x
                    * StepNumber.camera_rotate_x.value.interpolate(animation_time),
                )

            ground.render(animation_time)
            glClear(GL_DEPTH_BUFFER_BIT)

            if animation_time > (StepNumber.camera_rotate_y.value.start_time):
                frustum.render(animation_time)
            axis.render(animation_time)
            cube.render(animation_time)

    if animation_time < StepNumber.paddle_1_translate.value.start_time:
        axis.render(animation_time)
    else:
        axis.render(animation_time, grayed_out=True)

    with ms.PushMatrix(ms.MatrixStack.model):
        if animation_time > (StepNumber.paddle_1_translate.value.start_time):
            ms.translate(
                ms.MatrixStack.model,
                paddle1.position[0]
                * StepNumber.paddle_1_translate.value.interpolate(animation_time),
                paddle1.position[1]
                * StepNumber.paddle_1_translate.value.interpolate(animation_time),
                0.0,
            )
        if animation_time > (StepNumber.paddle_1_rotate.value.start_time):
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle1.rotation
                * StepNumber.paddle_1_rotate.value.interpolate(animation_time),
            )

        if animation_time > (StepNumber.beginning.value.start_time) and (
            animation_time < StepNumber.square_translate_z.value.start_time
        ):
            axis.render(animation_time)
        if animation_time > (StepNumber.square_translate_z.value.start_time):
            # ascontiguousarray puts the array in column major order
            paddle1.render(animation_time)

        # # draw the square

        if animation_time > (StepNumber.square_translate_z.value.start_time):
            ms.translate(
                ms.MatrixStack.model,
                0.0,
                0.0,
                -5.0 * StepNumber.square_translate_z.value.interpolate(animation_time),
            )
        if animation_time > (StepNumber.square_rotate_z_first.value.start_time):
            ms.rotate_z(
                ms.MatrixStack.model,
                rotation_around_paddle1
                * StepNumber.square_rotate_z_first.value.interpolate(animation_time),
            )
        if animation_time > (StepNumber.square_translate_x.value.start_time):
            ms.translate(
                ms.MatrixStack.model,
                1.5 * StepNumber.square_translate_x.value.interpolate(animation_time),
                0.0,
                0.0,
            )
        if animation_time > (StepNumber.square_rotate_z_second.value.start_time):
            ms.rotate_z(
                ms.MatrixStack.model,
                square_rotation
                * StepNumber.square_rotate_z_second.value.interpolate(animation_time),
            )

        if animation_time > (StepNumber.paddle_1_rotate.value.start_time) and (
            animation_time < StepNumber.paddle_2_translate.value.start_time
        ):
            axis.render(animation_time)

        if animation_time > (StepNumber.paddle_2_translate.value.start_time):
            square.render(animation_time)

    # get back to center of global space

    with ms.PushMatrix(ms.MatrixStack.model):
        # draw paddle 2
        if animation_time > (StepNumber.paddle_2_translate.value.start_time):
            ms.translate(
                ms.MatrixStack.model,
                paddle2.position[0]
                * StepNumber.paddle_2_translate.value.interpolate(animation_time),
                paddle2.position[1]
                * StepNumber.paddle_2_translate.value.interpolate(animation_time),
                0.0,
            )
        if animation_time > (StepNumber.paddle_2_rotate.value.start_time):
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle2.rotation
                * StepNumber.paddle_2_rotate.value.interpolate(animation_time),
            )

        if animation_time > (StepNumber.paddle_2_translate.value.start_time) and (
            animation_time < (StepNumber.camera_pre_placement_pause.value.start_time)
        ):
            axis.render(animation_time)

        if animation_time > (StepNumber.camera_pre_placement_pause.value.start_time):
            paddle2.render(animation_time)

    imgui.render()
    impl.render(imgui.get_draw_data())

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
