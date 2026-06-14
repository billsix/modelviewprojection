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
# # The Cross Product, derived with rotors
#
# This is the cross-product derivation from
# `multivariate-math/proofs/crossproduct.tex`, ported from rotation matrices to
# **gacalc rotors**.  The geometry is unchanged: rotate $\vec a$ and $\vec b$ so
# that $\vec a$ lies on the $x$ axis, rotate $\vec b$ into the $x$-$y$ plane, read
# off the perpendicular, then rotate everything back.  Each rotation, which the
# LaTeX proof writes as a matrix, is here a single rotor built with
# `rotor_from_vectors` and applied with `sandwich`.
#
# * **Part 1** does the derivation **symbolically** for general $\vec a$, $\vec b$
#   and proves it equals the analytic cross product.
# * **Part 2** repeats it on a concrete example, showing **every multiplication**
#   term-by-term with `show_mult`.
#
# The runnable, headless version of this math is
# `modelviewprojection.mathdemos.crossproduct.cross_product`.

# %%

# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# %%
import sympy
from IPython.display import Markdown, display

from gacalc.g3 import Vector3
from gacalc.nbplotutils import show_mult

e_1, e_2, e_3 = Vector3.e_1, Vector3.e_2, Vector3.e_3

# %% [markdown]
# ## The problem
#
# Given $\vec a$ and $\vec b$ in $\mathbb{R}^3$, find $\vec c$ that is
# perpendicular to both, follows the right-hand rule, and has
# $\lVert \vec c \rVert = \lVert \vec a \rVert\,\lVert \vec b \rVert \sin\theta$.

# %% [markdown]
# ## Part 1 — the rotor derivation (symbolic, for all $\vec a$, $\vec b$)

# %%
a_x, a_y, a_z, b_x, b_y, b_z = sympy.symbols(
    "a_x a_y a_z b_x b_y b_z", real=True
)
a = Vector3(a_x, a_y, a_z)
b = Vector3(b_x, b_y, b_z)
a, b

# %% [markdown]
# **Step 1 — a rotor that carries $\vec a$ onto the $x$ axis.**
# `rotor_from_vectors` builds the rotor that rotates its `from_vector` toward its
# `to_vector`; the sandwich $R\,\vec a\,R^{-1}$ then lands $\vec a$ on $+x$ as
# $\lVert \vec a\rVert\, e_1$.  (This single rotor is the proof's
# $f_{a'}^x \circ f_a^{zx}$.)

# %%
R1 = Vector3.rotor_from_vectors(from_vector=a, to_vector=e_1).normalize()
a_aligned = R1.sandwich(a)
a_aligned.simplified()  # = |a| e_1

# %% [markdown]
# **Step 2 — carry $\vec b$ along with the same rotor**, giving $\vec b\,''$.

# %%
b_aligned = R1.sandwich(b)
b_aligned.simplified()

# %% [markdown]
# **Step 3 — the part of $\vec b\,''$ perpendicular to $\vec a$** lives in the
# $y$-$z$ plane (since $\vec a$ is now on $x$).  Its length is
# $c = \lVert \vec b\rVert \sin\theta$.

# %%
b_perp = Vector3.reject(away_from=e_1)(b_aligned)
c = b_perp.magnitude()
b_perp.simplified()

# %% [markdown]
# **Step 4 — a second rotor** carries that perpendicular part onto $+y$.  It is a
# rotation in the $y$-$z$ plane, so it leaves $\vec a$ (on $x$) fixed.  This is the
# proof's $f_{b''}^{xy}$.

# %%
R2 = Vector3.rotor_from_vectors(from_vector=b_perp, to_vector=e_2).normalize()

# %% [markdown]
# **Step 5 — in the fully aligned frame** $\vec a\,'' = \lVert\vec a\rVert e_1$ and
# $\vec b\,'''$ lies in the $x$-$y$ plane, so the perpendicular is simply along
# $z$ with length $\lVert\vec a\rVert\,c$:

# %%
c_aligned = (a.magnitude() * c) * e_3
c_aligned

# %% [markdown]
# **Step 6 — rotate the result back** to the original frame by undoing $R_2$ then
# $R_1$ (the reverse of a unit rotor is its inverse).

# %%
cross = R1.reverse().sandwich(R2.reverse().sandwich(c_aligned))

# %% [markdown]
# **The proof.**  Each component, simplified, equals the analytic cross product
# $\vec a \times \vec b = (a_y b_z - a_z b_y,\; a_z b_x - a_x b_z,\; a_x b_y - a_y b_x)$.
# (`sympy.simplify` has to denest the rotor radicals, so this cell takes a few
# minutes.)

# %%
got_x, got_y, got_z = tuple(cross)
exp_x = a_y * b_z - a_z * b_y
exp_y = a_z * b_x - a_x * b_z
exp_z = a_x * b_y - a_y * b_x
checks = [
    sympy.simplify(got_x - exp_x) == 0,
    sympy.simplify(got_y - exp_y) == 0,
    sympy.simplify(got_z - exp_z) == 0,
]
display(Markdown(f"All three components match the cross product: **{all(checks)}**"))

# %% [markdown]
# ## Part 2 — step by step, every multiplication via `show_mult`
#
# The same derivation on a concrete example, with each geometric product expanded
# term-by-term.  Exact arithmetic (integer inputs route through sympy), so nothing
# is rounded.

# %%
a = Vector3(2, 1, 3)
b = Vector3(0, 4, 1)
a, b

# %% [markdown]
# ### Aligning $\vec a$ onto the $x$ axis is a sandwich $R_1\,\vec a\,R_1^{-1}$
# First the left product $R_1\,\vec a$, broken into its component products:

# %%
R1 = Vector3.rotor_from_vectors(from_vector=a, to_vector=e_1).normalize()
show_mult(R1, a)

# %% [markdown]
# Then multiply that on the right by $R_1^{-1}$ to finish the sandwich; the result
# is $\lVert\vec a\rVert\,e_1$ (purely along $x$):

# %%
show_mult(R1 * a, R1.reverse())

# %% [markdown]
# ### The same rotor carries $\vec b$ to $\vec b\,''$

# %%
show_mult(R1 * b, R1.reverse())

# %% [markdown]
# ### Second rotor: bring $\vec b\,''$'s perpendicular part onto $y$

# %%
b_aligned = R1.sandwich(b)
b_perp = Vector3.reject(away_from=e_1)(b_aligned)
R2 = Vector3.rotor_from_vectors(from_vector=b_perp, to_vector=e_2).normalize()
show_mult(R2 * b_aligned, R2.reverse())

# %% [markdown]
# ### The aligned-frame perpendicular, rotated back, is $\vec a \times \vec b$

# %%
c = b_perp.magnitude()
c_aligned = (a.magnitude() * c) * e_3
cross = R1.reverse().sandwich(R2.reverse().sandwich(c_aligned))
cross.simplified()

# %% [markdown]
# ## Part 3 -- alignment by projections + rotors (no trigonometry)
#
# The animation aligns `a` the way the original rotation-matrix proof does, but
# **without ever computing an angle**.  Each rotation is: *project the vector onto
# a coordinate plane, then make a rotor from that projection to an axis* -- using
# only `reject` (projection) and `rotor_from_vectors` (a geometric product
# `R = |u||v| + v*u`).  No `sin` / `cos` / `atan` / `acos` anywhere.
#
# Shown numerically here so the steps read cleanly; the symbolic proof in Part 1
# (and the test suite) covers all `a`, `b`.  This mirrors
# `mathdemos.crossproduct.build_alignment_graph`, which builds these same three
# rotors as Cayley-graph edges.

# %%
a = Vector3(2.0, 1.0, 3.0)
b = Vector3(0.0, 4.0, 1.0)
[float(x) for x in a], [float(x) for x in b]

# %% [markdown]
# **Step 1 (about z):** project `a` onto the e1-e2 plane (drop its e3 part), then a
# rotor carrying that shadow onto +x.  Applying it leaves `a` in the x-z plane
# (its e2 component becomes 0).

# %%
a_xy = Vector3.reject(away_from=e_3)(a)  # projection onto the e1-e2 plane
R_z = Vector3.rotor_from_vectors(from_vector=a_xy, to_vector=e_1).normalize()
a1 = R_z.sandwich(a)
[round(float(x), 4) for x in a1]

# %% [markdown]
# **Step 2 (about y):** a rotor carrying that x-z vector onto the +x axis, so
# `a` lands on `(|a|, 0, 0)`.

# %%
R_y = Vector3.rotor_from_vectors(from_vector=a1, to_vector=e_1).normalize()
a2 = R_y.sandwich(a1)
[round(float(x), 4) for x in a2]

# %% [markdown]
# **Step 3 (about x):** carry `b` along, take the part of `b` perpendicular to `a`
# (project onto the e2-e3 plane), and a rotor carrying it onto +y -- `b` into the
# x-y plane.

# %%
b2 = R_y.sandwich(R_z.sandwich(b))
b_perp3 = Vector3.reject(away_from=e_1)(b2)
R_x = Vector3.rotor_from_vectors(from_vector=b_perp3, to_vector=e_2).normalize()
c3 = float(b_perp3.magnitude())
[round(float(x), 4) for x in R_x.sandwich(b2)]

# %% [markdown]
# In the fully aligned frame the perpendicular is along z with length `|a| c`;
# rotate it back (undo R_x, then R_y, then R_z) to get `a x b` -- with no
# trigonometry used anywhere.

# %%
cross3_aligned = (float(a.magnitude()) * c3) * e_3
cross3 = R_z.reverse().sandwich(
    R_y.reverse().sandwich(R_x.reverse().sandwich(cross3_aligned))
)
[round(float(x), 4) for x in cross3]  # = a x b = (-11, -2, 8)
