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

import dataclasses
import typing

import IPython.display as display
import numpy as np
import PIL
import PIL.Image

import modelviewprojection.mathutils2d as mu2d

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
    def framebuffer(self) -> PIL.Image:
        return PIL.Image.fromarray(self._framebuffer, "RGB")

    @framebuffer.setter
    def framebuffer(self, value: PIL.Image) -> None:
        self._framebuffer = value

    def show_framebuffer(self) -> None:
        """Display the framebuffer in the Jupyter notebook."""
        display.display(self.framebuffer)

    def clear_framebuffer(self) -> None:
        """Fill the framebuffer with the given color."""
        self._framebuffer[:, :] = self.clear_color

    def screenspace_to_framebuffer(self, v: mu2d.Vector2D) -> mu2d.Vector2D:
        """Convert from OpenGL-style coords to framebuffer array coords."""
        ss_to_fb = mu2d.compose(
            [
                mu2d.translate(mu2d.Vector2D(0, self.height - 1)),
                mu2d.scale(m_x=1, m_y=-1),
            ]
        )
        return ss_to_fb(v)

    def set_color(self, v: mu2d.Vector2D, color: typing.Tuple[int, int, int]):
        self._framebuffer[int(round(v.y)), int(round(v.x))] = color

    def draw_filled_triangle(
        self,
        p1: mu2d.Vector2D,
        p2: mu2d.Vector2D,
        p3: mu2d.Vector2D,
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

        v1: mu2d.Vector2D = mu2d.Vector2D(x1, y1)
        v2: mu2d.Vector2D = mu2d.Vector2D(x2, y2)
        v3: mu2d.Vector2D = mu2d.Vector2D(x3, y3)

        try:
            if mu2d.is_parallel(v2 - v1, v3 - v2):
                return  # Degenerate triangle
        except RuntimeWarning:
            # if any of the Vectors are 0, nothing to do with that pixel
            pass

        # Loop over bounding box
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                pixel_position: mu2d.Vector2D = mu2d.Vector2D(x, y)
                try:
                    counter_clockwise_values: typing.List[bool] = [
                        mu2d.is_counter_clockwise(v2 - v1, pixel_position - v1),
                        mu2d.is_counter_clockwise(v3 - v2, pixel_position - v2),
                        mu2d.is_counter_clockwise(v1 - v3, pixel_position - v3),
                    ]

                    # If the signs match the triangle area, pixel is inside
                    if all(counter_clockwise_values) or not any(
                        counter_clockwise_values
                    ):
                        self.set_color(mu2d.Vector2D(x, y), color)
                except RuntimeWarning:
                    # if any of the Vectors are 0, nothing to do with that pixel
                    pass
