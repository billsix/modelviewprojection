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
from typing import List, Tuple

from modelviewprojection.mathutils import InvertibleFunction, compose
from modelviewprojection.mathutils1d import translate
from modelviewprojection.mathutils2d import Vector2D, scale, translate
from modelviewprojection.softwarerendering import clear_framebuffer
from modelviewprojection.softwarerendering import (
    draw_filled_triangle_vec as draw_filled_triangle,
)
from modelviewprojection.softwarerendering import (
    get_framebuffer,
    height,
    make_framebuffer,
    show_framebuffer,
    width,
)

# %%
# Show initial random framebuffer
make_framebuffer(width=700, height=500)
show_framebuffer()


# %%
# Clear to black and show
clear_framebuffer()
show_framebuffer()


# %% [markdown]
# Problem 2
# ---------
#
# Make a new picture below where the triangle is translated 0.3 units in NDC to the left

# %%
ndc_to_screen: InvertibleFunction[Vector2D] = compose(
    translate(Vector2D((width() + 0.5) // 2, (height() + 0.5) // 2)),
    scale((width() + 0.5) // 2, (height() + 0.5) // 2),
)

# %%
# Example: draw a white triangle

triangle_in_NDC: Tuple[Vector2D] = (
    Vector2D(0.0, 0.0),
    Vector2D(0.2, 0.0),
    Vector2D(0.2, 0.2),
)

# %%
triangle_in_screen: List[Vector2D] = [ndc_to_screen(x) for x in triangle_in_NDC]
print(triangle_in_screen)


clear_framebuffer()
draw_filled_triangle(
    triangle_in_screen[0],
    triangle_in_screen[1],
    triangle_in_screen[2],
    color=(255, 255, 255),
)
show_framebuffer()

# %%
move: InvertibleFunction[Vector2D] = translate(Vector2D(0, 0.5))

triangle_in_screen = [compose(ndc_to_screen, move)(x) for x in triangle_in_NDC]
print(triangle_in_screen)


clear_framebuffer()
draw_filled_triangle(*triangle_in_screen, color=(255, 255, 255))
show_framebuffer()

# %%
frames = []

import numpy as np

sixty_fps_times_2_sec = 120

# Create 10 frames with simple animation
for i in range(sixty_fps_times_2_sec):
    clear_framebuffer()
    move: InvertibleFunction[Vector2D] = translate(
        Vector2D(0, 0.5 * (np.sin(np.pi / 60.0 * float(i))))
    )

    triangle_in_screen = [
        compose(ndc_to_screen, move)(x) for x in triangle_in_NDC
    ]
    draw_filled_triangle(*triangle_in_screen, color=(255, 255, 255))

    frames.append(get_framebuffer())


np_frames = [np.array(img) for img in frames]
from IPython.display import Video
from moviepy import ImageSequenceClip

frames_np = [np.array(img) for img in frames]
clip = ImageSequenceClip(frames_np, fps=60)
clip.write_videofile("animation.mp4", codec="libx264")

Video("animation.mp4", embed=True)

# %%

# %%
