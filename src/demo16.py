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

import sys
from dataclasses import dataclass, field

import glfw
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    GL_SCISSOR_TEST,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glLoadIdentity,
    glMatrixMode,
    glScissor,
    glVertex3f,
    glViewport,
)

from mathutils3d import (
    Vertex3D,
    compose,
    fn_stack,
    inverse,
    rotate_z,
    translate,
    uniform_scale,
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


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0289, 0.071875, 0.0972, 1.0)


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
class Paddle:
    vertices: list[Vertex3D]
    r: float
    g: float
    b: float
    position: Vertex3D
    rotation: float = 0.0


# doc-region-begin instantiate paddle 1
paddle1: Paddle = Paddle(
    vertices=[
        Vertex3D(x=-1.0, y=-3.0, z=0.0),
        Vertex3D(x=1.0, y=-3.0, z=0.0),
        Vertex3D(x=1.0, y=3.0, z=0.0),
        Vertex3D(x=-1.0, y=3.0, z=0.0),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
    position=Vertex3D(x=-9.0, y=0.0, z=0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vertex3D(x=-1.0, y=-3.0, z=0.0),
        Vertex3D(x=1.0, y=-3.0, z=0.0),
        Vertex3D(x=1.0, y=3.0, z=0.0),
        Vertex3D(x=-1.0, y=3.0, z=0.0),
    ],
    r=1.0,
    g=1.0,
    b=0.0,
    position=Vertex3D(x=9.0, y=0.0, z=0.0),
)
# doc-region-end instantiate paddle 1


# doc-region-begin define camera class
@dataclass
class Camera:
    position_ws: Vertex3D = field(
        default_factory=lambda: Vertex3D(x=0.0, y=0.0, z=0.0)
    )


camera: Camera = Camera()
# doc-region-end define camera class

# doc-region-begin instantiate square
square: list[Vertex3D] = [
    Vertex3D(x=-0.5, y=-0.5, z=0.0),
    Vertex3D(x=0.5, y=-0.5, z=0.0),
    Vertex3D(x=0.5, y=0.5, z=0.0),
    Vertex3D(x=-0.5, y=0.5, z=0.0),
]
# doc-region-end instantiate square

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

    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.position_ws.y += 1.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_ws.y -= 1.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.position_ws.x -= 1.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.position_ws.x += 1.0

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


TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()

# doc-region-begin begin event loop
while not glfw.window_should_close(window):
    # doc-region-end begin event loop
    while (
        glfw.get_time()
        < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
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

    # doc-region-begin stack push camera space to ndc
    # camera space to NDC
    fn_stack.push(uniform_scale(1.0 / 10.0))
    # doc-region-end stack push camera space to ndc

    # doc-region-begin world space to camera space
    # world space to camera space
    fn_stack.push(inverse(translate(camera.position_ws)))
    # doc-region-end world space to camera space

    # doc-region-begin paddle 1 transformations
    # paddle 1 model space to world space
    fn_stack.push(compose(translate(paddle1.position),
                          rotate_z(paddle1.rotation)))
    # doc-region-end paddle 1 transformations

    # doc-region-begin draw paddle 1
    glColor3f(paddle1.r, paddle1.g, paddle1.b)
    glBegin(GL_QUADS)
    for p1_v_ms in paddle1.vertices:
        paddle1_vertex_ndc = fn_stack.modelspace_to_ndc_fn()(p1_v_ms)
        glVertex3f(
            paddle1_vertex_ndc.x,
            paddle1_vertex_ndc.y,
            paddle1_vertex_ndc.z,
        )
    glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin draw square

    # square space to paddle 1 space
    fn_stack.push(compose(translate(Vertex3D(x=0.0, y=0.0, z=-1.0)),
                          rotate_z(rotation_around_paddle1),
                          translate(Vertex3D(x=2.0, y=0.0, z=0.0)),
                          rotate_z(square_rotation)))
    # draw square
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_QUADS)
    for ms in square:
        square_vertex_ndc = fn_stack.modelspace_to_ndc_fn()(ms)
        glVertex3f(
            square_vertex_ndc.x,
            square_vertex_ndc.y,
            square_vertex_ndc.z,
        )
    glEnd()
    # doc-region-end draw square

    fn_stack.pop()  # pop off square space to paddle 1 space
    # current space is paddle 1 space
    fn_stack.pop()  # # pop off paddle 1 model space to world space
    # current space is world space

    # paddle 2 model space to world space
    fn_stack.push(compose(translate(paddle2.position),
                          rotate_z(paddle2.rotation)))

    # doc-region-begin draw paddle 2
    # draw paddle 2
    glColor3f(paddle2.r, paddle2.g, paddle2.b)
    glBegin(GL_QUADS)
    for p2_v_ms in paddle2.vertices:
        paddle2_vertex_ndc = fn_stack.modelspace_to_ndc_fn()(p2_v_ms)
        glVertex3f(
            paddle2_vertex_ndc.x,
            paddle2_vertex_ndc.y,
            paddle2_vertex_ndc.z,
        )
    glEnd()
    # doc-region-end draw paddle 2
    # fmt: on

    # doc-region-begin clear function stack for next iteration of the event loop
    # done rendering everything for this frame, just go ahead and clear all functions
    # off of the stack, back to NDC as current space
    fn_stack.clear()

    # doc-region-end clear function stack for next iteration of the event loop

    glfw.swap_buffers(window)

glfw.terminate()
