# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
# Copyright (c) 2025 William Emerison Six
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


# %%
from modelviewprojection.softwarerendering import (
    RED,
    WHITE,
    clear_framebuffer,
    draw_filled_triangle,
    make_framebuffer,
    show_framebuffer,
)

# %%
# Show initial random framebuffer
make_framebuffer(width=100, height=100)
show_framebuffer()


# %%
# Clear to black and show
clear_framebuffer()
show_framebuffer()


# %%
# Example: draw a white triangle
clear_framebuffer()
draw_filled_triangle((50, 50), (50, 70), (70, 70), color=WHITE)
show_framebuffer()

draw_filled_triangle((50, 50), (30, 50), (30, 30), color=RED)
show_framebuffer()

# %%
# %%
# Show initial random framebuffer
make_framebuffer(width=400, height=400)
show_framebuffer()


# %%
# Clear to black and show
clear_framebuffer()
show_framebuffer()


# %%
# Example: draw a white triangle
clear_framebuffer()
draw_filled_triangle((50, 50), (50, 70), (70, 70), color=WHITE)
show_framebuffer()

draw_filled_triangle((50, 50), (30, 50), (30, 30), color=RED)
show_framebuffer()

# %%

# %%
