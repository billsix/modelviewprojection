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

# doc-region-begin import first module
import sys

import glfw
import OpenGL.GL as GL

# doc-region-end import first module

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
def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)
# doc-region-end on user hitting escape, end event loop and quit

# doc-region-begin set background color
GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)
# doc-region-end set background color

# doc-region-begin don't use the built in mvp pipeline
GL.glMatrixMode(GL.GL_PROJECTION)
GL.glLoadIdentity()
GL.glMatrixMode(GL.GL_MODELVIEW)
GL.glLoadIdentity()
# doc-region-end don't use the built in mvp pipeline


# doc-region-begin event loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))
    glfw.swap_buffers(window)
    # doc-region-end event loop

glfw.terminate()
