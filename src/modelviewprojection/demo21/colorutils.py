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


from dataclasses import dataclass
from typing import TypeVar

# doc-region-begin define invertible function
# Define a generic type variable
T = TypeVar("T")


@dataclass
class Color3:
    r: float
    g: float
    b: float


@dataclass
class Color4:
    r: float
    g: float
    b: float
    a: float
