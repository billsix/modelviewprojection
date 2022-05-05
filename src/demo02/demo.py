# Copyright (c) 2018-2022 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import os
import numpy as np
import math
import OpenGL.GL
import glfw


if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 2", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

OpenGL.GL.glClearColor(0.0, 0.0, 0.0, 1.0)

OpenGL.GL.glMatrixMode(OpenGL.GL.GL_PROJECTION)
OpenGL.GL.glLoadIdentity()
OpenGL.GL.glMatrixMode(OpenGL.GL.GL_MODELVIEW)
OpenGL.GL.glLoadIdentity()

while not glfw.window_should_close(window):
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    OpenGL.GL.glViewport(0, 0, width, height)
    OpenGL.GL.glClear(OpenGL.GL.GL_COLOR_BUFFER_BIT | OpenGL.GL.GL_DEPTH_BUFFER_BIT)

    OpenGL.GL.glColor3f(0.578123, 0.0, 1.0)
    OpenGL.GL.glBegin(OpenGL.GL.GL_QUADS)
    OpenGL.GL.glVertex2f(-1.0, -0.3)
    OpenGL.GL.glVertex2f(-0.8, -0.3)
    OpenGL.GL.glVertex2f(-0.8, 0.3)
    OpenGL.GL.glVertex2f(-1.0, 0.3)
    OpenGL.GL.glEnd()

    OpenGL.GL.glColor3f(1.0, 0.0, 0.0)
    OpenGL.GL.glBegin(OpenGL.GL.GL_QUADS)
    OpenGL.GL.glVertex2f(0.8, -0.3)
    OpenGL.GL.glVertex2f(1.0, -0.3)
    OpenGL.GL.glVertex2f(1.0, 0.3)
    OpenGL.GL.glVertex2f(0.8, 0.3)
    OpenGL.GL.glEnd()

    glfw.swap_buffers(window)

glfw.terminate()
