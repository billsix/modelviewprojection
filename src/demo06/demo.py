# Copyright (c) 2018-2023 William Emerison Six
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

window = glfw.create_window(500, 500, "ModelViewProjection Demo 6", None, None)
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


# begin 8d06005b531874a91efb0a652db8527497f3a345
@dataclass
class Vertex:
    x: float
    y: float

    def translate(self: Vertex, tx: float, ty: float) -> Vertex:
        return Vertex(x=(self.x + tx), y=(self.y + ty))

    # end 8d06005b531874a91efb0a652db8527497f3a345

    # begin f8b77ac4a2656475404a658f038034e9ac9efb2e
    def scale(self: Vertex, scale_x: float, scale_y: float) -> Vertex:
        return Vertex(x=(self.x * scale_x), y=(self.y * scale_y))

    # end f8b77ac4a2656475404a658f038034e9ac9efb2e


@dataclass
class Paddle:
    vertices: list[Vertex]
    r: float
    g: float
    b: float
    position: Vertex


# begin be85f68c2e4e7e58096273ff1ab6a4abc162dc32
paddle1: Paddle = Paddle(
    vertices=[
        Vertex(x=-10.0, y=-30.0),
        Vertex(x=10.0, y=-30.0),
        Vertex(x=10.0, y=30.0),
        Vertex(x=-10.0, y=30.0),
    ],
    r=0.578123,
    g=0.0,
    b=1.0,
    position=Vertex(-90.0, 0.0),
)

paddle2: Paddle = Paddle(
    vertices=[
        Vertex(x=-10.0, y=-30.0),
        Vertex(x=10.0, y=-30.0),
        Vertex(x=10.0, y=30.0),
        Vertex(x=-10.0, y=30.0),
    ],
    r=1.0,
    g=0.0,
    b=0.0,
    position=Vertex(90.0, 0.0),
)
# end be85f68c2e4e7e58096273ff1ab6a4abc162dc32


# begin 1a17a9d680387b5c37d842115b617cdeb910be61
def handle_movement_of_paddles() -> None:
    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position.y -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position.y += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position.y -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position.y += 10.0


# end 1a17a9d680387b5c37d842115b617cdeb910be61

TARGET_FRAMERATE: int = 60

time_at_beginning_of_previous_frame: float = glfw.get_time()

# begin 3863f9f78b61a7b1c0c2faa12f9ea255c663edee
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
    # end 3863f9f78b61a7b1c0c2faa12f9ea255c663edee

    # begin 57631feba3dbad52833765b9bfc51c42d90141af
    glColor3f(paddle1.r, paddle1.g, paddle1.b)

    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        # end 57631feba3dbad52833765b9bfc51c42d90141af
        # fmt: off
        # begin 5b1156f32f2d788cec10cedf43b7847fe92f5350
        world_space: Vertex = model_space.translate(tx=paddle1.position.x,
                                                    ty=paddle1.position.y)
        # end 5b1156f32f2d788cec10cedf43b7847fe92f5350
        # begin 2091aa68e2d6d5bccdcb968391bf5d657fe9ad1a
        ndc_space: Vertex = world_space.scale(scale_x=1.0 / 100.0,
                                              scale_y=1.0 / 100.0)
        # end 2091aa68e2d6d5bccdcb968391bf5d657fe9ad1a
        # fmt: off
        # begin 4788d1809c34fff4b8a6e63bd28c0ca90184457a
        glVertex2f(ndc_space.x, ndc_space.y)

    glEnd()
    # end 4788d1809c34fff4b8a6e63bd28c0ca90184457a

    # begin db2e4352f654c9b0309ed0470515ff61113aec8d
    glColor3f(paddle2.r, paddle2.g, paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        # end db2e4352f654c9b0309ed0470515ff61113aec8d
        # fmt: off
        # begin 8654606ea6b0f530930d8d43f6c0d110e867e0d8
        world_space: Vertex = model_space.translate(tx=paddle2.position.x,
                                                    ty=paddle2.position.y)
        # end 8654606ea6b0f530930d8d43f6c0d110e867e0d8
        # begin a9da863c1edd7395ad98084f43056476991a5c5c
        ndc_space: Vertex = world_space.scale(scale_x=1.0 / 100.0,
                                              scale_y=1.0 / 100.0)
        # end a9da863c1edd7395ad98084f43056476991a5c5c
        # fmt: on

        # begin 260c1301effa6c7ec13f1b36454be3ff448ee641
        glVertex2f(ndc_space.x, ndc_space.y)
    glEnd()
    # end 260c1301effa6c7ec13f1b36454be3ff448ee641

    # begin 6d057656d804fe007498bc5d5314cb5a68788c67
    glfw.swap_buffers(window)
    # end 6d057656d804fe007498bc5d5314cb5a68788c67
glfw.terminate()
