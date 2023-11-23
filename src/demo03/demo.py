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

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 3", None, None)
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


# begin 1a8e13a46337c0e9ac0f9436953d66dec069eb1f
def draw_in_square_viewport() -> None:
    # end 1a8e13a46337c0e9ac0f9436953d66dec069eb1f

    # begin 263830783a8fbe25283deaa80688f95592917298
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    # end 263830783a8fbe25283deaa80688f95592917298

    # begin 3db7c4975ad4354e344c0a2f0d4d94125195ce32
    width, height = glfw.get_framebuffer_size(window)

    square_size = width if width < height else height
    # end 3db7c4975ad4354e344c0a2f0d4d94125195ce32

    # begin a2d0bcb5b525e8a68e0bc1ef213359f165981839enablescissortest
    glEnable(GL_SCISSOR_TEST)
    glScissor(
        int((width - square_size) / 2.0),  # bottom left x_screenspace
        int((height - square_size) / 2.0),  # bottom left y_screenspace
        square_size,  # x width, screenspace
        square_size,  # y height, screenspace
    )
    # end a2d0bcb5b525e8a68e0bc1ef213359f165981839enablescissortest

    # begin db4245dba3c0c229416c97fe84da3cb87b1f439d
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    # end db4245dba3c0c229416c97fe84da3cb87b1f439d
    # begin 9524935cab9f5725f921d11969872ebd9a54e508
    glDisable(GL_SCISSOR_TEST)
    # end 9524935cab9f5725f921d11969872ebd9a54e508
    # begin defaeb0e6b9ada0b6c349a4dec907300e4c14acbviewportcall
    glViewport(
        int(0.0 + (width - square_size) / 2.0),
        int(0.0 + (height - square_size) / 2.0),
        square_size,
        square_size,
    )
    # end defaeb0e6b9ada0b6c349a4dec907300e4c14acbviewportcall


# begin 33fecc926105eda74989fb02da7daca03e3bfea8
while not glfw.window_should_close(window):
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # end 33fecc926105eda74989fb02da7daca03e3bfea8

    # begin 415cedbd77f6cc02a34de30d2da1b24cab344c5c
    draw_in_square_viewport()
    # end 415cedbd77f6cc02a34de30d2da1b24cab344c5c
    # begin bf9a23e3296c75d786d75f7b0e406448b773b23b
    glColor3f(0.578123, 0.0, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(-1.0, -0.3)
    glVertex2f(-0.8, -0.3)
    glVertex2f(-0.8, 0.3)
    glVertex2f(-1.0, 0.3)
    glEnd()

    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_QUADS)

    glVertex2f(0.8, -0.3)
    glVertex2f(1.0, -0.3)
    glVertex2f(1.0, 0.3)
    glVertex2f(0.8, 0.3)
    glEnd()

    glfw.swap_buffers(window)
    # end bf9a23e3296c75d786d75f7b0e406448b773b23b
glfw.terminate()
