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

import math
import sys
from dataclasses import dataclass, field

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

window = glfw.create_window(500, 500, "ModelViewProjection Demo 17", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


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

    width, height = glfw.get_framebuffer_size(window)
    min = width if width < height else height

    glEnable(GL_SCISSOR_TEST)
    glScissor(
        int((width - min) / 2.0),
        int((height - min) / 2.0),
        min,
        min,
    )

    glClearColor(0.0289, 0.071875, 0.0972, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    glViewport(
        int(0.0 + (width - min) / 2.0),
        int(0.0 + (height - min) / 2.0),
        min,
        min,
    )


@dataclass
class Vertex2D:
    x: float
    y: float

    def __add__(self, rhs: Vertex2D) -> Vertex2D:
        return Vertex2D(x=self.x + rhs.x, y=self.y + rhs.y)

    def translate(self: Vertex2D, translate_amount: Vertex2D) -> Vertex2D:
        return self + translate_amount

    def __mul__(self, scalar: float) -> Vertex2D:
        return Vertex2D(x=self.x * scalar, y=self.y * scalar)

    def __rmul__(self, scalar: float) -> Vertex2D:
        return self * scalar

    def uniform_scale(self: Vertex2D, scalar: float) -> Vertex2D:
        return self * scalar

    def scale(self: Vertex2D, scale_x: float, scale_y: float) -> Vertex2D:
        return Vertex2D(x=self.x * scale_x, y=self.y * scale_y)

    def __neg__(self):
        return -1.0 * self

    def rotate_90_degrees(self: Vertex2D):
        return Vertex2D(x=-self.y, y=self.x)

    def rotate(self: Vertex2D, angle_in_radians: float) -> Vertex2D:
        return (
            math.cos(angle_in_radians) * self
            + math.sin(angle_in_radians) * self.rotate_90_degrees()
        )


# doc-region-begin define vertex class
@dataclass
class Vertex:
    # doc-region-end define vertex class
    x: float
    y: float
    z: float

    def __add__(self, rhs: Vertex) -> Vertex:
        return Vertex(x=self.x + rhs.x, y=self.y + rhs.y, z=self.z + rhs.z)

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
        return Vertex(x=self.x * scalar, y=self.y * scalar, z=self.z * scalar)

    def __rmul__(self, scalar: float) -> Vertex:
        return self * scalar

    def uniform_scale(self: Vertex, scalar: float) -> Vertex:
        return self * scalar

    def scale(self: Vertex, scale_x: float, scale_y: float, scale_z: float) -> Vertex:
        return Vertex(x=self.x * scale_x, y=self.y * scale_y, z=self.z * scale_z)

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
    # doc-region-begin define perspective
    def perspective(self: Vertex,
                    fov: float,
                    aspectRatio: float,
                    nearZ: float,
                    farZ: float) -> Vertex:
        # fov, field of view, is angle of y
        # aspectRatio is xwidth / ywidth

        top: float = -nearZ * math.tan(math.radians(fov) / 2.0)
        right: float = top * aspectRatio

        scaled_x: float = self.x / self.z * nearZ
        scaled_y: float = self.y / self.z * nearZ
        retangular_prism: Vertex = Vertex(scaled_x,
                                          scaled_y,
                                          self.z)

        return retangular_prism.ortho(left=-right,
                                      right=right,
                                      bottom=-top,
                                      top=top,
                                      near=nearZ,
                                      far=farZ)

    def camera_space_to_ndc_space_fn(self: Vertex) -> Vertex:
        return self.perspective(fov=45.0,
                                aspectRatio=1.0,
                                nearZ=-.1,
                                farZ=-1000.0)
    # doc-region-end define perspective
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
    position_worldspace: Vertex = field(
        default_factory=lambda: Vertex(x=0.0, y=0.0, z=40.0)
    )
    rot_y: float = 0.0
    rot_x: float = 0.0


camera: Camera = Camera()


square: Paddle = [
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

    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera.rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera.rot_x -= 0.03
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        forwards_camera_space = Vertex(x=0.0, y=0.0, z=-1.0)
        forward_world_space = forwards_camera_space.rotate_y(camera.rot_y) \
                                                   .translate(
                                                       camera.position_worldspace
                                                   )
        camera.position_worldspace.x = forward_world_space.x
        camera.position_worldspace.y = forward_world_space.y
        camera.position_worldspace.z = forward_world_space.z
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        forwards_camera_space = Vertex(x=0.0, y=0.0, z=1.0)
        forward_world_space = forwards_camera_space.rotate_y(camera.rot_y) \
                                                   .translate(
                                                       camera.position_worldspace
                                                   )
        camera.position_worldspace.x = forward_world_space.x
        camera.position_worldspace.y = forward_world_space.y
        camera.position_worldspace.z = forward_world_space.z

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position.y -= 1.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position.y += 1.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position.y -= 1.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position.y += 1.0

    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1


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
            camera.position_worldspace.x += (
                1.0 * axes_list[0][0] * math.cos(camera.rot_y)
            )
            camera.position_worldspace.z -= (
                1.0 * axes_list[0][0] * math.sin(camera.rot_y)
            )
        if math.fabs(float(axes_list[0][1])) > 0.1:
            camera.position_worldspace.x += (
                1.0 * axes_list[0][1] * math.sin(camera.rot_y)
            )
            camera.position_worldspace.z += (
                1.0 * axes_list[0][1] * math.cos(camera.rot_y)
            )

        # print(axes_list[0][4])
        if math.fabs(axes_list[0][3]) > 0.10:
            camera.rot_x -= 3.0 * axes_list[0][3] * 0.01
        if math.fabs(axes_list[0][2]) > 0.10:
            camera.rot_y -= axes_list[0][2] * 0.01

    # fmt: off
    # doc-region-begin draw paddle 1
    # draw paddle 1
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for paddle1_vertex_in_model_space in paddle1.vertices:
        paddle1_vertex_in_world_space: Vertex = paddle1_vertex_in_model_space.rotate_z(paddle1.rotation) \
                                         .translate(paddle1.position)
        # paddle1_vertex_in_world_space: Vertex = paddle1_vertex_in_camera_space.rotate_x(camera.rot_x) \
        #                                   .rotate_y(camera.rot_y) \
        #                                   .translate(camera.position_worldspace)
        paddle1_vertex_in_camera_space: Vertex = paddle1_vertex_in_world_space.translate(-camera.position_worldspace) \
                                                                              .rotate_y(-camera.rot_y) \
                                                                              .rotate_x(-camera.rot_x)
        paddle1_vertex_in_ndc_space: Vertex = paddle1_vertex_in_camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(paddle1_vertex_in_ndc_space.x, paddle1_vertex_in_ndc_space.y, paddle1_vertex_in_ndc_space.z)
    glEnd()
    # doc-region-end draw paddle 1
    # fmt: off


    # fmt: off
    # draw square
    # doc-region-begin draw square
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_QUADS)
    for model_space in square:
        paddle_1_space: Vertex = model_space.rotate_z(square_rotation) \
                                            .translate(Vertex(x=2.0,
                                                              y=0.0,
                                                              z=0.0)) \
                                            .rotate_z(rotation_around_paddle1) \
                                            .translate(Vertex(x=0.0,
                                                              y=0.0,
                                                              z=-1.0))
        world_space: Vertex =paddle_1_space.rotate_z(paddle1.rotation) \
                                           .translate(paddle1.position)
        camera_space: Vertex = world_space.translate(-camera.position_worldspace) \
                                          .rotate_y(-camera.rot_y) \
                                          .rotate_x(-camera.rot_x)
        ndc_space: Vertex = camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end draw square
    # fmt: on

    # fmt: off
    # draw paddle 2
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        world_space: Vertex = model_space.rotate_z(paddle2.rotation) \
                                         .translate(paddle2.position)
        camera_space: Vertex = world_space.translate(-camera.position_worldspace) \
                                          .rotate_y(-camera.rot_y) \
                                          .rotate_x(-camera.rot_x)
        ndc_space: Vertex = camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()

    glfw.swap_buffers(window)

glfw.terminate()
