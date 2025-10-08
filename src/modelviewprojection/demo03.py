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
from modelviewprojection.glhelper import clear_mask

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

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)

GL.glMatrixMode(GL.GL_PROJECTION)
GL.glLoadIdentity()
GL.glMatrixMode(GL.GL_MODELVIEW)
GL.glLoadIdentity()


# doc-region-begin square viewport
def draw_in_square_viewport() -> None:
    # doc-region-end square viewport

    # doc-region-begin set to gray
    GL.glClearColor(0.2, 0.2, 0.2, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    # doc-region-end set to gray

    # doc-region-begin get framebuffer size
    w, h = glfw.get_framebuffer_size(window)

    square_size = w if w < h else h
    # doc-region-end get framebuffer size

    # doc-region-begin enable scissor test
    GL.glEnable(GL.GL_SCISSOR_TEST)
    GL.glScissor(
        int((w - square_size) / 2.0),  # bottom left x_screenspace
        int((h - square_size) / 2.0),  # bottom left y_screenspace
        square_size,  # x width, screenspace
        square_size,  # y height, screenspace
    )
    # doc-region-end enable scissor test

    # doc-region-begin set background to be close to black
    GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    # doc-region-end set background to be close to black
    # doc-region-begin disable scissor test
    GL.glDisable(GL.GL_SCISSOR_TEST)
    # doc-region-end disable scissor test
    # doc-region-begin set square viewport
    GL.glViewport(
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
    GL.glViewport(0, 0, width, height)
    GL.glClear(clear_mask(GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT))
    # doc-region-end event loop begin

    # doc-region-begin call draw in square viewport
    draw_in_square_viewport()
    # doc-region-end call draw in square viewport
    # doc-region-begin draw both paddles
    GL.glColor3f(0.578123, 0.0, 1.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex2f(-1.0, -0.3)
    GL.glVertex2f(-0.8, -0.3)
    GL.glVertex2f(-0.8, 0.3)
    GL.glVertex2f(-1.0, 0.3)
    GL.glEnd()

    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glBegin(GL.GL_QUADS)

    GL.glVertex2f(0.8, -0.3)
    GL.glVertex2f(1.0, -0.3)
    GL.glVertex2f(1.0, 0.3)
    GL.glVertex2f(0.8, 0.3)
    GL.glEnd()

    glfw.swap_buffers(window)
    # doc-region-end draw both paddles
glfw.terminate()
