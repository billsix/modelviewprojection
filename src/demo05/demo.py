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
from dataclasses import dataclass

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
    glVertex2f,
    glViewport,
)

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 5", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0289, 0.071875, 0.0972, 1.0)

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


# doc-region-begin 45f8b976d5ca561e6551fced4b91491a0608e07c
@dataclass
class Vertex:
    x: float
    y: float

    def translate(self: Vertex, rhs: Vertex) -> Vertex:
        return Vertex(x=self.x + rhs.x, y=self.y + rhs.y)


# doc-region-end 45f8b976d5ca561e6551fced4b91491a0608e07c


# doc-region-begin c04057e28feefe7d49c375940e142dccd15bb006
@dataclass
class Paddle:
    vertices: list[Vertex]
    r: float
    g: float
    b: float
    position: Vertex


# doc-region-end c04057e28feefe7d49c375940e142dccd15bb006

# doc-region-begin 9e8aed62ab60a749bf800a0d2d975e9d5807aa91
paddle1: Paddle = Paddle(
    vertices=[
        Vertex(x=-0.1, y=-0.3),
        Vertex(x=0.1, y=-0.3),
        Vertex(x=0.1, y=0.3),
        Vertex(x=-0.1, y=0.3),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
    position=Vertex(-0.9, 0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vertex(-0.1, -0.3),
        Vertex(0.1, -0.3),
        Vertex(0.1, 0.3),
        Vertex(-0.1, 0.3),
    ],
    r=1.0,
    g=0.0,
    b=0.0,
    position=Vertex(0.9, 0.0),
)
# doc-region-end 9e8aed62ab60a749bf800a0d2d975e9d5807aa91


# doc-region-begin b0d86b4d150b3ca92951137634b12d7881ee6350
def handle_movement_of_paddles() -> None:
    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position.y -= 0.1
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position.y += 0.1
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position.y -= 0.1
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position.y += 0.1


# doc-region-end b0d86b4d150b3ca92951137634b12d7881ee6350

TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()

# doc-region-begin 1cacf5f226065bc4b85826f7642bf817a36b6540
while not glfw.window_should_close(window):
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
    handle_movement_of_paddles()
    # doc-region-end 1cacf5f226065bc4b85826f7642bf817a36b6540

    # doc-region-begin 9de7437ce84e5390a8907af83bb84e955ca80286
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        ndc_space: Vertex = model_space.translate(paddle1.position)
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # doc-region-end 9de7437ce84e5390a8907af83bb84e955ca80286

    # doc-region-begin 6b46719ca5e13f1c1c90c8ea495549599c6d0008
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        ndc_space: Vertex = model_space.translate(paddle2.position)
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # doc-region-end 6b46719ca5e13f1c1c90c8ea495549599c6d0008

    glfw.swap_buffers(window)

glfw.terminate()
