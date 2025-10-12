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
def create_graphs(title, filename, graph_bounds):
    try:
        fig, axes = plt.subplots(figsize=(6, 6))
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


def create_basis(graph_bounds, gridline_interval, fn=lambda x: x):
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
            color=(0.0, 0.0, 1.0),
        )

        # y axis
        y_axis = [mu2d.Vector2D(0, 0), mu2d.Vector2D(0, 1)]
        plt.plot(
            [fn(vec).x for vec in y_axis],
            [fn(vec).y for vec in y_axis],
            "-",
            lw=1.0,
            color=(1.0, 0.0, 1.0),
        )


# %%

with create_graphs("foo", "bar.txt", (10, 10)):
    create_basis((3, 3), 1)

# %%

with create_graphs(
    "foo",
    "bar.txt",
    (3, 3),
):
    create_basis((3, 3), 1, mu2d.rotate(math.radians(53.130102)))

# %%


with create_graphs("foo", "bar.txt", (3, 3)):
    create_basis((3, 3), 1, mu2d.rotate(0.0))
    create_basis((3, 3), 1, mu2d.rotate(math.radians(53.130102)))

# %%
with create_graphs("foo", "bar.txt", (3, 3)):
    create_basis(
        (3, 3),
        1,
        mu.compose(
            [
                mu2d.rotate(math.radians(53.130102)),
                mu.translate(mu2d.Vector2D(x=4.0, y=0.0)),
            ]
        ),
    )

# %%
