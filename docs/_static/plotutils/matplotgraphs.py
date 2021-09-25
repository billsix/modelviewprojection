# Copyright (c) 2018-2020 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numpy as np
import matplotlib.pyplot as plt
import math
import sys
import itertools

import generategridlines
import mpltransformations as mplt

N = 50
x = np.random.rand(N) * 10
y = np.random.rand(N) * 10

plt.scatter(x, y)

graphBounds = (10, 10)

axes = plt.gca()
axes.set_xlim([-2.0, graphBounds[0]])
axes.set_ylim([-2.0, graphBounds[1]])


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
    for xs, ys, thickness in generategridlines.generategridlines(graphBounds):
        plt.plot(xs, ys, "k-", lw=thickness)

    # plot different basis
    for xs, ys, thickness in generategridlines.generategridlines(graphBounds):
        transformedXs, transformedYs = list(
            mplt.translate(
                2,
                2,
                *mplt.scale(
                    math.sqrt(8), math.sqrt(8), *mplt.rotate(math.radians(45.0), xs, ys)
                )
            )
        )
        plt.plot(transformedXs, transformedYs, "k-", lw=thickness)

    # make sure the x and y axis are equally proportional in screen space
    plt.gca().set_aspect("equal", adjustable="box")
    plt.show()
