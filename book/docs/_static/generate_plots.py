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

if __name__ != "__main__":
    sys.exit(0)

matplotlib.use("agg")

import doctest

# TODO, generalize to any number of dimensions
def accumulate_transformation(procedures, forwards=True):
    """Given a pipeline of functions, provide all intermediate results via a function.

    >>> fs = [mplt.translate(0,10),
    ...       mplt.translate(5,0)]
    >>> f = accumulate_transformation(fs, forwards=False)
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
    >>> f = accumulate_transformation(fs, forwards=True)
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

    # without this function, accumulate_transformation
    # would have an error in it, because of scope in a nested
    # function being retained.  I should figure out what is actually
    # happening there.
    def python_scoping_is_dumb(r, procedures):
        def foo(x, y):
            result_x, result_y = x, y
            for current_fn_index in r:
                result_x, result_y = procedures[current_fn_index](
                    result_x, result_y
                )
            return result_x, result_y

        return foo

    def id(x, y):
        return x, y

    yield id, len(procedures)

    if forwards:
        for number_of_fns_to_apply_this_round in [
            x + 1 for x in range(len(procedures))
        ]:
            yield (
                python_scoping_is_dumb(
                    range(number_of_fns_to_apply_this_round), procedures
                ),
                len(procedures) - number_of_fns_to_apply_this_round,
            )
    else:
        reversed_procs = list(range(len(procedures)))
        reversed_procs.reverse()
        for proc_index in reversed_procs:
            yield (
                python_scoping_is_dumb(
                    range(proc_index, len(procedures)), procedures
                ),
                proc_index,
            )


modules = [sys.modules[__name__]]
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
    forwards=True,
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
    procs = list(reversed(procs))
    # when plotting the transformations is forwards order, show the axis
    # at the last step first before plotting the data

    def idProc(x, y):
        return (x, y)

    if forwards:
        procs.append(idProc)
        procs.append(idProc)
    else:
        procs.insert(0, idProc)

    # create a single frame of the animated gif
    def create_single_frame(accumfn, stepsRemaining, fn, frame_number):
        for round_number in [1] if not forwards else [1, 2]:
            fig, axes = plt.subplots()
            axes.set_xlim([-graph_bounds[0], graph_bounds[0]])
            axes.set_ylim([-graph_bounds[1], graph_bounds[1]])

            # plot transformed basis
            for xs, ys, thickness in generategridlines.generategridlines(
                graph_bounds, interval=gridline_interval
            ):
                if (not forwards) and stepsRemaining > 1:
                    transformed_xs, transformed_ys = accumfn(xs, ys)
                elif (forwards) and round_number == 1 and frame_number != 1:
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
            if (not forwards) and stepsRemaining > 1:
                transformed_xs, transformed_ys = accumfn(
                    [0.0, unit_x], [0.0, 0.0]
                )
            elif (forwards) and round_number == 1 and frame_number != 1:
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
            if (not forwards) and stepsRemaining > 1:
                transformed_xs, transformed_ys = accumfn(
                    [0.0, 0.0], [0.0, unit_y]
                )
            elif (forwards) and round_number == 1 and frame_number != 1:
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
            accumulate_transformation(procs, forwards),
            [procs[0], *procs],
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
    procedures=[mplt.translate(-9.0, 2.0)],
    forwards=True,
)


create_graphs(
    title="Translation",
    filename="translation2-forwards",
    geometry=paddle2,
    procedures=[mplt.translate(9.0, -4.0)],
    forwards=True,
)

create_graphs(
    title="Translation",
    filename="translation-backwards",
    geometry=paddle1,
    procedures=[mplt.translate(-9.0, 2.0)],
    forwards=False,
)


create_graphs(
    title="Translation",
    filename="translation2-backwards",
    geometry=paddle2,
    procedures=[mplt.translate(9.0, -4.0)],
    forwards=False,
)

create_graphs(
    title="Rotation Relative to World Space",
    filename="rotate0",
    geometry=paddle1,
    procedures=[
        mplt.rotate(math.radians(45.0)),
    ],
    graph_bounds=(12, 12),
    forwards=True,
)


create_graphs(
    title="Scale Relative to World Space",
    filename="scale",
    geometry=paddle1,
    procedures=[
        mplt.scale(2.0, 3.0),
    ],
    forwards=True,
)


create_graphs(
    title="Rotation, Relative to World Space",
    filename="rotate1-forwards",
    geometry=paddle1,
    procedures=[
        mplt.translate(-9.0, 2.0),
        mplt.rotate(math.radians(45.0)),
    ],
    graph_bounds=(12, 12),
    forwards=True,
)

create_graphs(
    title="Incorrect Rotation, Relative to World Space",
    filename="incorrectrotate-forwards",
    geometry=paddle1,
    procedures=[
        mplt.rotate(math.radians(65.0)),
        mplt.translate(-9.0, 2.0),
    ],
    graph_bounds=(12, 12),
    forwards=True,
)

create_graphs(
    title="Incorrect Rotation, Relative to Local Space",
    filename="incorrectrotate-backwards",
    geometry=paddle1,
    procedures=[
        mplt.rotate(math.radians(65.0)),
        mplt.translate(-9.0, 2.0),
    ],
    forwards=False,
    graph_bounds=(12, 12),
)


create_graphs(
    title="Correct but Sloppy Rotation, Relative to Local Space",
    filename="rotate-sloppy-backwards",
    geometry=paddle1,
    procedures=[
        mplt.translate(-9.0, 2.0),
        mplt.rotate(math.radians(45.0)),
        mplt.translate(9.0, -2.0),
        mplt.translate(-9.0, 2.0),

    ],
    forwards=True,
    graph_bounds=(12, 12),
)

create_graphs(
    title="Correct but Sloppy Rotation, Relative to World Space",
    filename="rotate-sloppy-forwards",
    geometry=paddle1,
    procedures=[
        mplt.translate(-9.0, 2.0),
        mplt.rotate(math.radians(45.0)),
        mplt.translate(9.0, -2.0),
        mplt.translate(-9.0, 2.0),
    ],
    graph_bounds=(12, 12),
    forwards=True,
)


create_graphs(
    title="Rotation, Relative to Local Space",
    filename="rotate1-backwards",
    geometry=paddle1,
    procedures=[
        mplt.translate(-9.0, 2.0),
        mplt.rotate(math.radians(45.0)),
    ],
    graph_bounds=(12, 12),
    forwards=False,
)


create_graphs(
    title="Rotation, Relative to World Space",
    filename="rotate2-forwards",
    geometry=paddle2,
    procedures=[mplt.translate(9.0, -4.0), mplt.rotate(math.radians(-1.0))],
    graph_bounds=(12, 12),
    forwards=True,
)

create_graphs(
    title="Rotation, Relative to Local Space",
    filename="rotate2-backwards",
    geometry=paddle2,
    procedures=[
        mplt.translate(9.0, -4.0),
        mplt.rotate(math.radians(-1.0)),
    ],
    graph_bounds=(12, 12),
    forwards=False,
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
        mplt.rotate(math.radians(-45.0)),
        mplt.scale(scaleX=2.0, scaleY=4.5),
        mplt.rotate(math.radians(45.0)),
    ],
    forwards=False,
)

create_graphs(
    title="Covariance, Relative to World Space",
    filename="covariance-forwards",
    geometry=square,
    procedures=[
        mplt.rotate(math.radians(-45.0)),
        mplt.scale(scaleX=2.0, scaleY=4.5),
        mplt.rotate(math.radians(45.0)),
    ],
    forwards=True,
)


t = np.linspace(0, np.pi * 2, 100)
circ = [list(np.cos(t) * 10), list(np.sin(t) * 10)]
circle = Geometry(points=circ, color=(0.0, 1.0, 0.0), names=[])

create_graphs(
    title="Circle, Relative to Local Space",
    filename="circle-backwards",
    geometry=circle,
    procedures=[
        mplt.rotate(math.radians(-45.0)),
        mplt.scale(scaleX=2.0, scaleY=4.5),
        mplt.rotate(math.radians(45.0)),
    ],
    forwards=False,
)

create_graphs(
    title="Circle, Relative to World Space",
    filename="circle-forwards",
    geometry=circle,
    procedures=[
        mplt.rotate(math.radians(-45.0)),
        mplt.scale(scaleX=2.0, scaleY=4.5),
        mplt.rotate(math.radians(45.0)),
    ],
    forwards=True,
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
        mplt.scale(scaleX=1.0 / 2.0, scaleY=7.0 / 2.0),
        mplt.translate(1.0 / 2, 7.0 / 2),
    ],
    forwards=False,
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
        mplt.scale(scaleX=1.0 / 2.0, scaleY=7.0 / 2.0),
        mplt.translate(1.0 / 2, 7.0 / 2),
    ],
    forwards=True,
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
        mplt.translate(-1.0 / 2, -7.0 / 2),
        mplt.scale(scaleX=1.0 / (1.0 / 2.0), scaleY=1.0 / (7.0 / 2.0)),
    ],
    forwards=False,
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
        mplt.translate(-1.0 / 2, -7.0 / 2),
        mplt.scale(scaleX=1.0 / (1.0 / 2.0), scaleY=1.0 / (7.0 / 2.0)),
    ],
    forwards=True,
    graph_bounds=(10, 10),
    gridline_interval=1,
    unit_x=1.0,
    unit_y=1.0,
)
