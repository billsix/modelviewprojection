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

"""Shared lighting / geometry helpers for the lighting-era demos.

These were duplicated verbatim across demo22/demo22a/demo23.  They are
introduced (and explained) where they first appear; later demos import them
from here instead of redefining them.
"""

import math
import typing

from gacalc.g3 import Vector3

from modelviewprojection.mathutils import find_normal


def _face_normal(
    a: typing.Sequence[float],
    b: typing.Sequence[float],
    c: typing.Sequence[float],
) -> tuple[float, float, float]:
    """Outward *unit* normal of triangle (a, b, c), CCW-wound.

    The cross product of two edges -- computed via
    :func:`modelviewprojection.mathutils.find_normal` -- then normalized.

    A triangle in the x-y plane wound counter-clockwise faces +z:

    >>> _face_normal((0, 0, 0), (1, 0, 0), (0, 1, 0))
    (0.0, 0.0, 1.0)

    Reversing the winding flips the normal to face the other way:

    >>> _face_normal((0, 0, 0), (0, 1, 0), (1, 0, 0))
    (0.0, 0.0, -1.0)

    A degenerate (zero-area) triangle has no normal; report zeros rather than
    divide by a zero magnitude:

    >>> _face_normal((0, 0, 0), (1, 0, 0), (2, 0, 0))
    (0.0, 0.0, 0.0)
    """
    n = find_normal(Vector3(*a), Vector3(*b), Vector3(*c))
    mag = abs(n)
    return tuple((1.0 / mag) * n) if mag else (0.0, 0.0, 0.0)


def light_dir_ws(az_deg: float, el_deg: float) -> tuple[float, float, float]:
    """Unit direction to a light, from azimuth + elevation in **degrees**.

    Azimuth sweeps the x-z plane from +x toward +z; elevation lifts toward +y.
    So the three cardinal directions read off directly:

    >>> def rounded(v):
    ...     return tuple(round(c, 6) for c in v)
    >>> rounded(light_dir_ws(0, 0))       # azimuth 0, on the horizon -> +x
    (1.0, 0.0, 0.0)
    >>> rounded(light_dir_ws(90, 0))      # quarter turn in azimuth -> +z
    (0.0, 0.0, 1.0)
    >>> rounded(light_dir_ws(0, 90))      # straight up -> +y
    (0.0, 1.0, 0.0)

    Halfway up at azimuth 0 splits evenly between +x and +y:

    >>> rounded(light_dir_ws(0, 45))
    (0.707107, 0.707107, 0.0)

    The result is always unit length -- it is a direction, not a position:

    >>> x, y, z = light_dir_ws(37, 52)
    >>> round((x * x + y * y + z * z) ** 0.5, 6)
    1.0
    """
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    return (
        math.cos(el) * math.cos(az),
        math.sin(el),
        math.cos(el) * math.sin(az),
    )
