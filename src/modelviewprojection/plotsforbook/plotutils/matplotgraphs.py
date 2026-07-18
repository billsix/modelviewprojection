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

import math
import os
import sys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import modelviewprojection.plotsforbook.plotutils.mpltransformations as mplt
from modelviewprojection.plotsforbook.plotutils import generategridlines

# TkAgg needs an interactive display. Fall back to the headless Agg backend
# when there is none, so importing this module (and collecting its doctests)
# works in CI and in a container without X.
matplotlib.use("TkAgg" if os.environ.get("DISPLAY") else "Agg")

N = 50
x = np.random.rand(N) * 10
y = np.random.rand(N) * 10

plt.scatter(x, y)

graph_bounds = (10, 10)

axes = plt.gca()
axes.set_xlim((-2.0, graph_bounds[0]))
axes.set_ylim((-2.0, graph_bounds[1]))


if __name__ == "__main__":
    import doctest

    modules = [mplt]
    for m in modules:
        try:
            doctest.testmod(m, raise_on_error=True)
            print(doctest.testmod(m))
        except Exception:
            print(doctest.testmod())
            sys.exit(1)

    # plot natural basis
    for xs, ys, thickness in generategridlines.generategridlines(graph_bounds):
        plt.plot(xs, ys, "k-", lw=thickness)

    # plot different basis
    for xs, ys, thickness in generategridlines.generategridlines(graph_bounds):
        transformed_xs, transformed_ys = list(
            mplt.translate(2, 2)(
                *mplt.scale(math.sqrt(8), math.sqrt(8))(
                    *mplt.rotate(math.radians(45.0))(xs, ys)
                )
            )
        )
        plt.plot(transformed_xs, transformed_ys, "k-", lw=thickness)

    # make sure the x and y axis are equally proportional in screen space
    plt.gca().set_aspect("equal", adjustable="box")
    plt.show()
