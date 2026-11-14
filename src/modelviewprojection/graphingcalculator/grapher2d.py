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

"""2D graphing calculator -- plot authored ``f(x)`` functions.

A standalone program (run it by path).  It plots the first-class Python
functions in ``FUNCTIONS`` -- written into this file, graphing-calculator
style, not typed in at runtime; add one to the list to graph it too.  The
window, the pan/zoom view and the drawing are
:func:`gacalc.gl.grapher2d.run` (github.com/billsix/geometricalgebra).
"""

import math

from gacalc.gl import grapher2d

FUNCTIONS: list[grapher2d.PlottedFunction] = [
    grapher2d.PlottedFunction(
        fn=lambda x: math.sin(x),
        label="sin(x)",
        color=(0.95, 0.35, 0.35),
        latex=r"\sin(x)",
    ),
    grapher2d.PlottedFunction(
        fn=lambda x: math.cos(x),
        label="cos(x)",
        color=(0.35, 0.75, 0.95),
        latex=r"\cos(x)",
    ),
    grapher2d.PlottedFunction(
        fn=lambda x: 0.25 * x * x - 2.0,
        label="x^2/4 - 2",
        color=(0.55, 0.9, 0.5),
        latex=r"\tfrac{x^2}{4}-2",
    ),
    grapher2d.PlottedFunction(
        fn=lambda x: 0.05 * x * x * x,
        label="x^3/20",
        color=(0.95, 0.8, 0.4),
        latex=r"\tfrac{x^3}{20}",
    ),
]

if __name__ == "__main__":
    grapher2d.run(FUNCTIONS, title="2D Graphing Calculator")
