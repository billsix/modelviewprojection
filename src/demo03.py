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

import sys

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

window = glfw.create_window(500, 500, "ModelViewProjection Demo 3", None, None)
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


# doc-region-begin square viewport
def draw_in_square_viewport() -> None:
    # doc-region-end square viewport

    # doc-region-begin set to gray
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    # doc-region-end set to gray

    # doc-region-begin get framebuffer size
    w, h = glfw.get_framebuffer_size(window)

    square_size = w if w < h else h
    # doc-region-end get framebuffer size

    # doc-region-begin enable scissor test
    glEnable(GL_SCISSOR_TEST)
    glScissor(
        int((w - square_size) / 2.0),  # bottom left x_screenspace
        int((h - square_size) / 2.0),  # bottom left y_screenspace
        square_size,  # x width, screenspace
        square_size,  # y height, screenspace
    )
    # doc-region-end enable scissor test

    # doc-region-begin set background to be close to black
    glClearColor(0.0289, 0.071875, 0.0972, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    # doc-region-end set background to be close to black
    # doc-region-begin disable scissor test
    glDisable(GL_SCISSOR_TEST)
    # doc-region-end disable scissor test
    # doc-region-begin set square viewport
    glViewport(
        int(0.0 + (w - square_size) / 2.0),
        int(0.0 + (h - square_size) / 2.0),
        square_size,
        square_size,
    )
    # doc-region-end set square viewport


# doc-region-begin event loop begin
while not glfw.window_should_close(window):
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # doc-region-end event loop begin

    # doc-region-begin call draw in square viewport
    draw_in_square_viewport()
    # doc-region-end call draw in square viewport
    # doc-region-begin draw both paddles
    glColor3f(0.578123, 0.0, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(-1.0, -0.3)
    glVertex2f(-0.8, -0.3)
    glVertex2f(-0.8, 0.3)
    glVertex2f(-1.0, 0.3)
    glEnd()

    glColor3f(1.0, 1.0, 0.0)
    glBegin(GL_QUADS)

    glVertex2f(0.8, -0.3)
    glVertex2f(1.0, -0.3)
    glVertex2f(1.0, 0.3)
    glVertex2f(0.8, 0.3)
    glEnd()

    glfw.swap_buffers(window)
    # doc-region-end draw both paddles
glfw.terminate()
