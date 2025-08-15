# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%

# Copyright (c) 2025 William Emerison Six
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
# Below, Implement fahrenheit_to_kelvin, celsius_to_fahrenheit, and kelvin_to_fahrenheit.  replace "translate(0.0) with your implementation

# %%


from pytest import approx

from modelviewprojection.mathutils import InvertibleFunction, compose, inverse
from modelviewprojection.mathutils1d import Vector1D, translate, uniform_scale

# %%

# %%
Vector1D(x=1.0) + Vector1D(x=3.0)

# %%
Vector1D(x=5.0) - Vector1D(x=1.0)

# %%
4.0 * Vector1D(x=2.0)

# %%
-Vector1D(x=2.0)

# %% [markdown]
# Define the translate function
# -----------------------------
# $T_{b=2}(x) = x + b$


# %%
fn: InvertibleFunction[Vector1D] = translate(2.0)


# %% [markdown]
# $T_{b=2}(5) $

# %%
fn(Vector1D(5))

# %% [markdown]
# Define the affine function
# --------------------------
# $f(x) = {m}{x} + b = T_{b=2} \circ S_{m=5} $
#

# %%
m: float = 5.0
b: float = 2.0
fn: InvertibleFunction[Vector1D] = compose(translate(b), uniform_scale(m))
print(fn(Vector1D(0.0)))
print(fn(Vector1D(1.0)))


# %%
fn: InvertibleFunction[Vector1D] = uniform_scale(4.0)
print(fn(Vector1D(1.0)))
print(fn(Vector1D(2.0)))
print(fn(Vector1D(3.0)))

# %%
celsius_to_kelvin: InvertibleFunction[Vector1D] = translate(273.15)
assert celsius_to_kelvin(Vector1D(0.0)) == Vector1D(approx(273.15))
assert celsius_to_kelvin(Vector1D(100.0)) == Vector1D(approx(373.15))


fahrenheit_to_celsius: InvertibleFunction[Vector1D] = compose(
    uniform_scale(5.0 / 9.0), translate(-32.0)
)
assert fahrenheit_to_celsius(Vector1D(32.0)) == Vector1D(approx(0.0))
assert fahrenheit_to_celsius(Vector1D(212.0)) == Vector1D(approx(100.0))


kelvin_to_celsius: InvertibleFunction[Vector1D] = inverse(celsius_to_kelvin)
assert kelvin_to_celsius(Vector1D(273.15)) == Vector1D(approx(0.0))
assert kelvin_to_celsius(Vector1D(373.15)) == Vector1D(approx(100.0))


# %%


# %% [markdown]
# Implement fahrenheit_to_kelvin, celsius_to_fahrenheit, and kelvin_to_fahrenheit.  replace "translate(0.0) with your implementation

# %%

fahrenheit_to_kelvin: InvertibleFunction[Vector1D] = translate(0.0)
assert fahrenheit_to_kelvin(Vector1D(32.0)) == Vector1D(approx(273.15))
assert fahrenheit_to_kelvin(Vector1D(212.0)) == Vector1D(approx(373.15))

celsius_to_fahrenheit: InvertibleFunction[Vector1D] = translate(0.0)
assert celsius_to_fahrenheit(Vector1D(0.0)) == Vector1D(approx(32.0))
assert celsius_to_fahrenheit(Vector1D(100.0)) == Vector1D(approx(212.0))


kelvin_to_fahrenheit: InvertibleFunction[Vector1D] = translate(0.0)
assert kelvin_to_fahrenheit(Vector1D(273.15)) == Vector1D(approx(32.0))
assert kelvin_to_fahrenheit(Vector1D(373.15)) == Vector1D(approx(212.0))
