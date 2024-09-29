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

# fmt: off
# doc-region-begin import first module
import sys

# doc-region-begin import glfw
import glfw
# doc-region-begin import individual functions without needing module name
from OpenGL.GL import (GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_MODELVIEW,
                       GL_PROJECTION, glClear, glClearColor, glLoadIdentity,
                       glMatrixMode, glViewport)

# doc-region-end import first module

# doc-region-end import glfw


# doc-region-end import individual functions without needing module name
# fmt: on

# doc-region-begin initialize glfw
if not glfw.init():
    sys.exit()
# doc-region-end initialize glfw

# doc-region-begin use opengl 1.4
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
# doc-region-end use opengl 1.4

# doc-region-begin create window
window = glfw.create_window(500, 500, "ModelViewProjection Demo 1", None, None)
# doc-region-end create window

# doc-region-begin if the window is not created correctly, quit
if not window:
    glfw.terminate()
    sys.exit()
# doc-region-end if the window is not created correctly, quit

# doc-region-begin make context current
glfw.make_context_current(window)
# doc-region-end make context current


# doc-region-begin on user hitting escape, end event loop and quit
def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


# doc-region-end on user hitting escape, end event loop and quit

glfw.set_key_callback(window, on_key)

# doc-region-begin set background color
glClearColor(0.0289, 0.071875, 0.0972, 1.0)
# doc-region-end set background color

# doc-region-begin don't use the built in mvp pipeline
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()
# doc-region-end don't use the built in mvp pipeline


# doc-region-begin event loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glfw.swap_buffers(window)
# doc-region-end event loop

glfw.terminate()
