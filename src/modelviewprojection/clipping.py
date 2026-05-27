# Copyright (c) 2018-2026 William Emerison Six
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

"""Shared clipping helper for the demos.

`draw_in_square_viewport` is introduced and dissected in demo03 / chapter 3 --
it scissors+sets a centered square region so the scene keeps a 1:1 aspect ratio
regardless of window shape.  From demo04 onward the demos import it from here
instead of redefining the identical body.  (demo03 keeps its own annotated copy
for the chapter; demo19e keeps its own -- it uses a different background color.)
"""

import glfw
import OpenGL.GL as GL


def draw_in_square_viewport(window) -> None:
    GL.glClearColor(0.2, 0.2, 0.2, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    w, h = glfw.get_framebuffer_size(window)
    minimal_dimension = w if w < h else h

    GL.glEnable(GL.GL_SCISSOR_TEST)
    GL.glScissor(
        int((w - minimal_dimension) / 2.0),
        int((h - minimal_dimension) / 2.0),
        minimal_dimension,
        minimal_dimension,
    )

    GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glDisable(GL.GL_SCISSOR_TEST)

    GL.glViewport(
        int(0.0 + (w - minimal_dimension) / 2.0),
        int(0.0 + (h - minimal_dimension) / 2.0),
        minimal_dimension,
        minimal_dimension,
    )
