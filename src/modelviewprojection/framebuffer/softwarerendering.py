# Copyright (c) 2025-2026 William Emerison Six
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

import dataclasses
import typing

import IPython.display as display
import numpy as np
import PIL
import PIL.Image

from modelviewprojection.mathutils import (
    Vector2,
    compose,
    is_clockwise,
    is_counter_clockwise,
    is_parallel,
    scale_non_uniform,
    translate,
)



BLACK: typing.Tuple[int, int, int] = (0, 0, 0)
WHITE: typing.Tuple[int, int, int] = (255, 255, 255)
RED: typing.Tuple[int, int, int] = (255, 0, 0)
GREEN: typing.Tuple[int, int, int] = (0, 255, 0)
BLUE: typing.Tuple[int, int, int] = (0, 0, 255)


@dataclasses.dataclass
class FrameBuffer:
    width: int  #: The width of the framebuffer
    height: int  #: The height of the framebuffer
    clear_color: typing.Tuple[int, int, int] = dataclasses.field(
        default_factory=lambda: BLACK
    )  # the color that should be used for clear_color
    _framebuffer: np.ndarray = dataclasses.field(
        init=False
    )  # the array that holds the color values

    def __post_init__(self):
        self._framebuffer = np.random.randint(
            0, 256, (self.height, self.width, 3), dtype=np.uint8
        )

    @property
    def framebuffer(self) -> PIL.Image.Image:
        return PIL.Image.fromarray(self._framebuffer, "RGB")

    def show_framebuffer(self) -> None:
        """Display the framebuffer in the Jupyter notebook."""
        display.display(self.framebuffer)

    def clear_framebuffer(self) -> None:
        """Fill the framebuffer with the given color."""
        self._framebuffer[:, :] = self.clear_color

    def screenspace_to_framebuffer(self, v: Vector2) -> Vector2:
        """Convert from OpenGL-style coords to framebuffer array coords."""
        ss_to_fb = compose(
            [
                translate((self.height - 1) * Vector2.e_2),
                scale_non_uniform(1, -1),
            ]
        )
        return ss_to_fb(v)

    def set_color(self, v: Vector2, color: typing.Tuple[int, int, int]):
        self._framebuffer[int(round(v.coeff_e_2)), int(round(v.coeff_e_1))] = color

    def draw_filled_triangle(
        self,
        p1: Vector2,
        p2: Vector2,
        p3: Vector2,
        color=(255, 255, 255),
    ):
        """
        Draw a filled triangle using the edge function (cross product) method.
        p1, p2, p3 are (x, y) tuples in framebuffer coordinates.
        """
        x1: int
        y1: int
        x2: int
        y2: int
        x3: int
        y3: int

        x1, y1 = iter(self.screenspace_to_framebuffer(p1))
        x2, y2 = iter(self.screenspace_to_framebuffer(p2))
        x3, y3 = iter(self.screenspace_to_framebuffer(p3))

        # Triangle bounding box
        min_x: int = max(int(min(x1, x2, x3)), 0)
        max_x: int = min(int(max(x1, x2, x3)), self.width - 1)
        min_y: int = max(int(min(y1, y2, y3)), 0)
        max_y: int = min(int(max(y1, y2, y3)), self.height - 1)

        v1: Vector2 = x1 * Vector2.e_1 + y1 * Vector2.e_2
        v2: Vector2 = x2 * Vector2.e_1 + y2 * Vector2.e_2
        v3: Vector2 = x3 * Vector2.e_1 + y3 * Vector2.e_2

        # a zero-length edge (coincident vertices) or collinear vertices give a
        # zero-area triangle -- is_parallel now answers True for those instead of
        # dividing by zero
        if is_parallel(v2 - v1, v3 - v2):
            return  # degenerate triangle

        # Loop over bounding box
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                pixel_position: Vector2 = x * Vector2.e_1 + y * Vector2.e_2
                counter_clockwise_values: list[bool] = [
                    is_counter_clockwise(v2 - v1, pixel_position - v1),
                    is_counter_clockwise(v3 - v2, pixel_position - v2),
                    is_counter_clockwise(v1 - v3, pixel_position - v3),
                ]
                clockwise_values: list[bool] = [
                    is_clockwise(v2 - v1, pixel_position - v1),
                    is_clockwise(v3 - v2, pixel_position - v2),
                    is_clockwise(v1 - v3, pixel_position - v3),
                ]

                # Inside (or on the boundary) when the pixel is on the same side
                # of every edge.  A pixel exactly on an edge or vertex has a zero
                # cross there -- counted as both CCW and CW -- so it is lit for
                # either winding, vertices included.
                if all(counter_clockwise_values) or all(clockwise_values):
                    self.set_color(x * Vector2.e_1 + y * Vector2.e_2, color)
