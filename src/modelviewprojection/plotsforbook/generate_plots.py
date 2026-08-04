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

import doctest
import itertools
import math
import sys
from collections import namedtuple
from collections.abc import Iterator, Sequence

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
from gacalc.g2 import Vector2
from gacalc.transforms import (
    InvertibleFunction,
    compose_intermediate_fns,
    identity,
    scale_non_uniform,
    translate,
)

from modelviewprojection.mathutils import rotate
from modelviewprojection.plotsforbook.plotutils import generategridlines

matplotlib.use("agg")

#: One axis of a matplotlib point set: the parallel array of xs, or of ys.  A
#: 2-D point set is the pair ``(xs, ys)``.  The transforms themselves are gacalc
#: ``InvertibleFunction``s over :class:`Vector2`; ``_apply`` bridges the two
#: representations at the matplotlib boundary (like ``util.nbplotutils._xy``).
Axis = Sequence[float]


def _apply(
    fn: InvertibleFunction[Vector2], xs: Axis, ys: Axis
) -> tuple[list[float], list[float]]:
    """Apply the gacalc transform ``fn`` to matplotlib parallel arrays.

    Packs each ``(x, y)`` into a :class:`Vector2`, applies ``fn``, and reads the
    coordinates back out as parallel ``float`` lists.  The ``float`` casts guard
    against sympy ``Float`` coefficients leaking from a rotation (same reason as
    ``util.nbplotutils._xy``); a purely numeric pipeline stays numeric anyway.
    """
    vectors = [
        fn(float(x) * Vector2.e_1 + float(y) * Vector2.e_2)
        for x, y in zip(xs, ys)
    ]
    return (
        [float(v.coeff_e_1) for v in vectors],
        [float(v.coeff_e_2) for v in vectors],
    )


def _accumulate(
    procedures: list[InvertibleFunction[Vector2]], forwards: bool
) -> Iterator[tuple[InvertibleFunction[Vector2], int]]:
    """The per-frame "aggregate transform + steps remaining" sequence.

    Formerly the bespoke ``accumulate_transformation`` generator; gacalc's
    ``compose_intermediate_fns`` -- itself *ported from this book* -- yields the
    partial compositions.  The old ``forwards`` flag maps to its
    ``relative_basis``: ``forwards=True`` is the natural basis
    (``relative_basis=False``), ``forwards=False`` is ``relative_basis=True``.
    Validated frame-for-frame against the old generator's doctests (worst
    delta 1.8e-15) before it was deleted.  The list argument is
    ``reversed(procedures)`` because ``compose`` applies its list right-to-left
    while the old generator applied ``procs[0]`` first, and ``steps_remaining``
    is just ``len(procedures) - i`` (both old branches produced that identical
    countdown).
    """
    intermediates = compose_intermediate_fns(
        list(reversed(procedures)), relative_basis=not forwards
    )
    for i, aggregate_fn in enumerate(intermediates):
        yield aggregate_fn, len(procedures) - i


def main() -> None:
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
        title: str,
        filename: str,
        geometry: Geometry,
        procedures: list[InvertibleFunction[Vector2]],
        forwards: bool = True,
        graph_bounds: tuple[int, int] = (10, 10),
        gridline_interval: int = 1,
        unit_x: float = 1.0,
        unit_y: float = 1.0,
    ) -> None:
        """
        Creates an animated dif of the geometry, through a sequence of
        transformations
        """

        fig, axes = plt.subplots()
        axes.set_xlim((-graph_bounds[0], graph_bounds[0]))
        axes.set_ylim((-graph_bounds[1], graph_bounds[1]))

        procs = procedures.copy()
        procs = list(reversed(procs))
        # when plotting the transformations is forwards order, show the axis
        # at the last step first before plotting the data

        if forwards:
            procs.append(identity())
            procs.append(identity())
        else:
            procs.insert(0, identity())

        # create a single frame of the animated gif
        def create_single_frame(
            accumfn: InvertibleFunction[Vector2],
            steps_remaining: int,
            fn: InvertibleFunction[Vector2],
            frame_number: int,
        ) -> Iterator[plt.Figure]:
            for round_number in [1] if not forwards else [1, 2]:
                fig, axes = plt.subplots()
                axes.set_xlim((-graph_bounds[0], graph_bounds[0]))
                axes.set_ylim((-graph_bounds[1], graph_bounds[1]))

                # plot transformed basis
                for xs, ys, thickness in generategridlines.generategridlines(
                    graph_bounds, interval=gridline_interval
                ):
                    if (not forwards) and steps_remaining > 1:
                        transformed_xs, transformed_ys = _apply(accumfn, xs, ys)
                    elif (forwards) and round_number == 1 and frame_number != 1:
                        transformed_xs, transformed_ys = _apply(fn, xs, ys)
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
                if (not forwards) and steps_remaining > 1:
                    transformed_xs, transformed_ys = _apply(
                        accumfn, [0.0, unit_x], [0.0, 0.0]
                    )
                elif (forwards) and round_number == 1 and frame_number != 1:
                    transformed_xs, transformed_ys = _apply(
                        fn, [0.0, unit_x], [0.0, 0.0]
                    )
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
                if (not forwards) and steps_remaining > 1:
                    transformed_xs, transformed_ys = _apply(
                        accumfn, [0.0, 0.0], [0.0, unit_y]
                    )
                elif (forwards) and round_number == 1 and frame_number != 1:
                    transformed_xs, transformed_ys = _apply(
                        fn, [0.0, 0.0], [0.0, unit_y]
                    )
                else:
                    transformed_xs, transformed_ys = [0.0, 0.0], [0.0, unit_y]
                plt.plot(
                    transformed_xs,
                    transformed_ys,
                    "-",
                    lw=1.0,
                    color=(1.0, 0.0, 1.0),
                )

                if steps_remaining <= 0:
                    plot_character = "-"
                else:
                    plot_character = "."
                # plot the points
                transformed_xs, transformed_ys = _apply(
                    accumfn, *geometry.points
                )
                plt.title(str.format("{}\nStep {}", title, str(frame_number)))
                plt.plot(
                    transformed_xs,
                    transformed_ys,
                    plot_character,
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

                # make sure the x and y axis are equally proportional in screen
                # space
                plt.gca().set_aspect("equal", adjustable="box")
                axes.xaxis.set_major_locator(
                    matplotlib.ticker.MultipleLocator(1)
                )
                axes.yaxis.set_major_locator(
                    matplotlib.ticker.MultipleLocator(1)
                )
                fig.canvas.draw()
                np.array(fig.canvas.renderer.buffer_rgba())  # ty: ignore[unresolved-attribute]
                yield fig

        # create a single frame
        animated_images_list = [
            create_single_frame(accumfn, steps_remaining, fn, frame_number)
            for (accumfn, steps_remaining), fn, frame_number in zip(
                _accumulate(procs, forwards),
                [procs[0], *procs],
                itertools.count(start=1),
            )
        ]

        flattened_animated_images_list = list(
            itertools.chain(*animated_images_list)
        )

        for number, fig in enumerate(flattened_animated_images_list):
            fig.savefig(
                "./" + filename + "-" + str(number) + ".svg", format="svg"
            )
            plt.close(fig)

    create_graphs(
        title="Translation",
        filename="translation-forwards",
        geometry=paddle1,
        procedures=[translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2)],
        forwards=True,
    )

    create_graphs(
        title="Translation",
        filename="translation2-forwards",
        geometry=paddle2,
        procedures=[translate(b=9.0 * Vector2.e_1 + -4.0 * Vector2.e_2)],
        forwards=True,
    )

    create_graphs(
        title="Translation",
        filename="translation-backwards",
        geometry=paddle1,
        procedures=[translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2)],
        forwards=False,
    )

    create_graphs(
        title="Translation",
        filename="translation2-backwards",
        geometry=paddle2,
        procedures=[translate(b=9.0 * Vector2.e_1 + -4.0 * Vector2.e_2)],
        forwards=False,
    )

    create_graphs(
        title="Rotation Relative to World Space",
        filename="rotate0",
        geometry=paddle1,
        procedures=[
            rotate(math.radians(45.0)),
        ],
        graph_bounds=(12, 12),
        forwards=True,
    )

    create_graphs(
        title="Scale Relative to World Space",
        filename="scale",
        geometry=paddle1,
        procedures=[
            scale_non_uniform(2.0, 3.0),
        ],
        forwards=True,
    )

    create_graphs(
        title="Rotation, Relative to World Space",
        filename="rotate1-forwards",
        geometry=paddle1,
        procedures=[
            translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2),
            rotate(math.radians(45.0)),
        ],
        graph_bounds=(12, 12),
        forwards=True,
    )

    create_graphs(
        title="Incorrect Rotation, Relative to World Space",
        filename="incorrectrotate-forwards",
        geometry=paddle1,
        procedures=[
            rotate(math.radians(65.0)),
            translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2),
        ],
        graph_bounds=(12, 12),
        forwards=True,
    )

    create_graphs(
        title="Incorrect Rotation, Relative to Local Space",
        filename="incorrectrotate-backwards",
        geometry=paddle1,
        procedures=[
            rotate(math.radians(65.0)),
            translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2),
        ],
        forwards=False,
        graph_bounds=(12, 12),
    )

    create_graphs(
        title="Correct but Sloppy Rotation, Relative to Local Space",
        filename="rotate-sloppy-backwards",
        geometry=paddle1,
        procedures=[
            translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2),
            rotate(math.radians(45.0)),
            translate(b=9.0 * Vector2.e_1 + -2.0 * Vector2.e_2),
            translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2),
        ],
        forwards=True,
        graph_bounds=(12, 12),
    )

    create_graphs(
        title="Correct but Sloppy Rotation, Relative to World Space",
        filename="rotate-sloppy-forwards",
        geometry=paddle1,
        procedures=[
            translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2),
            rotate(math.radians(45.0)),
            translate(b=9.0 * Vector2.e_1 + -2.0 * Vector2.e_2),
            translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2),
        ],
        graph_bounds=(12, 12),
        forwards=True,
    )

    create_graphs(
        title="Rotation, Relative to Local Space",
        filename="rotate1-backwards",
        geometry=paddle1,
        procedures=[
            translate(b=-9.0 * Vector2.e_1 + 2.0 * Vector2.e_2),
            rotate(math.radians(45.0)),
        ],
        graph_bounds=(12, 12),
        forwards=False,
    )

    create_graphs(
        title="Rotation, Relative to World Space",
        filename="rotate2-forwards",
        geometry=paddle2,
        procedures=[
            translate(b=9.0 * Vector2.e_1 + -4.0 * Vector2.e_2),
            rotate(math.radians(-1.0)),
        ],
        graph_bounds=(12, 12),
        forwards=True,
    )

    create_graphs(
        title="Rotation, Relative to Local Space",
        filename="rotate2-backwards",
        geometry=paddle2,
        procedures=[
            translate(b=9.0 * Vector2.e_1 + -4.0 * Vector2.e_2),
            rotate(math.radians(-1.0)),
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
            rotate(math.radians(-45.0)),
            scale_non_uniform(2.0, 4.5),
            rotate(math.radians(45.0)),
        ],
        forwards=False,
    )

    create_graphs(
        title="Covariance, Relative to World Space",
        filename="covariance-forwards",
        geometry=square,
        procedures=[
            rotate(math.radians(-45.0)),
            scale_non_uniform(2.0, 4.5),
            rotate(math.radians(45.0)),
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
            rotate(math.radians(-45.0)),
            scale_non_uniform(2.0, 4.5),
            rotate(math.radians(45.0)),
        ],
        forwards=False,
    )

    create_graphs(
        title="Circle, Relative to World Space",
        filename="circle-forwards",
        geometry=circle,
        procedures=[
            rotate(math.radians(-45.0)),
            scale_non_uniform(2.0, 4.5),
            rotate(math.radians(45.0)),
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
            scale_non_uniform(1.0 / 2.0, 7.0 / 2.0),
            translate(b=1.0 / 2 * Vector2.e_1 + 7.0 / 2 * Vector2.e_2),
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
            scale_non_uniform(1.0 / 2.0, 7.0 / 2.0),
            translate(b=1.0 / 2 * Vector2.e_1 + 7.0 / 2 * Vector2.e_2),
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
            translate(b=-1.0 / 2 * Vector2.e_1 + -7.0 / 2 * Vector2.e_2),
            scale_non_uniform(1.0 / (1.0 / 2.0), 1.0 / (7.0 / 2.0)),
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
            translate(b=-1.0 / 2 * Vector2.e_1 + -7.0 / 2 * Vector2.e_2),
            scale_non_uniform(1.0 / (1.0 / 2.0), 1.0 / (7.0 / 2.0)),
        ],
        forwards=True,
        graph_bounds=(10, 10),
        gridline_interval=1,
        unit_x=1.0,
        unit_y=1.0,
    )
