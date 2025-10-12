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

# doc-region-begin imports
import warnings

import pytest

import modelviewprojection.mathutils1d as mu1d

# turn warnings into exceptions
warnings.filterwarnings("error", category=RuntimeWarning)

# doc-region-end imports

# %%

# %%
# doc-region-begin adding vectors
mu1d.Vector1D(x=1.0) + mu1d.Vector1D(x=3.0)
# doc-region-end adding vectors

# %%
# doc-region-begin subtracting vectors
mu1d.Vector1D(x=5.0) - mu1d.Vector1D(x=1.0)
# doc-region-end subtracting vectors

# %%
# doc-region-begin multiplying scalar by a vector
4.0 * mu1d.Vector1D(x=2.0)
# doc-region-end multiplying scalar by a vector

# %%
# doc-region-begin negating a vector
-mu1d.Vector1D(x=2.0)
# doc-region-end negating a vector

# %% [markdown]
# Define the translate function
# -----------------------------
# $T_{b=2}(x) = x + b$
#


# %%
# doc-region-begin invertible function
fn: mu1d.InvertibleFunction = mu1d.translate(mu1d.Vector1D(2.0))
# doc-region-end invertible function


# %% [markdown]
# $T_{b=2}(0) $ = 2.0

# %%
# doc-region-begin applying invertible function
assert fn(mu1d.Vector1D(0)) == mu1d.Vector1D(2.0)
assert fn(mu1d.Vector1D(1)) == mu1d.Vector1D(3.0)
assert fn(mu1d.Vector1D(5)) == mu1d.Vector1D(7.0)
# doc-region-end applying invertible function


# %%
# doc-region-begin applying inverse function
assert mu1d.inverse(fn)(mu1d.Vector1D(2)) == mu1d.Vector1D(0.0)
assert mu1d.inverse(fn)(mu1d.Vector1D(3)) == mu1d.Vector1D(1.0)
assert mu1d.inverse(fn)(mu1d.Vector1D(7)) == mu1d.Vector1D(5.0)
# doc-region-end applying inverse function

# %%
# doc-region-begin y = m*x + b
m: float = 5.0
b: float = 2.0
fn: mu1d.InvertibleFunction = mu1d.compose(
    [mu1d.translate(mu1d.Vector1D(b)), mu1d.uniform_scale(m)]
)
print(fn(mu1d.Vector1D(0.0)))
print(fn(mu1d.Vector1D(1.0)))

assert fn(mu1d.Vector1D(0.0)) == mu1d.Vector1D(2.0)
assert fn(mu1d.Vector1D(1.0)) == mu1d.Vector1D(7.0)
# doc-region-end y = m*x + b


# %%
fn: mu1d.InvertibleFunction = mu1d.uniform_scale(4.0)
print(fn(mu1d.Vector1D(1.0)))
assert fn(mu1d.Vector1D(1.0)) == mu1d.Vector1D(4.0)
print(fn(mu1d.Vector1D(2.0)))
assert fn(mu1d.Vector1D(2.0)) == mu1d.Vector1D(8.0)
print(fn(mu1d.Vector1D(3.0)))
assert fn(mu1d.Vector1D(3.0)) == mu1d.Vector1D(12.0)

# %%
# doc-region-begin defined functions
celsius_to_kelvin: mu1d.InvertibleFunction = mu1d.translate(
    mu1d.Vector1D(273.15)
)
assert celsius_to_kelvin(mu1d.Vector1D(0.0)) == mu1d.Vector1D(
    pytest.approx(273.15)
)
assert celsius_to_kelvin(mu1d.Vector1D(100.0)) == mu1d.Vector1D(
    pytest.approx(373.15)
)


fahrenheit_to_celsius: mu1d.InvertibleFunction = mu1d.compose(
    [mu1d.uniform_scale(5.0 / 9.0), mu1d.translate(mu1d.Vector1D(-32.0))]
)
assert fahrenheit_to_celsius(mu1d.Vector1D(32.0)) == mu1d.Vector1D(
    pytest.approx(0.0)
)
assert fahrenheit_to_celsius(mu1d.Vector1D(212.0)) == mu1d.Vector1D(
    pytest.approx(100.0)
)


kelvin_to_celsius: mu1d.InvertibleFunction = mu1d.inverse(celsius_to_kelvin)
assert kelvin_to_celsius(mu1d.Vector1D(273.15)) == mu1d.Vector1D(
    pytest.approx(0.0)
)
assert kelvin_to_celsius(mu1d.Vector1D(373.15)) == mu1d.Vector1D(
    pytest.approx(100.0)
)
# doc-region-end defined functions


# %%


# %% [markdown]
# Implement fahrenheit_to_kelvin, celsius_to_fahrenheit, and kelvin_to_fahrenheit.  replace "mu1d.translate(mu1d.Vector1D(0.0)) with your implementation

# %%

# doc-region-begin work to do
fahrenheit_to_kelvin: mu1d.InvertibleFunction = mu1d.translate(
    mu1d.Vector1D(0.0)
)
assert fahrenheit_to_kelvin(mu1d.Vector1D(32.0)) == mu1d.Vector1D(
    pytest.approx(273.15)
)
assert fahrenheit_to_kelvin(mu1d.Vector1D(212.0)) == mu1d.Vector1D(
    pytest.approx(373.15)
)

celsius_to_fahrenheit: mu1d.InvertibleFunction = mu1d.translate(
    mu1d.Vector1D(0.0)
)
assert celsius_to_fahrenheit(mu1d.Vector1D(0.0)) == mu1d.Vector1D(
    pytest.approx(32.0)
)
assert celsius_to_fahrenheit(mu1d.Vector1D(100.0)) == mu1d.Vector1D(
    pytest.approx(212.0)
)


kelvin_to_fahrenheit: mu1d.InvertibleFunction = mu1d.translate(
    mu1d.Vector1D(0.0)
)
assert kelvin_to_fahrenheit(mu1d.Vector1D(273.15)) == mu1d.Vector1D(
    pytest.approx(32.0)
)
assert kelvin_to_fahrenheit(mu1d.Vector1D(373.15)) == mu1d.Vector1D(
    pytest.approx(212.0)
)
# doc-region-end work to do

# %%
