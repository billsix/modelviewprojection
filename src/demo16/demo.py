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

window = glfw.create_window(500, 500, "ModelViewProjection Demo 16", None, None)
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
class Vertex:
    x: float
    y: float
    z: float

    def translate(self: Vertex, tx: float, ty: float, tz: float) -> Vertex:
        return Vertex(x=self.x + tx, y=self.y + ty, z=self.z + tz)

    def rotate_x(self: Vertex, angle_in_radians: float) -> Vertex:
        return Vertex(
            x=self.x,
            y=self.y * math.cos(angle_in_radians) - self.z * math.sin(angle_in_radians),
            z=self.y * math.sin(angle_in_radians) + self.z * math.cos(angle_in_radians),
        )

    def rotate_y(self: Vertex, angle_in_radians: float) -> Vertex:
        return Vertex(
            x=self.z * math.sin(angle_in_radians) + self.x * math.cos(angle_in_radians),
            y=self.y,
            z=self.z * math.cos(angle_in_radians) - self.x * math.sin(angle_in_radians),
        )

    def rotate_z(self: Vertex, angle_in_radians: float) -> Vertex:
        return Vertex(
            x=self.x * math.cos(angle_in_radians) - self.y * math.sin(angle_in_radians),
            y=self.x * math.sin(angle_in_radians) + self.y * math.cos(angle_in_radians),
            z=self.z,
        )

    def scale(self: Vertex, scale_x: float, scale_y: float, scale_z: float) -> Vertex:
        return Vertex(x=self.x * scale_x, y=self.y * scale_y, z=self.z * scale_z)

    # fmt: off
    # doc-region-begin f772cea61c9d02b6a9d8565f5427658c0e40cef3
    def ortho(self: Vertex,
              left: float,
              right: float,
              bottom: float,
              top: float,
              near: float,
              far: float,
              ) -> Vertex:
        midpoint_x, midpoint_y, midpoint_z = (
            (left + right) / 2.0,
            (bottom + top) / 2.0,
            (near + far) / 2.0,
        )
        length_x: float
        length_y: float
        length_z: float
        length_x, length_y, length_z = right - left, top - bottom, far - near
        return self.translate(tx=-midpoint_x,
                              ty=-midpoint_y,
                              tz=-midpoint_z) \
                   .scale(2.0 / length_x,
                          2.0 / length_y,
                          2.0 / (-length_z))
    # doc-region-end f772cea61c9d02b6a9d8565f5427658c0e40cef3
    # fmt: on

    # fmt: off
    # doc-region-begin b23c753f650185c5b1e4a0e6c8008852afae73d9
    def camera_space_to_ndc_space_fn(self: Vertex) -> Vertex:
        return self.ortho(left=-100.0,
                          right=100.0,
                          bottom=-100.0,
                          top=100.0,
                          near=-1.0,
                          far=-100.0)
    # doc-region-end b23c753f650185c5b1e4a0e6c8008852afae73d9
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
        Vertex(x=-10.0, y=-30.0, z=0.0),
        Vertex(x=10.0, y=-30.0, z=0.0),
        Vertex(x=10.0, y=30.0, z=0.0),
        Vertex(x=-10.0, y=30.0, z=0.0),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
    position=Vertex(x=-90.0, y=0.0, z=0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vertex(x=-10.0, y=-30.0, z=0.0),
        Vertex(x=10.0, y=-30.0, z=0.0),
        Vertex(x=10.0, y=30.0, z=0.0),
        Vertex(x=-10.0, y=30.0, z=0.0),
    ],
    r=1.0,
    g=0.0,
    b=0.0,
    position=Vertex(x=90.0, y=0.0, z=0.0),
)


# doc-region-begin ec5a4d2515c361a5f311d93c93b2c89b60eb2dfc


@dataclass
class Camera:
    position_worldspace: Vertex = field(
        default_factory=lambda: Vertex(x=0.0, y=0.0, z=50.0)
    )
    rot_y: float = 0.0
    rot_x: float = 0.0
    # doc-region-end ec5a4d2515c361a5f311d93c93b2c89b60eb2dfc


camera: Camera = Camera()


square: Paddle = [
    Vertex(x=-5.0, y=-5.0, z=0.0),
    Vertex(x=5.0, y=-5.0, z=0.0),
    Vertex(x=5.0, y=5.0, z=0.0),
    Vertex(x=-5.0, y=5.0, z=0.0),
]
square_rotation: float = 0.0
rotation_around_paddle1: float = 0.0


# doc-region-begin af7c283e5f33d95279c0b6223af95e9b16826acc
def handle_inputs() -> None:
    # doc-region-end af7c283e5f33d95279c0b6223af95e9b16826acc
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera

    # doc-region-begin 33b92ff8834a0e251991d9373983c374449eab36
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera.rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera.rot_x -= 0.03
    # doc-region-end 33b92ff8834a0e251991d9373983c374449eab36
    # fmt: off
    # doc-region-begin 809cd77769244adb1e3866899e53ba3c203a535a
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        forwards_camera_space = Vertex(x=0.0, y=0.0, z=-1.0)
        forward_world_space = forwards_camera_space.rotate_y(camera.rot_y) \
                                                   .translate(tx=camera.position_worldspace.x,
                                                              ty=camera.position_worldspace.y,
                                                              tz=camera.position_worldspace.z)
        camera.position_worldspace.x = forward_world_space.x
        camera.position_worldspace.y = forward_world_space.y
        camera.position_worldspace.z = forward_world_space.z
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        forwards_camera_space = Vertex(x=0.0, y=0.0, z=1.0)
        forward_world_space = forwards_camera_space.rotate_y(camera.rot_y) \
                                                   .translate(tx=camera.position_worldspace.x,
                                                              ty=camera.position_worldspace.y,
                                                              tz=camera.position_worldspace.z)
        camera.position_worldspace.x = forward_world_space.x
        camera.position_worldspace.y = forward_world_space.y
        camera.position_worldspace.z = forward_world_space.z
    # doc-region-end 809cd77769244adb1e3866899e53ba3c203a535a
    # fmt: on

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position.y -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position.y += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position.y -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position.y += 10.0

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

# doc-region-begin ee882a76ee2962c327841e2a952998acce07cc2a
while not glfw.window_should_close(window):
    # doc-region-end ee882a76ee2962c327841e2a952998acce07cc2a
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

    # fmt: off
    # doc-region-begin 751192ea5ea95537db3cc34c4c3b1549d1fd91e4
    glColor3f(paddle1.r, paddle1.g, paddle1.b)
    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        world_space: Vertex = model_space.rotate_z(paddle1.rotation) \
                                         .translate(tx=paddle1.position.x,
                                                    ty=paddle1.position.y,
                                                    tz=0.0)
        # doc-region-begin d194601529be6fa90270809dd56628cb47360ff2
        # world_space: Vertex = camera_space.rotate_x(camera.rot_x) \
        #                                   .rotate_y(camera.rot_y) \
        #                                   .translate(tx=camera.position_worldspace.x,
        #                                              ty=camera.position_worldspace.y,
        #                                              tz=camera.position_worldspace.z)
        # doc-region-end d194601529be6fa90270809dd56628cb47360ff2
        # doc-region-begin 21b5929d16e434165544480ad25b7ff015e239f7
        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y,
                                                     tz=-camera.position_worldspace.z) \
                                          .rotate_y(-camera.rot_y) \
                                          .rotate_x(-camera.rot_x)
        # doc-region-end 21b5929d16e434165544480ad25b7ff015e239f7
        ndc_space: Vertex = camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end 751192ea5ea95537db3cc34c4c3b1549d1fd91e4
    # fmt: on

    # fmt: off
    # doc-region-begin 554eda2bd3b5edf8eee0c1441a1e8c8f366c575b
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_QUADS)
    for model_space in square:
        paddle_1_space: Vertex = model_space.rotate_z(square_rotation) \
                                            .translate(tx=20.0,
                                                       ty=0.0,
                                                       tz=0.0) \
                                            .rotate_z(rotation_around_paddle1) \
                                            .translate(tx=0.0, ty=0.0, tz=-10.0)

        world_space: Vertex = model_space.rotate_z(paddle1.rotation) \
                                         .translate(tx=paddle1.position.x,
                                                    ty=paddle1.position.y,
                                                    tz=0.0)
        # world_space: Vertex = camera_space.rotate_x(camera.rot_x) \
        #                                   .rotate_y(camera.rot_y) \
        #                                   .translate(tx=camera.position_worldspace.x,
        #                                              ty=camera.position_worldspace.y,
        #                                              tz=camera.position_worldspace.z)

        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y,
                                                     tz=-camera.position_worldspace.z,
                                                     ) \
                                          .rotate_y(-camera.rot_y) \
                                          .rotate_x(-camera.rot_x)
        ndc_space: Vertex = camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end 554eda2bd3b5edf8eee0c1441a1e8c8f366c575b
    # fmt: on

    # fmt: off
    # doc-region-begin ed9eeae978339791ef50c475f26ec4fe8bf018c7
    glColor3f(paddle2.r, paddle2.g, paddle2.b)
    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        world_space: Vertex = model_space.rotate_z(paddle2.rotation) \
                                         .translate(tx=paddle2.position.x,
                                                    ty=paddle2.position.y,
                                                    tz=0.0)
        # world_space: Vertex = camera_space.rotate_x(camera.rot_x) \
        #                                   .rotate_y(camera.rot_y) \
        #                                   .translate(tx=camera.position_worldspace.x,
        #                                              ty=camera.position_worldspace.y,
        #                                              tz=camera.position_worldspace.z)

        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y,
                                                     tz=-camera.position_worldspace.z) \
                                          .rotate_y(-camera.rot_y) \
                                          .rotate_x(-camera.rot_x)

        ndc_space: Vertex = camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end ed9eeae978339791ef50c475f26ec4fe8bf018c7
    # fmt: on
    glfw.swap_buffers(window)

glfw.terminate()
