# Copyright (c) 2018-2025 William Emerison Six
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

import modelviewprojection.mathutils as mu

# for ease of use in importing and using
from modelviewprojection.mathutils import (
    InvertibleFunction,
    Vector,
    compose,
    compose_intermediate_fns,
    compose_intermediate_fns_and_fn,
    inverse,
    translate,
    uniform_scale,
)


__all__ = [
    "Vector1D",
    "translate",
    "uniform_scale",
    "InvertibleFunction",
    "inverse",
    "compose",
    "compose_intermediate_fns",
    "compose_intermediate_fns_and_fn",
    "Vector",
]


# doc-region-begin define vector class
@dataclasses.dataclass
class Vector1D(mu.Vector):
    x: float  #: The value of the 1D mu.Vector
    # doc-region-end define vector class
