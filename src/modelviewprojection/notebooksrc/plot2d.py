# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Plot 2D


# %%

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

# %% [markdown]
# Problem 1
# ---------
#

# %%
import math

import sympy

from modelviewprojection.mathutils import (
    Vector1,
    Vector2,
    Vector3,
    compose,
    compose_intermediate_fns,
    identity,
    inverse,
    rotate,
    scale_non_uniform,
    translate,
)
from modelviewprojection.util.nbplotutils import (
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
translate(b=5 * Vector1.e_1)

# %%
scale_non_uniform(5, 6)

# %%
inverse(translate(b=5 * Vector1.e_1))

# %%
translate(b=5 * Vector2.e_1 + 6 * Vector2.e_2)

# %%
translate(b=5 * Vector3.e_1 + 6 * Vector3.e_2 + 7 * Vector3.e_3)

# %%
inverse(translate(b=5 * Vector3.e_1 + 6 * Vector3.e_2 + 7 * Vector3.e_3))

# %%
rotate(sympy.pi / 2)

# %%
compose([rotate(sympy.pi / 2), translate(b=5 * Vector2.e_1 + 6 * Vector2.e_2)])

# %%
inverse(
    compose(
        [rotate(sympy.pi / 2), translate(b=5 * Vector2.e_1 + 6 * Vector2.e_2)]
    )
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
fn = rotate(math.radians(53.130102))
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
fn = rotate(math.radians(53.130102))
with create_graphs(graph_bounds=(5, 5)) as axes:
    create_basis(fn=rotate(0.0))
    create_x_and_y(fn=rotate(0.0))
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
fn = rotate(math.radians(53.130102))
with create_graphs(graph_bounds=(5, 5)) as axes:
    create_basis(fn=rotate(0.0))
    create_x_and_y(fn=rotate(0.0))
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
        rotate(sympy.pi / 4),
        translate(b=2.0 * Vector2.e_1),
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
    [rotate(sympy.pi / 4), translate(b=2.0 * Vector2.e_1)]
):
    # TODO - figure out if I can render the latex as part of one markdown
    # command, if I were to uncomment out this line and other markdown lines,
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
        rotate(sympy.pi / 4),
        translate(b=1.0 * Vector2.e_1),
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
        translate(b=-0.5 * Vector2.e_1 - 0.5 * Vector2.e_2),
        scale_non_uniform(screen_width, screen_height),
        scale_non_uniform(0.5, 0.5),
        translate(b=1.0 * Vector2.e_1 + 1.0 * Vector2.e_2),
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
        translate(b=-0.5 * Vector2.e_1 - 0.5 * Vector2.e_2),
        scale_non_uniform(screen_width, screen_height),
        scale_non_uniform(0.5, 0.5),
        translate(b=1.0 * Vector2.e_1 + 1.0 * Vector2.e_2),
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
