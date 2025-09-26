# Copyright (c) 2018-2025 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import sys

import glfw
import OpenGL.GL as GL

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 2", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)

GL.glMatrixMode(GL.GL_PROJECTION)
GL.glLoadIdentity()
GL.glMatrixMode(GL.GL_MODELVIEW)
GL.glLoadIdentity()

# doc-region-begin event loop
while not glfw.window_should_close(window):
    # doc-region-end event loop
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # doc-region-begin draw paddle 1
    GL.glColor3f(0.578123, 0.0, 1.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex2f(-1.0, -0.3)  # vertex C
    GL.glVertex2f(-0.8, -0.3)  # vertex D
    GL.glVertex2f(-0.8, 0.3)  # vertex A
    GL.glVertex2f(-1.0, 0.3)  # vertex B
    GL.glEnd()
    # doc-region-end draw paddle 1

    # doc-region-begin draw paddle 2
    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex2f(0.8, -0.3)  # vertex G
    GL.glVertex2f(1.0, -0.3)  # vertex H
    GL.glVertex2f(1.0, 0.3)  # vertex E
    GL.glVertex2f(0.8, 0.3)  # vertex F
    GL.glEnd()
    # doc-region-end draw paddle 2

    # doc-region-begin flush framebuffer to monitor
    glfw.swap_buffers(window)
    # doc-region-end flush framebuffer to monitor

glfw.terminate()
