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

"""Shared GLFW windowing helpers for the demos.

`on_key` is the escape-to-quit key callback used by every demo.  It is
introduced (and explained) in demo01 / chapter 1; from demo02 onward the
demos import it from here instead of redefining the identical boilerplate.
Per-frame, per-demo key handling lives in each demo's own `handle_inputs`,
which is intentionally *not* shared.
"""

import typing

import glfw

if typing.TYPE_CHECKING:
    # glfw types window handles as `_GLFWwindowPointerT`: private, absent at
    # runtime, so alias it here for the annotations below.
    from glfw import _GLFWwindowPointerT

    GLFWWindow = _GLFWwindowPointerT


def on_key(
    win: "GLFWWindow",
    key: int,
    scancode: int,
    action: int,
    mods: int,
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)
