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
import typing
import modelviewprojection.softwarerendering as sr

import modelviewprojection.mathutils as mu
import modelviewprojection.mathutils2d as mu2d
import IPython.display
import moviepy
import numpy as np


# %%
# Show initial random framebuffer
fake_fb: sr.FrameBuffer = sr.FrameBuffer(width=700, height=500)
fake_fb.show_framebuffer()


# %%
# Clear to black and show
fake_fb.clear_framebuffer()
fake_fb.show_framebuffer()


# %% [markdown]
# Problem 2
# ---------
#
# Make a new picture below where the triangle is mu.translated 0.3 units in NDC to the left

# %%
ndc_to_screen: mu.InvertibleFunction[mu2d.Vector2D] = mu.compose(
    mu.translate(
        mu2d.Vector2D((fake_fb.width + 0.5) // 2, (fake_fb.height + 0.5) // 2)
    ),
    mu2d.scale((fake_fb.width + 0.5) // 2, (fake_fb.height + 0.5) // 2),
)

# %%
# Example: draw a white triangle

triangle_in_NDC: typing.Tuple[mu2d.Vector2D] = (
    mu2d.Vector2D(0.0, 0.0),
    mu2d.Vector2D(0.2, 0.0),
    mu2d.Vector2D(0.2, 0.2),
)

# %%
triangle_in_screen: typing.List[mu2d.Vector2D] = [
    ndc_to_screen(x) for x in triangle_in_NDC
]
print(triangle_in_screen)


fake_fb.clear_framebuffer()
fake_fb.draw_filled_triangle(
    triangle_in_screen[0],
    triangle_in_screen[1],
    triangle_in_screen[2],
    color=(255, 255, 255),
)
fake_fb.show_framebuffer()

# %%
move: mu.InvertibleFunction[mu2d.Vector2D] = mu.translate(mu2d.Vector2D(0, 0.5))

triangle_in_screen = [
    mu.compose(ndc_to_screen, move)(x) for x in triangle_in_NDC
]
print(triangle_in_screen)


fake_fb.clear_framebuffer()
fake_fb.draw_filled_triangle(*triangle_in_screen, color=(255, 255, 255))
fake_fb.show_framebuffer()

# %%
frames = []


sixty_fps_times_2_sec = 120

# Create 10 frames with simple animation
for i in range(sixty_fps_times_2_sec):
    fake_fb.clear_framebuffer()
    move: mu.InvertibleFunction[mu2d.Vector2D] = mu.translate(
        mu2d.Vector2D(0, 0.5 * (np.sin(np.pi / 60.0 * float(i))))
    )

    triangle_in_screen = [
        mu.compose(ndc_to_screen, move)(x) for x in triangle_in_NDC
    ]
    fake_fb.draw_filled_triangle(*triangle_in_screen, color=(255, 255, 255))

    frames.append(fake_fb.framebuffer)


np_frames = [np.array(img) for img in frames]

frames_np = [np.array(img) for img in frames]
clip = moviepy.ImageSequenceClip(frames_np, fps=60)
clip.write_videofile("animation.mp4", codec="libx264")

IPython.display.Video("animation.mp4", embed=True)

# %%

# %%
