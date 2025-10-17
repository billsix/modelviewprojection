# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
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


# %% [markdown]
# Problem 1
# ---------
#
# Foobar

# %%

import contextlib
import math

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

import modelviewprojection.mathutils as mu
import modelviewprojection.mathutils2d as mu2d

extraLinesMultiplier = 3

# %%


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


# %%


@contextlib.contextmanager
def create_graphs(graph_bounds=(3, 3), title=None, filename=None):
    try:
        fig, axes = plt.subplots(figsize=(3, 3))
        axes.set_xlim([-graph_bounds[0], graph_bounds[0]])
        axes.set_ylim([-graph_bounds[1], graph_bounds[1]])

        plt.tight_layout()
        yield
    finally:
        # make sure the x and y axis are equally proportional in screen space
        plt.gca().set_aspect("equal", adjustable="box")
        axes.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
        axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
        fig.canvas.draw()
        np.array(fig.canvas.renderer.buffer_rgba())
        return fig


# %%
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


# %% [markdown]
# Draw graph paper
# ----------------
#
# Just draw graph paper, where one unit in the x direction is blue,
# and one unit in the y direction is pink.  The graph paper corresponds
# to the numbers on the left and on the bottom.
#
#

# %%
with create_graphs():
    create_basis()

# %%

with create_graphs():
    create_basis(fn=mu2d.rotate(math.radians(53.130102)))

# %% [markdown]
# Draw relative graph paper
# -------------------------
#
# Draw two relative number lines, making a relative graph paper,
# but keep the original coordinate system on the left and bottom.
# Any point in the plane can be described using two different
# graph papers.
#
#

# %%
with create_graphs():
    create_basis(fn=mu2d.rotate(0.0))
    create_basis(
        fn=mu2d.rotate(math.radians(53.130102)),
        xcolor=(0, 1, 0),
        ycolor=(0, 1, 1),
    )

# %% [markdown]
# Draw relative graph paper, defined by composed functions
# --------------------------------------------------------
#
# Draw a translated and rotated graph paper.
# You can read the sequence of composed functions
# in the order that they are applied, or in reverse order

# %%
with create_graphs():
    create_basis(
        fn=mu2d.compose(
            [
                mu2d.rotate(math.radians(53.130102)),
                mu2d.translate(mu2d.Vector2D(x=1.0, y=0.0)),
            ]
        ),
    )

# %% [markdown]
# Composed functions, read bottom up
# ----------------------------------
#
# The sequence of functions shown, where the translate
# is applied first, and operations are relative to the
# units on the left and bottom.

# %%
for f in mu.compose_intermediate_fns(
    [
        mu2d.rotate(math.radians(53.130102)),
        mu2d.translate(mu2d.Vector2D(x=1.0, y=0.0)),
    ]
):
    with create_graphs():
        create_basis(fn=f)

# %% [markdown]
# Composed functions, read top down
# ---------------------------------
#
# The sequence of functions shown, where we visualize
# the rotate first, and then the translate relative to
# that relative graph paper.
#

# %%
for f in mu.compose_intermediate_fns(
    [
        mu2d.rotate(math.radians(53.130102)),
        mu2d.translate(mu2d.Vector2D(x=1.0, y=0.0)),
    ],
    relative_basis=True,
):
    with create_graphs():
        create_basis(fn=f)
