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


from typing import Tuple

import IPython.display as display
import numpy as np
import PIL
from IPython.display import display
from PIL import Image

from modelviewprojection.mathutils2d import Vector2D

WIDTH: int
HEIGHT: int
WIDTH, HEIGHT = 700, 700


def width() -> int:
    return WIDTH


def height() -> int:
    return HEIGHT


framebuffer: np.ndarray = np.random.randint(
    0, 256, (HEIGHT, WIDTH, 3), dtype=np.uint8
)

BLACK: Tuple[int, int, int] = (0, 0, 0)
WHITE: Tuple[int, int, int] = (255, 255, 255)
RED: Tuple[int, int, int] = (255, 0, 0)
GREEN: Tuple[int, int, int] = (0, 255, 0)
BLUE: Tuple[int, int, int] = (0, 0, 255)


def make_framebuffer(width: int, height: int) -> None:
    global WIDTH
    WIDTH = width
    global HEIGHT
    HEIGHT = height
    global framebuffer

    framebuffer = np.random.randint(0, 256, (HEIGHT, WIDTH, 3), dtype=np.uint8)


def show_framebuffer() -> None:
    """Display the framebuffer in the Jupyter notebook."""
    img = Image.fromarray(framebuffer, "RGB")
    display(img)


def get_framebuffer() -> PIL.Image.Image:
    return Image.fromarray(framebuffer, "RGB")


def clear_framebuffer(color=BLACK) -> None:
    """Fill the framebuffer with the given color."""
    global framebuffer
    framebuffer[:, :] = color


def draw_filled_triangle(
    p1: Tuple[int, int],
    p2: Tuple[int, int],
    p3: Tuple[int, int],
    color=(255, 255, 255),
):
    """
    Draw a filled triangle using the edge function (cross product) method.
    p1, p2, p3 are (x, y) tuples in framebuffer coordinates.
    """
    global framebuffer

    def to_fb_coords(x, y):
        """Convert from OpenGL-style coords to framebuffer array coords."""
        return x, HEIGHT - 1 - y

    x1: int
    y1: int
    x2: int
    y2: int
    z1: int
    z3: int

    x1, y1 = to_fb_coords(*p1)
    x2, y2 = to_fb_coords(*p2)
    x3, y3 = to_fb_coords(*p3)

    # Triangle bounding box
    min_x: int = max(int(min(x1, x2, x3)), 0)
    max_x: int = min(int(max(x1, x2, x3)), WIDTH - 1)
    min_y: int = max(int(min(y1, y2, y3)), 0)
    max_y: int = min(int(max(y1, y2, y3)), HEIGHT - 1)

    # Edge function (cross product)
    def edge(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> int:
        return (px - ax) * (by - ay) - (py - ay) * (bx - ax)

    # Precompute edge function signs for top-left rule
    area = edge(x1, y1, x2, y2, x3, y3)
    if area == 0:
        return  # Degenerate triangle

    # Loop over bounding box
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            w0 = edge(x2, y2, x3, y3, x, y)
            w1 = edge(x3, y3, x1, y1, x, y)
            w2 = edge(x1, y1, x2, y2, x, y)

            # If the signs match the triangle area, pixel is inside
            if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (
                w0 <= 0 and w1 <= 0 and w2 <= 0
            ):
                framebuffer[y, x] = color


def draw_filled_triangle_vec(
    v1: Vector2D, v2: Vector2D, v3: Vector2D, color=(255, 255, 255)
) -> None:
    """
    Draw a filled triangle using the edge function (cross product) method.
    p1, p2, p3 are (x, y) tuples in framebuffer coordinates.
    """
    global framebuffer

    def to_fb_coords(x, y):
        """Convert from OpenGL-style coords to framebuffer array coords."""
        return x, HEIGHT - 1 - y

    x1: int
    y1: int
    x2: int
    y2: int
    z1: int
    z3: int

    x1, y1 = to_fb_coords(int(v1.x), int(v1.y))
    x2, y2 = to_fb_coords(int(v2.x), int(v2.y))
    x3, y3 = to_fb_coords(int(v3.x), int(v3.y))

    # Triangle bounding box
    min_x: int = max(int(min(x1, x2, x3)), 0)
    max_x: int = min(int(max(x1, x2, x3)), WIDTH - 1)
    min_y: int = max(int(min(y1, y2, y3)), 0)
    max_y: int = min(int(max(y1, y2, y3)), HEIGHT - 1)

    # Edge function (cross product)
    def edge(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> int:
        return (px - ax) * (by - ay) - (py - ay) * (bx - ax)

    # Precompute edge function signs for top-left rule
    area: int = edge(x1, y1, x2, y2, x3, y3)
    if area == 0:
        return  # Degenerate triangle

    # Loop over bounding box
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            w0 = edge(x2, y2, x3, y3, x, y)
            w1 = edge(x3, y3, x1, y1, x, y)
            w2 = edge(x1, y1, x2, y2, x, y)

            # If the signs match the triangle area, pixel is inside
            if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (
                w0 <= 0 and w1 <= 0 and w2 <= 0
            ):
                framebuffer[y, x] = color
