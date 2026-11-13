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

"""3D graphing calculator -- plot an authored ``f(x, y)`` as a surface.

A standalone program (run it by path).  It plots one of the first-class Python
surfaces in ``SURFACES`` -- written into this file -- as a height field; the
Surface menu picks which.  The window, the orbit camera, the wireframe/solid
mesh and the drawing are :func:`gacalc.gl.grapher3d.run`
(github.com/billsix/geometricalgebra).
"""

import math

from gacalc.gl import grapher3d


def _ripple(x: float, y: float) -> float:
    r: float = math.sqrt(x * x + y * y)
    return 2.0 * math.sin(r)


SURFACES: list[grapher3d.Surface] = [
    grapher3d.Surface(
        fn=lambda x, y: x * y / 4.0,
        label="saddle: x*y/4",
        color=(0.95, 0.55, 0.35),
        latex=r"z=\tfrac{xy}{4}",
    ),
    grapher3d.Surface(
        fn=lambda x, y: (x * x + y * y) / 8.0,
        label="paraboloid: (x^2+y^2)/8",
        color=(0.45, 0.8, 0.95),
        latex=r"z=\tfrac{x^2+y^2}{8}",
    ),
    grapher3d.Surface(
        fn=_ripple,
        label="ripple: 2 sin(r)",
        color=(0.6, 0.9, 0.5),
        latex=r"z=2\sin\sqrt{x^2+y^2}",
    ),
    grapher3d.Surface(
        fn=lambda x, y: math.sin(x) * math.cos(y),
        label="waves: sin(x) cos(y)",
        color=(0.9, 0.75, 0.45),
        latex=r"z=\sin(x)\cos(y)",
    ),
]

if __name__ == "__main__":
    grapher3d.run(SURFACES, title="3D Graphing Calculator")
