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

# Copyright (c) 2025-2026 William Emerison Six
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
# Below, Implement fahrenheit_to_kelvin, celsius_to_fahrenheit, and
# kelvin_to_fahrenheit.  replace "translate(b=0.0 * e_1)" with your
# implementation


# %%
# doc-region-begin imports
import warnings

from gacalc.g1 import Vector, e_1
from gacalc.transforms import (
    InvertibleFunction,
    compose,
    inverse,
    translate,
    uniform_scale,
)

# turn warnings into exceptions
warnings.filterwarnings("error", category=RuntimeWarning)

# doc-region-end imports

# %% [markdown]
# A one-dimensional vector is a multiple of the basis vector `e_1`, so `2.0 *
# e_1` is the number 2 seen as a vector.  Write the coefficient every time --
# `1 * e_1`, not a bare `e_1` -- so that each value reads as
# `coefficient * basis`.

# %%
# doc-region-begin adding vectors
1.0 * e_1 + 3.0 * e_1
# doc-region-end adding vectors

# %%
# doc-region-begin subtracting vectors
5.0 * e_1 - 1.0 * e_1
# doc-region-end subtracting vectors

# %%
# doc-region-begin multiplying scalar by a vector
4.0 * (2.0 * e_1)
# doc-region-end multiplying scalar by a vector

# %%
# doc-region-begin negating a vector
-(2.0 * e_1)
# doc-region-end negating a vector

# %% [markdown]
# Define the translate function
# -----------------------------
# $T_{b=2}(x) = x + b$
#


# %%
# doc-region-begin invertible function
fn: InvertibleFunction[Vector] = translate(b=2.0 * e_1)
# doc-region-end invertible function


# %% [markdown]
# $T_{b=2}(0) $ = 2.0

# %%
# doc-region-begin applying invertible function
assert fn(0.0 * e_1) == 2.0 * e_1
assert fn(1.0 * e_1) == 3.0 * e_1
assert fn(5.0 * e_1) == 7.0 * e_1
# doc-region-end applying invertible function


# %%
# doc-region-begin applying inverse function
assert inverse(fn)(2.0 * e_1) == 0.0 * e_1
assert inverse(fn)(3.0 * e_1) == 1.0 * e_1
assert inverse(fn)(7.0 * e_1) == 5.0 * e_1
# doc-region-end applying inverse function

# %%
# doc-region-begin y = m*x + b
m: float = 5.0
b: float = 2.0
fn: InvertibleFunction[Vector] = compose(
    [translate(b=b * e_1), uniform_scale(m=m)]
)
print(fn(0.0 * e_1))
print(fn(1.0 * e_1))

assert fn(0.0 * e_1) == 2.0 * e_1
assert fn(1.0 * e_1) == 7.0 * e_1
# doc-region-end y = m*x + b


# %%
fn: InvertibleFunction[Vector] = uniform_scale(m=4.0)
print(fn(1.0 * e_1))
assert fn(1.0 * e_1) == 4.0 * e_1
print(fn(2.0 * e_1))
assert fn(2.0 * e_1) == 8.0 * e_1
print(fn(3.0 * e_1))
assert fn(3.0 * e_1) == 12.0 * e_1

# %% [markdown]
# The conversions below compare with `isclose` rather than `==`, because the
# arithmetic is floating point and lands a fraction of a degree away from the
# exact answer.  gacalc's `isclose` defaults to EXACT equality, so the
# tolerances are given explicitly at every call.

# %%
# doc-region-begin defined functions
celsius_to_kelvin: InvertibleFunction[Vector] = translate(b=273.15 * e_1)
assert celsius_to_kelvin(0.0 * e_1).isclose(
    273.15 * e_1, rel_tol=1e-5, abs_tol=1e-5
)

assert celsius_to_kelvin(100.0 * e_1).isclose(
    373.15 * e_1, rel_tol=1e-5, abs_tol=1e-5
)


fahrenheit_to_celsius: InvertibleFunction[Vector] = compose(
    [uniform_scale(m=5.0 / 9.0), translate(b=-32.0 * e_1)]
)
assert fahrenheit_to_celsius(32.0 * e_1).isclose(
    0.0 * e_1, rel_tol=1e-5, abs_tol=1e-5
)

assert fahrenheit_to_celsius(212.0 * e_1).isclose(
    100.0 * e_1, rel_tol=1e-5, abs_tol=1e-5
)


kelvin_to_celsius: InvertibleFunction[Vector] = inverse(celsius_to_kelvin)
assert kelvin_to_celsius(273.15 * e_1).isclose(
    0.0 * e_1, rel_tol=1e-5, abs_tol=1e-5
)
assert kelvin_to_celsius(373.15 * e_1).isclose(
    100.0 * e_1, rel_tol=1e-5, abs_tol=1e-5
)
# doc-region-end defined functions


# %%


# %% [markdown]
# Implement fahrenheit_to_kelvin, celsius_to_fahrenheit, and
# kelvin_to_fahrenheit.
# replace "translate(b=0.0 * e_1)" with your implementation

# %%

# doc-region-begin work to do
fahrenheit_to_kelvin: InvertibleFunction[Vector] = translate(b=0.0 * e_1)
assert fahrenheit_to_kelvin(32.0 * e_1).isclose(
    273.15 * e_1, rel_tol=1e-5, abs_tol=1e-5
)
assert fahrenheit_to_kelvin(212.0 * e_1).isclose(
    373.15 * e_1, rel_tol=1e-5, abs_tol=1e-5
)

celsius_to_fahrenheit: InvertibleFunction[Vector] = translate(b=0.0 * e_1)
assert celsius_to_fahrenheit(0.0 * e_1).isclose(
    32.0 * e_1, rel_tol=1e-5, abs_tol=1e-5
)

assert celsius_to_fahrenheit(100.0 * e_1).isclose(
    212.0 * e_1, rel_tol=1e-5, abs_tol=1e-5
)


kelvin_to_fahrenheit: InvertibleFunction[Vector] = translate(b=0.0 * e_1)
assert kelvin_to_fahrenheit(273.15 * e_1).isclose(
    32.0 * e_1, rel_tol=1e-5, abs_tol=1e-5
)
assert kelvin_to_fahrenheit(373.15 * e_1).isclose(
    212.0 * e_1, rel_tol=1e-5, abs_tol=1e-5
)
# doc-region-end work to do

# %%
