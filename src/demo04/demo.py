# Copyright (c) 2018-2022 William Emerison Six
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
    glVertex2f,
    glEnd,
    glEnable,
    GL_SCISSOR_TEST,
    glScissor,
    glDisable,
)
import glfw

from dataclasses import dataclass

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

glClearColor(0.0, 0.0, 0.0, 1.0)

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


# begin defvertexclass
@dataclass
class Vertex:
    x: float
    y: float
# end defvertexclass

# begin defpaddleclass
@dataclass
class Paddle:
    vertices: list[Vertex]
    r: float
    g: float
    b: float
# end defpaddleclass

# begin defpaddles
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
    g=0.0,
    b=0.0,
)
# end defpaddles


# begin fnhandle
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
# end fnhandle

# begin framerate
TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()
# end framerate

# begin eventloop
while not glfw.window_should_close(window):

    while (
        glfw.get_time() < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass

    time_at_beginning_of_previous_frame = glfw.get_time()
    # end eventloop

    # begin startframe
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # end startframe

    # begin square
    draw_in_square_viewport()
    # end square

    # begin movement
    handle_movement_of_paddles()
    # end movement

    # begin paddle1
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for vertex in paddle1.vertices:
        glVertex2f(vertex.x, vertex.y)
    glEnd()
    # end paddle1

    # begin paddle2
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for vertex in paddle2.vertices:
        glVertex2f(vertex.x, vertex.y)
    glEnd()
    # end paddle2

    # begin swapbuffers
    glfw.swap_buffers(window)
    # end swapbuffers

glfw.terminate()
