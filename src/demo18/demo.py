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
import sys
from dataclasses import dataclass, field
from typing import Callable, List

import glfw
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_GREATER,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    GL_SCISSOR_TEST,
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
    glScissor,
    glVertex3f,
    glViewport,
)

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 18", None, None)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)


# Install a key handler
def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0289, 0.071875, 0.0972, 1.0)


glClearDepth(-1.0)
glDepthFunc(GL_GREATER)
glEnable(GL_DEPTH_TEST)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()


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
class Vertex2D:
    x: float
    y: float

    def __add__(self, rhs: Vertex2D) -> Vertex2D:
        return Vertex2D(x=(self.x + rhs.x), y=(self.y + rhs.y))

    def translate(self: Vertex2D, translate_amount: Vertex2D) -> Vertex2D:
        return self + translate_amount

    def __mul__(self, scalar: float) -> Vertex2D:
        return Vertex2D(x=self.x * scalar, y=self.y * scalar)

    def __rmul__(self, scalar: float) -> Vertex2D:
        return self * scalar

    def uniform_scale(self: Vertex2D, scalar: float) -> Vertex2D:
        return self * scalar

    def scale(self: Vertex2D, scale_x: float, scale_y: float) -> Vertex2D:
        return Vertex2D(x=(self.x * scale_x), y=(self.y * scale_y))

    def __neg__(self):
        return -1.0 * self

    def rotate_90_degrees(self: Vertex2D):
        return Vertex2D(x=-self.y, y=self.x)

    def rotate(self: Vertex2D, angle_in_radians: float) -> Vertex2D:
        return (
            math.cos(angle_in_radians) * self
            + math.sin(angle_in_radians) * self.rotate_90_degrees()
        )


@dataclass
class Vertex:
    x: float
    y: float
    z: float

    def __add__(self, rhs: Vertex) -> Vertex:
        return Vertex(x=(self.x + rhs.x), y=(self.y + rhs.y), z=(self.z + rhs.z))

    def translate(self: Vertex, translate_amount: Vertex) -> Vertex:
        return self + translate_amount

    def rotate_x(self: Vertex, angle_in_radians: float) -> Vertex:
        yz_on_xy: Vertex2D = Vertex2D(x=self.y, y=self.z).rotate(angle_in_radians)
        return Vertex(x=self.x, y=yz_on_xy.x, z=yz_on_xy.y)

    def rotate_y(self: Vertex, angle_in_radians: float) -> Vertex:
        zx_on_xy: Vertex2D = Vertex2D(x=self.z, y=self.x).rotate(angle_in_radians)
        return Vertex(x=zx_on_xy.y, y=self.y, z=zx_on_xy.x)

    def rotate_z(self: Vertex, angle_in_radians: float) -> Vertex:
        xy_on_xy: Vertex2D = Vertex2D(x=self.x, y=self.y).rotate(angle_in_radians)
        return Vertex(x=xy_on_xy.x, y=xy_on_xy.y, z=self.z)

    def __mul__(self, scalar: float) -> Vertex:
        return Vertex(x=(self.x * scalar), y=(self.y * scalar), z=(self.z * scalar))

    def __rmul__(self, scalar: float) -> Vertex:
        return self * scalar

    def uniform_scale(self: Vertex, scalar: float) -> Vertex:
        return self * scalar

    def scale(self: Vertex, scale_x: float, scale_y: float, scale_z: float) -> Vertex:
        return Vertex(x=(self.x * scale_x), y=(self.y * scale_y), z=(self.z * scale_z))

    def __neg__(self):
        return -1.0 * self

    # fmt: off
    def ortho(self: Vertex,
              left: float,
              right: float,
              bottom: float,
              top: float,
              near: float,
              far: float,
              ) -> Vertex:
        midpoint = Vertex(
            x=(left + right) / 2.0,
            y=(bottom + top) / 2.0,
            z=(near + far) / 2.0
        )
        length_x: float
        length_y: float
        length_z: float
        length_x, length_y, length_z = right - left, top - bottom, far - near
        return self.translate(-midpoint) \
                   .scale(2.0 / length_x,
                          2.0 / length_y,
                          2.0 / (-length_z))
    # fmt: on

    # fmt: off
    def perspective(self: Vertex,
                    field_of_view: float,
                    aspect_ratio: float,
                    near_z: float,
                    far_z: float) -> Vertex:
        # field_of_view, field of view, is angle of y
        # aspect_ratio is x_width / y_width

        top: float = -near_z * math.tan(math.radians(field_of_view) / 2.0)
        right: float = top * aspect_ratio

        scaled_x: float = self.x / self.z * near_z
        scaled_y: float = self.y / self.z * near_z
        rectangular_prism: Vertex = Vertex(scaled_x,
                                          scaled_y,
                                          self.z)

        return rectangular_prism.ortho(left=-right,
                                      right=right,
                                      bottom=-top,
                                      top=top,
                                      near=near_z,
                                      far=far_z)

    def cs_to_ndc_space_fn(self: Vertex) -> Vertex:
        return self.perspective(field_of_view=45.0,
                                aspect_ratio=1.0,
                                near_z=-.1,
                                far_z=-1000.0)
    # fmt: on


@dataclass
class Paddle:
    vertices: list[Vertex]
    r: float
    g: float
    b: float
    position: Vertex
    rotation: float = 0.0


paddle1: Paddle = Paddle(
    vertices=[
        Vertex(x=-1.0, y=-3.0, z=0.0),
        Vertex(x=1.0, y=-3.0, z=0.0),
        Vertex(x=1.0, y=3.0, z=0.0),
        Vertex(x=-1.0, y=3.0, z=0.0),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
    position=Vertex(x=-9.0, y=0.0, z=0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vertex(x=-1.0, y=-3.0, z=0.0),
        Vertex(x=1.0, y=-3.0, z=0.0),
        Vertex(x=1.0, y=3.0, z=0.0),
        Vertex(x=-1.0, y=3.0, z=0.0),
    ],
    r=1.0,
    g=1.0,
    b=0.0,
    position=Vertex(x=9.0, y=0.0, z=0.0),
)


number_of_controllers = glfw.joystick_present(glfw.JOYSTICK_1)


@dataclass
class Camera:
    position_ws: Vertex = field(default_factory=lambda: Vertex(x=0.0, y=0.0, z=40.0))
    rot_y: float = 0.0
    rot_x: float = 0.0


camera: Camera = Camera()


square: list[Vertex] = [
    Vertex(x=-0.5, y=-0.5, z=0.0),
    Vertex(x=0.5, y=-0.5, z=0.0),
    Vertex(x=0.5, y=0.5, z=0.0),
    Vertex(x=-0.5, y=0.5, z=0.0),
]
square_rotation: float = 0.0
rotation_around_paddle1: float = 0.0


def handle_inputs() -> None:
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
        camera.position_ws.x -= move_multiple * math.sin(camera.rot_y)
        camera.position_ws.z -= move_multiple * math.cos(camera.rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_ws.x += move_multiple * math.sin(camera.rot_y)
        camera.position_ws.z += move_multiple * math.cos(camera.rot_y)

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position.y -= 1.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position.y += 1.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position.y -= 1.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position.y += 1.0

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1


# doc-region-begin define function stack class
@dataclass
class FunctionStack:
    stack: List[Callable[Vertex, Vertex]] = field(default_factory=lambda: [])

    def push(self, o: object):
        self.stack.append(o)

    def pop(self):
        return self.stack.pop()

    def clear(self):
        self.stack.clear()

    def modelspace_to_ndc(self, vertex: Vertex) -> Vertex:
        v = vertex
        for fn in reversed(self.stack):
            v = fn(v)
        return v


fn_stack = FunctionStack()
# doc-region-end define function stack class


TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()

# doc-region-begin begin event loop
while not glfw.window_should_close(window):
    # doc-region-end begin event loop
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
            camera.position_ws.x += 1.0 * axes_list[0][0] * math.cos(camera.rot_y)
            camera.position_ws.z -= 1.0 * axes_list[0][0] * math.sin(camera.rot_y)
        if math.fabs(float(axes_list[0][1])) > 0.1:
            camera.position_ws.x += 1.0 * axes_list[0][1] * math.sin(camera.rot_y)
            camera.position_ws.z += 1.0 * axes_list[0][1] * math.cos(camera.rot_y)

        # print(axes_list[0][4])
        if math.fabs(axes_list[0][3]) > 0.10:
            camera.rot_x -= 3.0 * axes_list[0][3] * 0.01
        if math.fabs(axes_list[0][2]) > 0.10:
            camera.rot_y -= axes_list[0][2] * 0.01

    # doc-region-begin stack push camera space to ndc
    fn_stack.push(lambda v: v.cs_to_ndc_space_fn())  # (1)
    # doc-region-end stack push camera space to ndc

    # doc-region-begin camera space to world space, commented out
    # fn_stack.push(
    #     lambda v: v.translate(camera.position_ws)
    # fn_stack.push(lambda v: v.rotate_y(camera.rot_y))
    # fn_stack.push(lambda v: v.rotate_x(camera.rot_x))
    # doc-region-end camera space to world space, commented out

    # doc-region-begin world space to camera space
    fn_stack.push(lambda v: v.rotate_x(-camera.rot_x))  # (2)
    fn_stack.push(lambda v: v.rotate_y(-camera.rot_y))  # (3)
    fn_stack.push(lambda v: v.translate(-camera.position_ws))  # (4)
    # doc-region-end world space to camera space

    # doc-region-begin paddle 1 transformations
    fn_stack.push(
        lambda v: v.translate(paddle1.position)
    )  # (5) translate the local origin
    fn_stack.push(
        lambda v: v.rotate_z(paddle1.rotation)
    )  # (6) (rotate around the local z axis
    # doc-region-end paddle 1 transformations

    # doc-region-begin draw paddle 1
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        p1_v_ndc = fn_stack.modelspace_to_ndc(p1_v_ms)
        glVertex3f(
            p1_v_ndc.x,
            p1_v_ndc.y,
            p1_v_ndc.z,
        )
    glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin draw paddle 2
    glColor3f(0.0, 0.0, 1.0)

    fn_stack.push(lambda v: v.translate(Vertex(x=0.0, y=0.0, z=-1.0)))  # (7)
    fn_stack.push(lambda v: v.rotate_z(rotation_around_paddle1))  # (8)
    fn_stack.push(lambda v: v.translate(Vertex(x=2.0, y=0.0, z=0.0)))  # (9)
    fn_stack.push(lambda v: v.rotate_z(square_rotation))  # (10)

    glBegin(GL_QUADS)
    for ms in square:
        ndc = fn_stack.modelspace_to_ndc(ms)
        glVertex3f(ndc.x, ndc.y, ndc.z)
    glEnd()
    # doc-region-end draw paddle 2

    # doc-region-begin pop to get back to world space
    fn_stack.pop()  # pop off (10)
    fn_stack.pop()  # pop off (9)
    fn_stack.pop()  # pop off (8)
    fn_stack.pop()  # pop off (7)
    fn_stack.pop()  # pop off (6)
    fn_stack.pop()  # pop off (5)
    # doc-region-end pop to get back to world space

    # doc-region-begin draw paddle 2
    fn_stack.push(lambda v: v.translate(paddle2.position))  # (5)
    fn_stack.push(lambda v: v.rotate_z(paddle2.rotation))  # (6)

    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        p2_v_ndc: Vertex = fn_stack.modelspace_to_ndc(p2_v_ms)
        glVertex3f(p2_v_ndc.x, p2_v_ndc.y, p2_v_ndc.z)
    glEnd()
    # doc-region-end draw paddle 2

    # doc-region-begin clear function stack for next iteration of the event loop
    fn_stack.clear()  # done rendering everything, just go ahead and clean 1-6 off of the stack
    # doc-region-end clear function stack for next iteration of the event loop

    # doc-region-begin flush framebuffer
    glfw.swap_buffers(window)
    # doc-region-end flush framebuffer

fn_stack = FunctionStack()


# doc-region-begin function stack examples definitions
def identity(x):
    return x


def add_one(x):
    return x + 1


def multiply_by_2(x):
    return x * 2


def add_5(x):
    return x + 5


# doc-region-end function stack examples definitions

# never pop this off, otherwise can't apply the stack
# doc-region-begin push identity
fn_stack.push(identity)
print(fn_stack)
print(fn_stack.modelspace_to_ndc(1))  # x = 1
# doc-region-end push identity

# doc-region-begin push add one
fn_stack.push(add_one)
print(fn_stack)
print(fn_stack.modelspace_to_ndc(1))  # x + 1 = 2
# doc-region-end push add one

# doc-region-begin push multiply by two
fn_stack.push(multiply_by_2)  # (x * 2) + 1 = 3
print(fn_stack)
print(fn_stack.modelspace_to_ndc(1))
# doc-region-end push multiply by two

# doc-region-begin push add 5
fn_stack.push(add_5)  # ((x + 5) * 2) + 1 = 13
print(fn_stack)
print(fn_stack.modelspace_to_ndc(1))
# doc-region-end push add 5

# doc-region-begin first pop
fn_stack.pop()
print(fn_stack)
print(fn_stack.modelspace_to_ndc(1))  # (x * 2) + 1 = 3
# doc-region-end first pop

# doc-region-begin second pop
fn_stack.pop()
print(fn_stack)
print(fn_stack.modelspace_to_ndc(1))  # x + 1 = 2
# doc-region-end second pop

# doc-region-begin third pop
fn_stack.pop()
print(fn_stack)
print(fn_stack.modelspace_to_ndc(1))  # x = 1
# doc-region-end third pop

glfw.terminate()
