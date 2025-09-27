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

import itertools
import math
import sys
from collections import namedtuple

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import plotutils.generategridlines as generategridlines
import plotutils.mpltransformations as mplt
import modelviewprojection.mathutils as mu
import modelviewprojection.mathutils2d as mu2d
import doctest

if __name__ != "__main__":
    sys.exit(0)

matplotlib.use("agg")


def wrap_proc(f):
    def aoeu(xs, ys):
        results = [f(mu2d.Vector2D(x,y)) for x, y in zip(xs, ys)]
        return tuple([r.x for r in results]), tuple([r.y for r in results])
    return aoeu

# TODO, generalize to any number of dimensions
def accumulate_transformation(procedures, backwards=False):
    """Given a pipeline of functions, provide all intermediate results via a function.

    >>> fs = [mu.translate(mu2d.Vector2D(5,0)),
    ...       mu.translate(mu2d.Vector2D(0,10))]
    >>> f = accumulate_transformation(fs)
    >>> f1, stepsRemaining = next(f)
    >>> f1((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (4, 5, 6))
    >>> stepsRemaining
    2
    >>> f2, stepsRemaining = next(f)
    >>> f2((1, 2, 3), (4, 5, 6))
    ((6, 7, 8), (4, 5, 6))
    >>> stepsRemaining
    1
    >>> f3, stepsRemaining = next(f)
    >>> f3((1, 2, 3), (4, 5, 6))
    ((6, 7, 8), (14, 15, 16))
    >>> stepsRemaining
    0
    >>> f1((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (4, 5, 6))
    >>> f = accumulate_transformation(fs, backwards=True)
    >>> f1, stepsRemaining = next(f)
    >>> f1((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (4, 5, 6))
    >>> stepsRemaining
    2
    >>> f2, stepsRemaining = next(f)
    >>> f2((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (14, 15, 16))
    >>> stepsRemaining
    1
    >>> f3, stepsRemaining = next(f)
    >>> f3((1, 2, 3), (4, 5, 6))
    ((6, 7, 8), (14, 15, 16))
    >>> stepsRemaining
    0
    >>> f1((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (4, 5, 6))


    """
    fns = mu.compose_(*procedures, relative_basis=(not backwards))
    fn_count = len(fns)

    def id(x, y):
        return x, y

    yield id, len(procedures)
    for f, remaining in zip(fns, reversed(range(fn_count))):
        yield wrap_proc(f), remaining




modules = [sys.modules[__name__]]
#modules = [mplt, sys.modules[__name__]]
for m in modules:
    try:
        doctest.testmod(m, raise_on_error=True)
        print(doctest.testmod(m))
    except Exception:
        print(doctest.testmod(m))
        sys.exit(1)
## Translation Plots


## Translation Plots - reading the transformations forward

### Step 1

Geometry = namedtuple("Geometry", "points color names")

paddle1 = Geometry(
    points=list(
        zip(
            *np.array(
                [
                    [-1.0, -3.0],
                    [1.0, -3.0],
                    [1.0, 3.0],
                    [-1.0, 3.0],
                    [-1.0, -3.0],
                ]
            )
        )
    ),
    color=(0.578123, 0.0, 1.0),
    names=["c", "d", "a", "b"],
)

paddle2 = Geometry(
    points=list(
        zip(
            *np.array(
                [
                    [-1.0, -3.0],
                    [1.0, -3.0],
                    [1.0, 3.0],
                    [-1.0, 3.0],
                    [-1.0, -3.0],
                ]
            )
        )
    ),
    color=(1.0, 0.0, 0.0),
    names=["c", "d", "a", "b"],
)


def create_graphs(
    title,
    filename,
    geometry,
    procedures,
    backwards=False,
    graph_bounds=(10, 10),
    gridline_interval=1,
    unit_x=1.0,
    unit_y=1.0,
):
    """Creates an animated dif of the geometry, through a sequence of transformations"""

    fig, axes = plt.subplots()
    axes.set_xlim([-graph_bounds[0], graph_bounds[0]])
    axes.set_ylim([-graph_bounds[1], graph_bounds[1]])

    procs = procedures.copy()
    # when plotting the transformations is backwards order, show the axis
    # at the last step first before plotting the data

    def idProc(x): return x

    if backwards:
        procs.insert(0, idProc)
        procs.insert(0, idProc)
    else:
        procs.append(idProc)

    # create a single frame of the animated gif
    def create_single_frame(accumfn, stepsRemaining, fn, frame_number):
        for round_number in [1] if backwards else [1, 2]:
            fig, axes = plt.subplots()
            axes.set_xlim([-graph_bounds[0], graph_bounds[0]])
            axes.set_ylim([-graph_bounds[1], graph_bounds[1]])

            # plot transformed basis
            for xs, ys, thickness in generategridlines.generategridlines(
                graph_bounds, interval=gridline_interval
            ):
                if backwards and stepsRemaining > 1:
                    transformed_xs, transformed_ys = accumfn(xs, ys)
                elif not backwards and round_number == 1 and frame_number != 1:
                    transformed_xs, transformed_ys = fn(xs, ys)
                else:
                    transformed_xs, transformed_ys = xs, ys
                plt.plot(
                    transformed_xs,
                    transformed_ys,
                    "-",
                    lw=thickness,
                    color=(0.1, 0.2, 0.5),
                    alpha=0.3,
                )

            # x axis
            if backwards and stepsRemaining > 1:
                transformed_xs, transformed_ys = accumfn(
                    [0.0, unit_x], [0.0, 0.0]
                )
            elif not backwards and round_number == 1 and frame_number != 1:
                transformed_xs, transformed_ys = fn([0.0, unit_x], [0.0, 0.0])
            else:
                transformed_xs, transformed_ys = [0.0, unit_x], [0.0, 0.0]
            plt.plot(
                transformed_xs,
                transformed_ys,
                "-",
                lw=1.0,
                color=(0.0, 0.0, 1.0),
            )

            # y axis
            if backwards and stepsRemaining > 1:
                transformed_xs, transformed_ys = accumfn(
                    [0.0, 0.0], [0.0, unit_y]
                )
            elif not backwards and round_number == 1 and frame_number != 1:
                transformed_xs, transformed_ys = fn([0.0, 0.0], [0.0, unit_y])
            else:
                transformed_xs, transformed_ys = [0.0, 0.0], [0.0, unit_y]
            plt.plot(
                transformed_xs,
                transformed_ys,
                "-",
                lw=1.0,
                color=(1.0, 0.0, 1.0),
            )

            if stepsRemaining <= 0:
                plotCharacter = "-"
            else:
                plotCharacter = "."
            # plot the points
            transformed_xs, transformed_ys = accumfn(*geometry.points)
            plt.title(str.format("{}\nStep {}", title, str(frame_number)))
            plt.plot(
                transformed_xs,
                transformed_ys,
                plotCharacter,
                lw=2,
                color=geometry.color,
            )

            for x, y, label in zip(
                transformed_xs, transformed_ys, geometry.names
            ):
                plt.annotate(
                    f"{label}",
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                )

            # make sure the x and y axis are equally proportional in screen space
            plt.gca().set_aspect("equal", adjustable="box")
            axes.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
            axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
            fig.canvas.draw()
            np.array(fig.canvas.renderer.buffer_rgba())
            yield fig

    # create a single frame
    animated_images_list = [
        create_single_frame(accumfn, stepsRemaining, fn, frame_number)
        for (accumfn, stepsRemaining), fn, frame_number in zip(
            accumulate_transformation(procs, backwards),
            [procs[0], *list(map(wrap_proc, procs))],
            itertools.count(start=1),
        )
    ]

    flattened_animated_images_list = list(
        itertools.chain(*animated_images_list)
    )

    for number, fig in enumerate(flattened_animated_images_list):
        fig.savefig("./" + filename + "-" + str(number) + ".svg", format="svg")
        plt.close(fig)


create_graphs(
    title="Translation",
    filename="translation-forwards",
    geometry=paddle1,
    procedures=[mu.translate(mu2d.Vector2D(-9.0, 2.0))],
)


create_graphs(
    title="Translation",
    filename="translation2-forwards",
    geometry=paddle2,
    procedures=[mu.translate(mu2d.Vector2D(9.0, -4.0))],
)

create_graphs(
    title="Translation",
    filename="translation-backwards",
    geometry=paddle1,
    procedures=[mu.translate(mu2d.Vector2D(-9.0, 2.0))],
    backwards=True,
)


create_graphs(
    title="Translation",
    filename="translation2-backwards",
    geometry=paddle2,
    procedures=[mu.translate(mu2d.Vector2D(9.0, -4.0))],
    backwards=True,
)

create_graphs(
    title="Rotation Relative to World Space",
    filename="rotate0",
    geometry=paddle1,
    procedures=[
        mu2d.rotate(math.radians(45.0)),
    ],
    graph_bounds=(12, 12),
)


create_graphs(
    title="Scale Relative to World Space",
    filename="scale",
    geometry=paddle1,
    procedures=[
        mu2d.scale(2.0, 3.0),
    ],
)


create_graphs(
    title="Rotation, Relative to World Space",
    filename="rotate1-forwards",
    geometry=paddle1,
    procedures=[
        mu2d.rotate(math.radians(45.0)),
        mu.translate(mu2d.Vector2D(-9.0, 2.0)),
    ],
    graph_bounds=(12, 12),
)

create_graphs(
    title="Incorrect Rotation, Relative to World Space",
    filename="incorrectrotate-forwards",
    geometry=paddle1,
    procedures=[
        mu.translate(mu2d.Vector2D(-9.0, 2.0)),
        mu2d.rotate(math.radians(65.0)),
    ],
    graph_bounds=(12, 12),
)

create_graphs(
    title="Incorrect Rotation, Relative to Local Space",
    filename="incorrectrotate-backwards",
    geometry=paddle1,
    procedures=[
        mu.translate(mu2d.Vector2D(-9.0, 2.0)),
        mu2d.rotate(math.radians(65.0)),
    ],
    backwards=True,
    graph_bounds=(12, 12),
)


create_graphs(
    title="Correct but Sloppy Rotation, Relative to Local Space",
    filename="rotate-sloppy-backwards",
    geometry=paddle1,
    procedures=[
        mu.translate(mu2d.Vector2D(-9.0, 2.0)),
        mu.translate(mu2d.Vector2D(9.0, -2.0)),
        mu2d.rotate(math.radians(45.0)),
        mu.translate(mu2d.Vector2D(-9.0, 2.0)),
    ],
    backwards=True,
    graph_bounds=(12, 12),
)

create_graphs(
    title="Correct but Sloppy Rotation, Relative to World Space",
    filename="rotate-sloppy-forwards",
    geometry=paddle1,
    procedures=[
        mu.translate(mu2d.Vector2D(-9.0, 2.0)),
        mu.translate(mu2d.Vector2D(9.0, -2.0)),
        mu2d.rotate(math.radians(45.0)),
        mu.translate(mu2d.Vector2D(-9.0, 2.0)),
    ],
    graph_bounds=(12, 12),
)


create_graphs(
    title="Rotation, Relative to Local Space",
    filename="rotate1-backwards",
    geometry=paddle1,
    procedures=[
        mu2d.rotate(math.radians(45.0)),
        mu.translate(mu2d.Vector2D(-9.0, 2.0)),
    ],
    backwards=True,
    graph_bounds=(12, 12),
)


create_graphs(
    title="Rotation, Relative to World Space",
    filename="rotate2-forwards",
    geometry=paddle2,
    procedures=[mu2d.rotate(math.radians(-1.0)), mu.translate(mu2d.Vector2D(9.0, -4.0))],
    graph_bounds=(12, 12),
)

create_graphs(
    title="Rotation, Relative to Local Space",
    filename="rotate2-backwards",
    geometry=paddle2,
    procedures=[
        mu2d.rotate(math.radians(-1.0)),
        mu.translate(mu2d.Vector2D(9.0, -4.0)),
    ],
    backwards=True,
    graph_bounds=(12, 12),
)

square = Geometry(
    points=list(
        zip(
            *np.array(
                [
                    [-1.0, -1.0],
                    [1.0, -1.0],
                    [1.0, 1.0],
                    [-1.0, 1.0],
                    [-1.0, -1.0],
                ]
            )
        )
    ),
    color=(1.0, 0.0, 0.0),
    names=["c", "d", "a", "b"],
)


create_graphs(
    title="Covariance, Relative to Local Space",
    filename="covariance-backwards",
    geometry=square,
    procedures=[
        mu2d.rotate(math.radians(-45.0)),
        mu2d.scale(2.0, 4.5),
        mu2d.rotate(math.radians(45.0)),
    ],
    backwards=True,
)

create_graphs(
    title="Covariance, Relative to World Space",
    filename="covariance-forwards",
    geometry=square,
    procedures=[
        mu2d.rotate(math.radians(-45.0)),
        mu2d.scale(2.0, 4.5),
        mu2d.rotate(math.radians(45.0)),
    ],
    backwards=False,
)


t = np.linspace(0, np.pi * 2, 100)
circ = [list(np.cos(t) * 10), list(np.sin(t) * 10)]
circle = Geometry(points=circ, color=(0.0, 1.0, 0.0), names=[])

create_graphs(
    title="Circle, Relative to Local Space",
    filename="circle-backwards",
    geometry=circle,
    procedures=[
        mu2d.rotate(math.radians(-45.0)),
        mu2d.scale(2.0, 4.5),
        mu2d.rotate(math.radians(45.0)),
    ],
    backwards=True,
)

create_graphs(
    title="Circle, Relative to World Space",
    filename="circle-forwards",
    geometry=circle,
    procedures=[
        mu2d.rotate(math.radians(-45.0)),
        mu2d.scale(2.0, 4.5),
        mu2d.rotate(math.radians(45.0)),
    ],
    backwards=False,
)


square_ndc = Geometry(
    points=list(
        zip(
            *np.array(
                [
                    [-1.0, -1.0],
                    [1.0, -1.0],
                    [1.0, 1.0],
                    [-1.0, 1.0],
                    [-1.0, -1.0],
                ]
            )
        )
    ),
    color=(1.0, 0.0, 0.0),
    names=[],
)


create_graphs(
    title="Inverse Ortho2d",
    filename="inverse-ortho2d-backwards",
    geometry=square_ndc,
    procedures=[
        mu2d.scale(1.0 / 2.0, 7.0 / 2.0),
        mu.translate(mu2d.Vector2D(1.0 / 2, 7.0 / 2)),
    ],
    backwards=True,
    graph_bounds=(10, 10),
    gridline_interval=1,
    unit_x=1.0,
    unit_y=1.0,
)

create_graphs(
    title="Inverse Ortho2d",
    filename="inverse-ortho2d",
    geometry=square_ndc,
    procedures=[
        mu2d.scale(1.0 / 2.0, 7.0 / 2.0),
        mplt.translate(1.0 / 2, 7.0 / 2),
    ],
    backwards=False,
    graph_bounds=(10, 10),
    gridline_interval=1,
    unit_x=1.0,
    unit_y=1.0,
)


square_ndc = Geometry(
    points=list(
        zip(
            *np.array(
                [
                    [0.0, 0.0],
                    [1.0, 0.0],
                    [1.0, 7.0],
                    [0.0, 7.0],
                    [0.0, 0.0],
                ]
            )
        )
    ),
    color=(1.0, 0.0, 0.0),
    names=[],
)


create_graphs(
    title="Ortho2d",
    filename="ortho2d-backwards",
    geometry=square_ndc,
    procedures=[
        mu.translate(mu2d.Vector2D(-1.0 / 2, -7.0 / 2)),
        mu2d.scale(1.0 / (1.0 / 2.0), 1.0 / (7.0 / 2.0)),
    ],
    backwards=True,
    graph_bounds=(10, 10),
    gridline_interval=1,
    unit_x=1.0,
    unit_y=1.0,
)

create_graphs(
    title="Ortho2d",
    filename="ortho2d",
    geometry=square_ndc,
    procedures=[
        mu.translate(mu2d.Vector2D(-1.0 / 2, -7.0 / 2)),
        mu2d.scale(1.0 / (1.0 / 2.0), 1.0 / (7.0 / 2.0)),
    ],
    backwards=False,
    graph_bounds=(10, 10),
    gridline_interval=1,
    unit_x=1.0,
    unit_y=1.0,
)
