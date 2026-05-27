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

from modelviewprojection.mathutils import Vector3D, find_normal


def _face_normal(a, b, c) -> tuple[float, float, float]:
    """Outward *unit* normal of triangle (a, b, c), CCW-wound.

    The cross product of two edges -- computed via
    :func:`modelviewprojection.mathutils.find_normal` -- then normalized.
    """
    n = find_normal(Vector3D(*a), Vector3D(*b), Vector3D(*c))
    mag = abs(n)
    return tuple((1.0 / mag) * n) if mag else (0.0, 0.0, 0.0)


def light_dir_ws(az_deg: float, el_deg: float) -> tuple[float, float, float]:
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    return (
        math.cos(el) * math.cos(az),
        math.sin(el),
        math.cos(el) * math.sin(az),
    )
