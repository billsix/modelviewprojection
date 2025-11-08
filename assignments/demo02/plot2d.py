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

from modelviewprojection.mathutils2d import (
    Vector2D,
    compose,
    compose_intermediate_fns,
)
from modelviewprojection.mathutils2d import rotate as R
from modelviewprojection.mathutils2d import translate as T
from modelviewprojection.nbplotutils import (
    create_basis,
    create_graphs,
    draw_triangle,
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
    create_basis(fn=R(math.radians(53.130102)))

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
    create_basis(fn=R(0.0))
    create_basis(
        fn=R(math.radians(45.0)),
        xcolor=(0, 1, 0),
        ycolor=(1, 1, 0),
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
        fn=compose(
            [
                R(math.radians(90.0)),
                T(Vector2D(x=2.0, y=0.0)),
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
for f in compose_intermediate_fns(
    [
        R(math.radians(90.0)),
        T(Vector2D(x=2.0, y=0.0)),
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
for f in compose_intermediate_fns(
    [
        R(math.radians(0)),
        R(math.radians(90.0)),
        T(Vector2D(x=2.0, y=0.0)),
    ],
    relative_basis=True,
):
    with create_graphs():
        create_basis(fn=f)
        draw_triangle(fn=f)
