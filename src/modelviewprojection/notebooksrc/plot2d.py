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

import sympy

from modelviewprojection.mathutils import (
    compose,
    compose_intermediate_fns,
    e_1,
    e_2,
    e_3,
    identity,
    inverse,
)
from modelviewprojection.mathutils import rotate as R
from modelviewprojection.mathutils import scale_non_uniform_2d as S
from modelviewprojection.mathutils import translate as T
from modelviewprojection.nbplotutils import (
    create_basis,
    create_graphs,
    create_unit_circle,
    create_x_and_y,
    draw_isoceles_triangle,
    draw_right_triangle,
    draw_screen,
    draw_second_right_triangle,
)

# %%
T(5 * e_1)

# %%
S(5, 6)

# %%
inverse(T(5 * e_1))

# %%
T(5 * e_1 + 6 * e_2)

# %%
T(5 * e_1 + 6 * e_2 + 7 * e_3)

# %%
inverse(T(5 * e_1 + 6 * e_2 + 7 * e_3))

# %%
R(sympy.pi / 2)

# %%
compose([R(sympy.pi / 2), T(5 * e_1 + 6 * e_2)])

# %%
inverse(compose([R(sympy.pi / 2), T(5 * e_1 + 6 * e_2)]))

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
with create_graphs(graph_bounds=(5, 5)) as axes:
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
fn = R(math.radians(53.130102))
with create_graphs(graph_bounds=(5, 5)) as axes:
    create_basis(fn=R(0.0))
    create_x_and_y(fn=R(0.0))
    create_basis(
        fn=fn,
        xcolor=(0, 1, 0),
        ycolor=(1, 1, 0),
    )
    create_x_and_y(
        fn=fn,
        xcolor=(0, 1, 0),
        ycolor=(1, 1, 0),
    )
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
fn = R(math.radians(53.130102))
with create_graphs(graph_bounds=(5, 5)) as axes:
    create_basis(fn=R(0.0))
    create_x_and_y(fn=R(0.0))
    create_basis(
        fn=fn,
        xcolor=(0, 1, 0),
        ycolor=(1, 1, 0),
    )
    create_x_and_y(
        fn=fn,
        xcolor=(0, 1, 0),
        ycolor=(1, 1, 0),
    )
    create_unit_circle(fn=fn)
    draw_right_triangle()
    draw_second_right_triangle()
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
        R(sympy.pi / 4),
        T(2.0 * e_1 + 0.0 * e_2),
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
for f in compose_intermediate_fns([R(sympy.pi / 4), T(2.0 * e_1 + 0.0 * e_2)]):
    # TODO - figure out if I can render the latex as part of one markdown command,
    # if I were to uncomment out this line and other markdown lines,
    # the build of HTML would fail

    with create_graphs() as axes:
        create_basis(fn=f)
        create_x_and_y(fn=f)
        create_x_and_y()
        draw_isoceles_triangle(fn=f)
        create_unit_circle(fn=f)
        create_unit_circle()
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
        R(sympy.pi / 4),
        T(1.0 * e_1),
    ],
    relative_basis=True,
):
    with create_graphs() as axes:
        create_basis(fn=f)
        create_x_and_y(fn=f)
        draw_isoceles_triangle(fn=f)
        create_unit_circle(fn=f)
        axes.set_title(f._repr_latex_())
# %%
screen_width: int = 4
screen_height: int = 3

for f in compose_intermediate_fns(
    [
        T(-1 / 2 * e_1 + -1 / 2 * e_2),
        S(screen_width, screen_height),
        S(1 / 2, 1 / 2),
        T(1 * e_1 + 1 * e_2),
    ],
    relative_basis=False,
):
    with create_graphs(graph_bounds=(6, 6)) as axes:
        # create_basis(fn=f)
        # create_x_and_y(fn=f)
        create_basis(fn=identity())
        create_x_and_y(fn=identity())
        # draw_ndc(fn=f)
        draw_screen(width=screen_width, height=screen_height, fn=f)
        axes.set_title(f._repr_latex_())
# %%
screen_width: int = 4
screen_height: int = 3

for f in compose_intermediate_fns(
    [
        T(-0.5 * e_1 + -0.5 * e_2),
        S(screen_width, screen_height),
        S(0.5, 0.5),
        T(1.0 * e_1 + 1.0 * e_2),
    ],
    relative_basis=True,
):
    with create_graphs(graph_bounds=(6, 6)) as axes:
        # create_basis(fn=f)
        # create_x_and_y(fn=f)
        create_basis(fn=identity())
        create_x_and_y(fn=f)
        # draw_ndc(fn=f)
        draw_screen(width=screen_width, height=screen_height, fn=f)
        axes.set_title(f._repr_latex_())

# %%

# %%
