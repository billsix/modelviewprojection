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
import math
from OpenGL.GL import (
    glMatrixMode,
    glLoadIdentity,
    GL_PROJECTION,
    GL_MODELVIEW,
    glClear,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    glViewport,
    glClearColor,
    glColor3f,
    glBegin,
    GL_QUADS,
    glEnd,
    glEnable,
    GL_SCISSOR_TEST,
    glScissor,
    glDisable,
    glVertex3f,
    glClearDepth,
    glDepthFunc,
    GL_GREATER,
    GL_DEPTH_TEST,
)
import glfw

from dataclasses import dataclass, field


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

glClearColor(0.0, 0.0, 0.0, 1.0)


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

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    glViewport(
        int(0.0 + (width - min) / 2.0),
        int(0.0 + (height - min) / 2.0),
        min,
        min,
    )


# doc-region-begin 24b2f9fc341605b61f191425ea7a8e7a2ac42873
@dataclass
class Vertex:
    # doc-region-end 24b2f9fc341605b61f191425ea7a8e7a2ac42873
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

    def ortho(
        self: Vertex,
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
        return self.translate(tx=-midpoint_x, ty=-midpoint_y, tz=-midpoint_z).scale(
            2.0 / length_x, 2.0 / length_y, 2.0 / (-length_z)
        )

    # fmt: off
    # doc-region-begin 7f3ac095c4dfe0c0162e607a871f4e12e6fd633c
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
                                nearZ=-0.1,
                                farZ=-10000.0)
    # doc-region-end 7f3ac095c4dfe0c0162e607a871f4e12e6fd633c
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


number_of_controllers = glfw.joystick_present(glfw.JOYSTICK_1)

def _default_camera_position() -> Vertex:
    return Vertex(x=0.0, y=0.0, z=400.0)

@dataclass
class Camera:
    position_worldspace: Vertex = field(default_factory=_default_camera_position)
    rot_y: float = 0.0
    rot_x: float = 0.0

camera: Camera = Camera()


square: Paddle = [
    Vertex(x=-5.0, y=-5.0, z=0.0),
    Vertex(x=5.0, y=-5.0, z=0.0),
    Vertex(x=5.0, y=5.0, z=0.0),
    Vertex(x=-5.0, y=5.0, z=0.0),
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

    move_multiple = 15.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera.rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera.rot_x -= 0.03
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        forwards_camera_space = Vertex(x=0.0, y=0.0, z=-3.0)
        forward_world_space = forwards_camera_space.rotate_y(camera.rot_y).translate(
            tx=camera.position_worldspace.x,
            ty=camera.position_worldspace.y,
            tz=camera.position_worldspace.z,
        )
        camera.position_worldspace.x = forward_world_space.x
        camera.position_worldspace.y = forward_world_space.y
        camera.position_worldspace.z = forward_world_space.z
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        forwards_camera_space = Vertex(x=0.0, y=0.0, z=3.0)
        forward_world_space = forwards_camera_space.rotate_y(camera.rot_y).translate(
            tx=camera.position_worldspace.x,
            ty=camera.position_worldspace.y,
            tz=camera.position_worldspace.z,
        )
        camera.position_worldspace.x = forward_world_space.x
        camera.position_worldspace.y = forward_world_space.y
        camera.position_worldspace.z = forward_world_space.z

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

# doc-region-begin 67ffd7b7adc42d01ca93bacdef858c0d4b678e38
while not glfw.window_should_close(window):
    # doc-region-end 67ffd7b7adc42d01ca93bacdef858c0d4b678e38
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
        if math.fabs(float(axes_list[0][0])) > 0.19:
            camera.position_worldspace.x += (
                10.0 * axes_list[0][0] * math.cos(camera.rot_y)
            )
            camera.position_worldspace.z -= (
                10.0 * axes_list[0][0] * math.sin(camera.rot_y)
            )
        if math.fabs(float(axes_list[0][1])) > 0.19:
            camera.position_worldspace.x += (
                10.0 * axes_list[0][1] * math.sin(camera.rot_y)
            )
            camera.position_worldspace.z += (
                10.0 * axes_list[0][1] * math.cos(camera.rot_y)
            )

        if math.fabs(axes_list[0][3]) > 0.19:
            camera.rot_y -= 3.0 * axes_list[0][3] * 0.01
        if math.fabs(axes_list[0][4]) > 0.19:
            camera.rot_x += axes_list[0][4] * 0.01

    # fmt: off
    # doc-region-begin 2ced82a1c3de464adbfe5d303faffdd2314c17c2
    # draw paddle 1
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
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
                                                     tz=-camera.position_worldspace.z) \
                                          .rotate_y(-camera.rot_y) \
                                          .rotate_x(-camera.rot_x)
        ndc_space: Vertex = camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end 2ced82a1c3de464adbfe5d303faffdd2314c17c2
    # fmt: off


    # fmt: off
    # draw square
    # doc-region-begin 23cd906b0bec259766279f1a9277922719cf1e2b
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_QUADS)
    for model_space in square:
        paddle_1_space: Vertex = model_space.rotate_z(square_rotation) \
                                            .translate(tx=20.0,
                                                       ty=0.0,
                                                       tz=0.0) \
                                            .rotate_z(rotation_around_paddle1) \
                                            .translate(tx=0.0,
                                                       ty=0.0,
                                                       tz=-10.0)
        world_space: Vertex =paddle_1_space.rotate_z(paddle1.rotation).translate(tx=paddle1.position.x,
                                                                                 ty=paddle1.position.y,
                                                                                 tz=0.0)
        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y,
                                                     tz=-camera.position_worldspace.z) \
                                          .rotate_y(-camera.rot_y) \
                                          .rotate_x(-camera.rot_x)
        ndc_space: Vertex = camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end 23cd906b0bec259766279f1a9277922719cf1e2b
    #fmt: on

    #fmt: off
    # draw paddle 2
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        world_space: Vertex = model_space.rotate_z(paddle2.rotation) \
                                         .translate(tx=paddle2.position.x,
                                                    ty=paddle2.position.y,
                                                    tz=0.0)
        camera_space: Vertex = world_space.translate(tx=-camera.position_worldspace.x,
                                                     ty=-camera.position_worldspace.y,
                                                     tz=-camera.position_worldspace.z) \
                                          .rotate_y(-camera.rot_y) \
                                          .rotate_x(-camera.rot_x)
        ndc_space: Vertex = camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    #fmt: off

    glfw.swap_buffers(window)

glfw.terminate()
