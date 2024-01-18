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

window = glfw.create_window(500, 500, "ModelViewProjection Demo 18", None, None)
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

    def perspective(
        self: Vertex, fov: float, aspectRatio: float, nearZ: float, farZ: float
    ) -> Vertex:
        top: float = -nearZ * math.tan(math.radians(fov) / 2.0)
        right: float = top * aspectRatio

        scaled_x: float = self.x * nearZ / self.z
        scaled_y: float = self.y * nearZ / self.z
        projected: Vertex = Vertex(scaled_x, scaled_y, self.z)
        return projected.ortho(
            left=-right, right=right, bottom=-top, top=top, near=nearZ, far=farZ
        )

    def camera_space_to_ndc_space_fn(self: Vertex) -> Vertex:
        return self.perspective(
            fov=45.0,
            aspectRatio=1.0,
            nearZ=-0.1,
            farZ=-10000.0,
        )


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
        camera.position_worldspace.x -= move_multiple * math.sin(camera.rot_y)
        camera.position_worldspace.z -= move_multiple * math.cos(camera.rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_worldspace.x += move_multiple * math.sin(camera.rot_y)
        camera.position_worldspace.z += move_multiple * math.cos(camera.rot_y)

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


# doc-region-begin 17f3fd5d2ee2d55faeeff6e71eeb4dbe288c7842
fn_stack: List[Callable[Vertex, Vertex]] = []
# doc-region-end 17f3fd5d2ee2d55faeeff6e71eeb4dbe288c7842


# doc-region-begin b10a3979fe71e9a6afb18fa102ceb44ab253abc6
def apply_stack(vertex: Vertex) -> Vertex:
    v = vertex
    for fn in reversed(fn_stack):
        v = fn(v)
    return v


# doc-region-end b10a3979fe71e9a6afb18fa102ceb44ab253abc6

TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()

# doc-region-begin 6d86d07154c99ed6e1c3feab73545d184153f9ae
while not glfw.window_should_close(window):
    # doc-region-end 6d86d07154c99ed6e1c3feab73545d184153f9ae
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
                10.0 * axes_list[0][0] * math.cos(camera.rot_y)
            )
            camera.position_worldspace.z -= (
                10.0 * axes_list[0][0] * math.sin(camera.rot_y)
            )
        if math.fabs(float(axes_list[0][1])) > 0.1:
            camera.position_worldspace.x += (
                10.0 * axes_list[0][1] * math.sin(camera.rot_y)
            )
            camera.position_worldspace.z += (
                10.0 * axes_list[0][1] * math.cos(camera.rot_y)
            )

        #print(axes_list[0][4])
        if math.fabs(axes_list[0][3]) > 0.10:
            camera.rot_x -= 3.0 * axes_list[0][3] * 0.01
        if math.fabs(axes_list[0][2]) > 0.10:
            camera.rot_y -= axes_list[0][2] * 0.01

    # doc-region-begin 48bd13153ce54db3f6b9ea5833e91820b7d8b020
    fn_stack.append(lambda v: v.camera_space_to_ndc_space_fn())  # (1)
    # doc-region-end 48bd13153ce54db3f6b9ea5833e91820b7d8b020

    # doc-region-begin f217e71c7f5a228622d5db86e6fe0dec1e072dca
    # fn_stack.append(
    #     lambda v: v.translate(tx=camera.position_worldspace.x,
    #                           ty=camera.position_worldspace.y,
    #                           tz=camera.position_worldspace.z)
    # )
    # fn_stack.append(lambda v: v.rotate_y(camera.rot_y))
    # fn_stack.append(lambda v: v.rotate_x(camera.rot_x))
    # doc-region-end f217e71c7f5a228622d5db86e6fe0dec1e072dca

    # fmt: off
    # doc-region-begin c0dcf40149c0b85d84f13b4421a114409a274432
    fn_stack.append(lambda v: v.rotate_x(-camera.rot_x))  # (2)
    fn_stack.append(lambda v: v.rotate_y(-camera.rot_y))  # (3)
    fn_stack.append(lambda v: v.translate(tx=-camera.position_worldspace.x,
                                          ty=-camera.position_worldspace.y,
                                          tz=-camera.position_worldspace.z))  # (4)
    # doc-region-end c0dcf40149c0b85d84f13b4421a114409a274432
    # fmt: on

    # fmt: off
    # doc-region-begin 7de7248650b2809520898faed65be4050d2b441a
    fn_stack.append(lambda v: v.translate(tx=paddle1.position.x,
                                          ty=paddle1.position.y,
                                          tz=0.0)) # (5) translate the local origin
    fn_stack.append(lambda v: v.rotate_z(paddle1.rotation)) # (6) (rotate around the local z axis
    # doc-region-end 7de7248650b2809520898faed65be4050d2b441a
    # fmt: on

    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        ndc_space = apply_stack(model_space)
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()

    # doc-region-begin 87d309a76468a5dd49f5805f739932d7a1b4dac1
    glColor3f(0.0, 0.0, 1.0)

    fn_stack.append(lambda v: v.translate(tx=0.0, ty=0.0, tz=-10.0))  # (7)
    fn_stack.append(lambda v: v.rotate_z(rotation_around_paddle1))  # (8)
    fn_stack.append(lambda v: v.translate(tx=20.0, ty=0.0, tz=0.0))  # (9)
    fn_stack.append(lambda v: v.rotate_z(square_rotation))  # (10)

    glBegin(GL_QUADS)
    for model_space in square:
        ndc_space = apply_stack(model_space)
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end 87d309a76468a5dd49f5805f739932d7a1b4dac1

    # doc-region-begin 6e83cdfe078bb103bf04c3d53a4c4ec7cb22ef60
    fn_stack.pop()  # pop off (10)
    fn_stack.pop()  # pop off (9)
    fn_stack.pop()  # pop off (8)
    fn_stack.pop()  # pop off (7)
    fn_stack.pop()  # pop off (6)
    fn_stack.pop()  # pop off (5)
    # doc-region-end 6e83cdfe078bb103bf04c3d53a4c4ec7cb22ef60

    # fmt: off
    # doc-region-begin 9206a08662c91ad536b41641910f7e8e951f7c9e
    fn_stack.append(lambda v: v.translate(tx=paddle2.position.x,
                                          ty=paddle2.position.y,
                                          tz=0.0))  # (5)
    fn_stack.append(lambda v: v.rotate_z(paddle2.rotation))  # (6)

    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        ndc_space: Vertex = apply_stack(model_space)
        glVertex3f(ndc_space.x, ndc_space.y, ndc_space.z)
    glEnd()
    # doc-region-end 9206a08662c91ad536b41641910f7e8e951f7c9e
    # fmt: on

    # doc-region-begin 4d0f02db53413ede074a8693bb19e68292db3bd4
    fn_stack.clear()  # done rendering everything, just go ahead and clean 1-6 off of the stack
    # doc-region-end 4d0f02db53413ede074a8693bb19e68292db3bd4

    # doc-region-begin 64809e2fccc9daa3f97239991d905b7fc3f03d62
    glfw.swap_buffers(window)
    # doc-region-end 64809e2fccc9daa3f97239991d905b7fc3f03d62

fn_stack = []


# doc-region-begin 1b3386db3fb40d61e80828a90a820b3a235ca940
def identity(x):
    return x


def add_one(x):
    return x + 1


def multiply_by_2(x):
    return x * 2


def add_5(x):
    return x + 5


# doc-region-end 1b3386db3fb40d61e80828a90a820b3a235ca940

# never pop this off, otherwise can't apply the stack
# doc-region-begin 6e7a7ee4a8493ddc6478bcaf2dbb6fb4a2a9753a
fn_stack.append(identity)
print(fn_stack)
print(apply_stack(1))  # x = 1
# doc-region-end 6e7a7ee4a8493ddc6478bcaf2dbb6fb4a2a9753a

# doc-region-begin ccac3b1b9bc8c759e45929c467274c763f7671c7
fn_stack.append(add_one)
print(fn_stack)
print(apply_stack(1))  # x + 1 = 2
# doc-region-end ccac3b1b9bc8c759e45929c467274c763f7671c7

# doc-region-begin 24f3367f7ffaefa3d882a20f772ce7f089049391
fn_stack.append(multiply_by_2)  # (x * 2) + 1 = 3
print(fn_stack)
print(apply_stack(1))
# doc-region-end 24f3367f7ffaefa3d882a20f772ce7f089049391

# doc-region-begin b2d4aee29938ffba8e023e2d523e5a8b7b400bee
fn_stack.append(add_5)  # ((x + 5) * 2) + 1 = 13
print(fn_stack)
print(apply_stack(1))
# doc-region-end b2d4aee29938ffba8e023e2d523e5a8b7b400bee

# doc-region-begin 95d6bcea04206261224089df1734055b9b4196d3
fn_stack.pop()
print(fn_stack)
print(apply_stack(1))  # (x * 2) + 1 = 3
# doc-region-end 95d6bcea04206261224089df1734055b9b4196d3

# doc-region-begin 55dd21f698dbbde5bd5d1b332279d099a315f771
fn_stack.pop()
print(fn_stack)
print(apply_stack(1))  # x + 1 = 2
# doc-region-end 55dd21f698dbbde5bd5d1b332279d099a315f771

# doc-region-begin e09b968f9c8a2f9db13475d1c9ac310d94e54a2a
fn_stack.pop()
print(fn_stack)
print(apply_stack(1))  # x = 1
# doc-region-end e09b968f9c8a2f9db13475d1c9ac310d94e54a2a

glfw.terminate()
