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

# %% [markdown]
# Test
#


# %%
from pytest import approx

from modelviewprojection.mathutils import InvertibleFunction, compose, inverse
from modelviewprojection.mathutils1d import Vector1D, translate, uniform_scale

# %%
Vector1D(x=1.0) + Vector1D(x=3.0)

# %%
Vector1D(x=5.0) - Vector1D(x=1.0)

# %%
4.0 * Vector1D(x=2.0)

# %%
-Vector1D(x=2.0)

# %%
fn: InvertibleFunction[Vector1D] = translate(2.0)


# %%
fn(Vector1D(5))

# %% [markdown]
# f(x) = m*x + b
#

# %%
m = 5.0
b = 2.0
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

fahrenheit_to_kelvin: InvertibleFunction[Vector1D] = compose(
    celsius_to_kelvin, fahrenheit_to_celsius
)
assert fahrenheit_to_kelvin(Vector1D(32.0)) == Vector1D(approx(273.15))
assert fahrenheit_to_kelvin(Vector1D(212.0)) == Vector1D(approx(373.15))

kelvin_to_celsius: InvertibleFunction[Vector1D] = inverse(celsius_to_kelvin)
assert kelvin_to_celsius(Vector1D(273.15)) == Vector1D(approx(0.0))
assert kelvin_to_celsius(Vector1D(373.15)) == Vector1D(approx(100.0))


# %%


# %% [markdown]
# Implement   kelvin_to_celsius, celsius_to_fahrenheit, and kelvin_to_fahrenheit.  replace "translate(0.0) with your implementation

# %%

celsius_to_fahrenheit: InvertibleFunction[Vector1D] = translate(0.0)
assert celsius_to_fahrenheit(Vector1D(0.0)) == Vector1D(approx(32.0))
assert celsius_to_fahrenheit(Vector1D(100.0)) == Vector1D(approx(212.0))


kelvin_to_fahrenheit: InvertibleFunction[Vector1D] = translate(0.0)
assert kelvin_to_fahrenheit(Vector1D(273.15)) == Vector1D(approx(32.0))
assert kelvin_to_fahrenheit(Vector1D(373.15)) == Vector1D(approx(212.0))


# %%
