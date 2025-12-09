# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Plot 2D


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

# %%
import math

from modelviewprojection.mathutils import (
    identity,
)
from modelviewprojection.mathutils1d import (
    Vector1D,
)
from modelviewprojection.mathutils2d import (
    Vector2D,
    compose,
    compose_intermediate_fns,
    inverse,
)
from modelviewprojection.mathutils2d import rotate as R
from modelviewprojection.mathutils2d import scale as S
from modelviewprojection.mathutils2d import translate as T
from modelviewprojection.mathutils3d import (
    Vector3D,
)
from modelviewprojection.nbplotutils import (
    create_basis,
    create_graphs,
    create_unit_circle,
    create_x_and_y,
    draw_screen,
    draw_triangle,
)

# %%
T(Vector1D(5))

# %%
S(5, 6)

# %%
inverse(T(Vector1D(5)))

# %%
T(Vector2D(5, 6))

# %%
T(Vector3D(5, 6, 7))

# %%
inverse(T(Vector3D(5, 6, 7)))

# %%
R(math.pi / 2)

# %%
compose([R(math.pi / 2), T(Vector2D(5, 6))])

# %%
inverse(compose([R(math.pi / 2), T(Vector2D(5, 6))]))

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
fn = R(math.radians(53.130102))
with create_graphs() as axes:
    create_basis(fn=fn)
    create_x_and_y(fn=fn)
    create_unit_circle(fn=fn)
    axes.set_title(fn._repr_latex_())


# %% [markdown]
# Draw relative graph paper
# -------------------------
#
# Draw two relative number lines, making a relative graph paper,
# but keep the original coordinate system on the left and bottom.
# Any point in the plane can be described using two different
# graph papers.

# %%
fn = R(math.radians(45.0))
with create_graphs() as axes:
    create_basis(fn=R(0.0))
    create_x_and_y(fn=R(0.0))
    create_basis(
        fn=fn,
        xcolor=(0, 1, 0),
        ycolor=(1, 1, 0),
    )
    create_x_and_y(
        fn=R(math.radians(45.0)),
        xcolor=(0, 1, 0),
        ycolor=(1, 1, 0),
    )
    create_unit_circle(fn=fn)
    axes.set_title(fn._repr_latex_())

# %% [markdown]
# Draw relative graph paper, defined by composed functions
# --------------------------------------------------------
#
# Draw a translated and rotated graph paper.
# You can read the sequence of composed functions
# in the order that they are applied, or in reverse order

# %%
fn = compose(
    [
        R(math.radians(90.0)),
        T(Vector2D(x=2.0, y=0.0)),
    ]
)
with create_graphs() as axes:
    create_basis(
        fn=fn,
    )
    create_x_and_y(fn=fn)
    create_unit_circle(fn=fn)
    axes.set_title(fn._repr_latex_())

# %% [markdown]
# Composed functions, read bottom up
# ----------------------------------
#
# The sequence of functions shown, where the translate
# is applied first, and operations are relative to the
# units on the left and bottom.

# %%
for f in compose_intermediate_fns(
    [R(math.radians(90.0)), T(Vector2D(x=1.0, y=0.0)), identity()]
):
    # TODO - figure out if I can render the latex as part of one markdown command,
    # if I were to uncomment out this line and other markdown lines,
    # the build of HTML would fail

    with create_graphs() as axes:
        create_basis(fn=f)
        create_x_and_y(fn=f)
        draw_triangle(fn=f)
        create_unit_circle(fn=f)
        axes.set_title(f._repr_latex_())

# %% [markdown]
# Composed functions, read top down
# ---------------------------------
#
# The sequence of functions shown, where we visualize
# the rotate first, and then the translate relative to
# that relative graph paper.
#

# %%
for f in compose_intermediate_fns(
    [
        identity(),
        R(math.radians(90.0)),
        T(Vector2D(x=1.0, y=0.0)),
    ],
    relative_basis=True,
):
    with create_graphs() as axes:
        create_basis(fn=f)
        create_x_and_y(fn=f)
        draw_triangle(fn=f)
        create_unit_circle(fn=f)
        axes.set_title(f._repr_latex_())
# %%
screen_width = 4
screen_height = 3

for f in compose_intermediate_fns(
    [
        T(Vector2D(-0.5, -0.5)),
        S(screen_width, screen_height),
        S(0.5, 0.5),
        T(Vector2D(x=1.0, y=1.0)),
        identity(),
    ],
    relative_basis=False,
):
    with create_graphs(graph_bounds=(6, 6)) as axes:
        # create_basis(fn=f)
        # create_x_and_y(fn=f)
        create_basis(fn=identity())
        # create_x_and_y(fn=identity())
        # draw_ndc(fn=f)
        draw_screen(width=screen_width, height=screen_height, fn=f)
        axes.set_title(f._repr_latex_())
# %%
screen_width = 4
screen_height = 3

for f in compose_intermediate_fns(
    [
        identity(),
        T(Vector2D(-0.5, -0.5)),
        S(screen_width, screen_height),
        S(0.5, 0.5),
        T(Vector2D(x=1.0, y=1.0)),
    ],
    relative_basis=True,
):
    with create_graphs(graph_bounds=(6, 6)) as axes:
        # create_basis(fn=f)
        # create_x_and_y(fn=f)
        create_basis(fn=identity())
        # create_x_and_y(fn=identity())
        # draw_ndc(fn=f)
        draw_screen(width=screen_width, height=screen_height, fn=f)
        axes.set_title(f._repr_latex_())
# %%

# %%
