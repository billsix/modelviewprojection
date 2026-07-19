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


import typing

import numpy as np

extra_lines_multiplier = 3


def generategridlines(
    graph_bounds: tuple[int, int],
    interval: int = 1,
) -> typing.Iterator[tuple[list[float], list[float], int]]:
    for x in range(
        -graph_bounds[0] * extra_lines_multiplier,
        graph_bounds[0] * extra_lines_multiplier,
        interval,
    ):
        thickness = 4 if np.isclose(x, 0.0) else 1
        yield (
            [x, x],
            [
                -graph_bounds[1] * extra_lines_multiplier,
                graph_bounds[1] * extra_lines_multiplier,
            ],
            thickness,
        )

    for y in range(
        -graph_bounds[1] * extra_lines_multiplier,
        graph_bounds[1] * extra_lines_multiplier,
        interval,
    ):
        thickness = 4 if np.isclose(y, 0.0) else 1
        yield (
            [
                -graph_bounds[0] * extra_lines_multiplier,
                graph_bounds[0] * extra_lines_multiplier,
            ],
            [y, y],
            thickness,
        )
