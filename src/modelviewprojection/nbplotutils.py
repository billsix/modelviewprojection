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


import contextlib
import math

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
from matplotlib.patches import Polygon
from matplotlib_inline.backend_inline import set_matplotlib_formats

import modelviewprojection.mathutils2d as mu2d

set_matplotlib_formats("svg")

extraLinesMultiplier = 3


def generategridlines(graphBounds, interval=1):
    for x in range(
        -graphBounds[0] * extraLinesMultiplier,
        graphBounds[0] * extraLinesMultiplier,
        interval,
    ):
        thickness = 4 if np.isclose(x, 0.0) else 1
        yield (
            [
                mu2d.Vector2D(x, -graphBounds[1] * extraLinesMultiplier),
                mu2d.Vector2D(x, graphBounds[1] * extraLinesMultiplier),
            ],
            thickness,
        )

    for y in range(
        -graphBounds[1] * extraLinesMultiplier,
        graphBounds[1] * extraLinesMultiplier,
        interval,
    ):
        thickness = 4 if np.isclose(y, 0.0) else 1
        yield (
            [
                mu2d.Vector2D(-graphBounds[0] * extraLinesMultiplier, y),
                mu2d.Vector2D(graphBounds[0] * extraLinesMultiplier, y),
            ],
            thickness,
        )


axes = None


@contextlib.contextmanager
def create_graphs(graph_bounds=(3, 3), title=None, filename=None):
    global axes
    fig, axes = plt.subplots(figsize=(3, 3))
    axes.set_xlim([-graph_bounds[0], graph_bounds[0]])
    axes.set_ylim([-graph_bounds[1], graph_bounds[1]])

    plt.tight_layout()
    yield

    # make sure the x and y axis are equally proportional in screen space
    plt.gca().set_aspect("equal", adjustable="box")
    axes.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
    axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
    fig.canvas.draw()
    np.array(fig.canvas.renderer.buffer_rgba())
    return fig


def create_basis(
    fn=lambda x: x,
    graph_bounds=(10, 10),
    gridline_interval=1,
    xcolor=(0.0, 0.0, 1.0),
    ycolor=(1.0, 0.0, 1.0),
):
    # plot transformed basis
    for vecs, thickness in generategridlines(
        graph_bounds, interval=gridline_interval
    ):
        plt.plot(
            [fn(vec).x for vec in vecs],
            [fn(vec).y for vec in vecs],
            "-",
            lw=thickness,
            color=(0.1, 0.2, 0.5),
            alpha=0.3,
        )

        # x axis
        x_axis = [mu2d.Vector2D(0, 0), mu2d.Vector2D(1, 0)]
        plt.plot(
            [fn(vec).x for vec in x_axis],
            [fn(vec).y for vec in x_axis],
            "-",
            lw=1.0,
            color=xcolor,
        )

        # y axis
        y_axis = [mu2d.Vector2D(0, 0), mu2d.Vector2D(0, 1)]
        plt.plot(
            [fn(vec).x for vec in y_axis],
            [fn(vec).y for vec in y_axis],
            "-",
            lw=1.0,
            color=ycolor,
        )

    def generate_circle():
        theta_increment: float = 0.01
        scale_radius: float = 1.0

        for theta in np.arange(0.0, 2 * math.pi, theta_increment):
            yield (
                [
                    scale_radius
                    * mu2d.Vector2D(math.cos(theta), math.sin(theta)),
                    scale_radius
                    * mu2d.Vector2D(
                        math.cos(theta + theta_increment),
                        math.sin(theta + theta_increment),
                    ),
                ]
            )

    # plot transformed basis
    for vecs in generate_circle():
        plt.plot(
            [fn(vec).x for vec in vecs],
            [fn(vec).y for vec in vecs],
            "-",
            lw=1,
            color=(0.0, 0.0, 0.0),
            alpha=0.5,
        )


def draw_triangle(
    fn=lambda x: x,
    color=(0.0, 0.0, 1.0),
):
    vertices = [
        fn(v)
        for v in [
            mu2d.Vector2D(0.0, 0.0),
            mu2d.Vector2D(1.0, 0.0),
            mu2d.Vector2D(0.5, 1.0),
        ]
    ]

    triangle = Polygon(
        list(map(list, vertices)),
        closed=True,
        facecolor="lightblue",
        edgecolor="black",
    )
    axes.add_patch(triangle)

    vertices_as_np = np.array(list(map(list, vertices)))
    # Plot dots at the vertices
    axes.scatter(
        vertices_as_np[:, 0], vertices_as_np[:, 1], color="red", s=50, zorder=5
    )  # zorder ensures dots are on top

    # Label each vertex
    labels = ["A", "B", "C"]
    for i, label in enumerate(labels):
        # Use plt.annotate to place the label near the point
        plt.annotate(
            label,
            (vertices_as_np[i, 0], vertices_as_np[i, 1]),
            xytext=(5, 5),
            textcoords="offset points",
            ha="left",
            va="bottom",
        )
