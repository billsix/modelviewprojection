# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Framebuffer

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


import warnings

import modelviewprojection.mathutils2d as mu2d

# %%
import modelviewprojection.softwarerendering as sr

# turn warnings into exceptions
warnings.filterwarnings("error", category=RuntimeWarning)
# %% [markdown]
# Make a framebuffer, which is just a rectangular region of values

# %%
# Show initial random framebuffer
fake_fb: sr.FrameBuffer = sr.FrameBuffer(width=100, height=100)
fake_fb.show_framebuffer()


# %% [raw]
# Draw a triangle in the framebuffer

# %%
# Example: draw a white triangle
fake_fb.draw_filled_triangle(
    mu2d.Vector2D(50, 50),
    mu2d.Vector2D(50, 70),
    mu2d.Vector2D(70, 70),
    color=sr.WHITE,
)
fake_fb.show_framebuffer()


# %% [raw]
# Whoops!  That looks like trash.  We should change the background to
# have all one color.  That's what clear_framebuffer does

# %%
# Clear to red and show
fake_fb.clear_color = sr.RED
fake_fb.clear_framebuffer()
fake_fb.show_framebuffer()

# %%
# Clear to black and show
fake_fb.clear_color = sr.BLACK
fake_fb.clear_framebuffer()
fake_fb.show_framebuffer()


# %%
# Example: draw a white triangle
fake_fb.clear_framebuffer()
fake_fb.draw_filled_triangle(
    mu2d.Vector2D(50, 50),
    mu2d.Vector2D(50, 70),
    mu2d.Vector2D(70, 70),
    color=sr.WHITE,
)
fake_fb.show_framebuffer()

# draw a red triangle
fake_fb.draw_filled_triangle(
    mu2d.Vector2D(50, 50),
    mu2d.Vector2D(30, 50),
    mu2d.Vector2D(30, 30),
    color=sr.RED,
)
fake_fb.show_framebuffer()

# %% [markdown]
# Make a larger framebuffer
# %%
# Show initial random framebuffer
fake_fb400: sr.FrameBuffer = sr.FrameBuffer(width=400, height=400)
fake_fb400.show_framebuffer()


# %%
# Clear to black and show
fake_fb400.clear_framebuffer()
fake_fb400.show_framebuffer()


# %%
# Example: draw a white triangle
fake_fb400.clear_framebuffer()
fake_fb400.draw_filled_triangle(
    mu2d.Vector2D(50, 50),
    mu2d.Vector2D(50, 70),
    mu2d.Vector2D(70, 70),
    color=sr.WHITE,
)
fake_fb400.show_framebuffer()

fake_fb400.draw_filled_triangle(
    mu2d.Vector2D(50, 50),
    mu2d.Vector2D(30, 50),
    mu2d.Vector2D(30, 30),
    color=sr.RED,
)
fake_fb400.show_framebuffer()

# %%

# %%
