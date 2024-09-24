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

window = glfw.create_window(500, 500, "ModelViewProjection Demo 4", None, None)
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


# doc-region-begin ca6358d2d0e38e03d5c0642954e9a34ed62ab406
@dataclass
class Vertex:
    x: float
    y: float


# doc-region-end ca6358d2d0e38e03d5c0642954e9a34ed62ab406


# doc-region-begin ecf8e1a61285c18b321fef38792c6e6a5c1ca79c
@dataclass
class Paddle:
    vertices: list[Vertex]
    r: float
    g: float
    b: float


# doc-region-end ecf8e1a61285c18b321fef38792c6e6a5c1ca79c

# doc-region-begin 6ab0efd624f5d076b983e875700a2b2307788cc2
paddle1 = Paddle(
    vertices=[
        Vertex(x=-1.0, y=-0.3),
        Vertex(x=-0.8, y=-0.3),
        Vertex(x=-0.8, y=0.3),
        Vertex(x=-1.0, y=0.3),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
)

paddle2 = Paddle(
    vertices=[Vertex(0.8, -0.3), Vertex(1.0, -0.3), Vertex(1.0, 0.3), Vertex(0.8, 0.3)],
    r=1.0,
    g=1.0,
    b=0.0,
)
# doc-region-end 6ab0efd624f5d076b983e875700a2b2307788cc2


# doc-region-begin 4b68726b67eef939645c430941518f4fb374f0c8
def handle_movement_of_paddles() -> None:
    global paddle1, paddle2
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        for v in paddle1.vertices:
            v.y -= 0.1
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        for v in paddle1.vertices:
            v.y += 0.1
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        for v in paddle2.vertices:
            v.y -= 0.1
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        for v in paddle2.vertices:
            v.y += 0.1


# doc-region-end 4b68726b67eef939645c430941518f4fb374f0c8

# doc-region-begin 2ef80e67f318610c9d846513e604bdff5d037285
TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()
# doc-region-end 2ef80e67f318610c9d846513e604bdff5d037285

# doc-region-begin 89e003b98e8ebecccb7ad30f6cd29e35a1a6e0f2
while not glfw.window_should_close(window):
    while (
        glfw.get_time() < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass

    time_at_beginning_of_previous_frame = glfw.get_time()
    # doc-region-end 89e003b98e8ebecccb7ad30f6cd29e35a1a6e0f2

    # doc-region-begin c414af3df41f977118e25fb4e96de3194469a04a
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # doc-region-end c414af3df41f977118e25fb4e96de3194469a04a

    # doc-region-begin daaa146fafc0d1c453ca4dcc38b7b9df1f92b0fd
    draw_in_square_viewport()
    # doc-region-end daaa146fafc0d1c453ca4dcc38b7b9df1f92b0fd

    # doc-region-begin 96ff95610f3df28ee581dcad279dce732a45920c
    handle_movement_of_paddles()
    # doc-region-end 96ff95610f3df28ee581dcad279dce732a45920c

    # doc-region-begin 43814a73075f8265e8b55941fded5bd024914743
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for vertex in paddle1.vertices:
        glVertex2f(vertex.x, vertex.y)
    glEnd()
    # doc-region-end 43814a73075f8265e8b55941fded5bd024914743

    # doc-region-begin 2126570070cea12469df9ade20858acf7ac414c7
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for vertex in paddle2.vertices:
        glVertex2f(vertex.x, vertex.y)
    glEnd()
    # doc-region-end 2126570070cea12469df9ade20858acf7ac414c7

    # doc-region-begin cda9e45b9bd0c4a866156e72290667c32015ea59
    glfw.swap_buffers(window)
    # doc-region-end cda9e45b9bd0c4a866156e72290667c32015ea59

glfw.terminate()
