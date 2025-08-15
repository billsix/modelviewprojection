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
# Problem 1
# ---------
#
# Below, Implement fahrenheit_to_kelvin, celsius_to_fahrenheit, and kelvin_to_fahrenheit.  replace "translate(0.0) with your implementation

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


# %%
from typing import List, Tuple
import IPython.display as display

# %%
import numpy as np
from PIL import Image

# Framebuffer dimensions
WIDTH: int
HEIGHT: int
WIDTH, HEIGHT = 700, 700

# Global framebuffer (3 channels: RGB)
framebuffer: np.ndarray = np.random.randint(
    0, 256, (HEIGHT, WIDTH, 3), dtype=np.uint8
)

# Global default color (black)
BLACK: Tuple[int, int, int] = (0, 0, 0)


def show_framebuffer() -> None:
    """Display the framebuffer in the Jupyter notebook."""
    img: PIL.Image.Image = Image.fromarray(framebuffer, "RGB")
    display.display(img)


# Show initial random framebuffer
show_framebuffer()


# %%
def clear_framebuffer(color=BLACK) -> None:
    """Fill the framebuffer with the given color."""
    global framebuffer
    framebuffer[:, :] = color


# Clear to black and show
clear_framebuffer()
show_framebuffer()


# %%
def draw_filled_triangle(v1: Vector2D, v2: Vector2D, v3: Vector2D, color=(255, 255, 255)) -> None:
    """
    Draw a filled triangle using the edge function (cross product) method.
    p1, p2, p3 are (x, y) tuples in framebuffer coordinates.
    """
    global framebuffer

    def to_fb_coords(x, y):
        """Convert from OpenGL-style coords to framebuffer array coords."""
        return x, HEIGHT - 1 - y

    x1: int
    y1: int
    x2: int
    y2: int
    z1: int
    z3: int

    x1, y1 = to_fb_coords(int(v1.x), int(v1.y))
    x2, y2 = to_fb_coords(int(v2.x), int(v2.y))
    x3, y3 = to_fb_coords(int(v3.x), int(v3.y))

    # Triangle bounding box
    min_x: int = max(int(min(x1, x2, x3)), 0)
    max_x: int = min(int(max(x1, x2, x3)), WIDTH - 1)
    min_y: int = max(int(min(y1, y2, y3)), 0)
    max_y: int = min(int(max(y1, y2, y3)), HEIGHT - 1)

    # Edge function (cross product)
    def edge(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> int:
        return (px - ax) * (by - ay) - (py - ay) * (bx - ax)

    # Precompute edge function signs for top-left rule
    area: int = edge(x1, y1, x2, y2, x3, y3)
    if area == 0:
        return  # Degenerate triangle

    # Loop over bounding box
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            w0 = edge(x2, y2, x3, y3, x, y)
            w1 = edge(x3, y3, x1, y1, x, y)
            w2 = edge(x1, y1, x2, y2, x, y)

            # If the signs match the triangle area, pixel is inside
            if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (
                w0 <= 0 and w1 <= 0 and w2 <= 0
            ):
                framebuffer[y, x] = color


# %% [markdown]
# Problem 2
# ---------
#
# Make a new picture below where the triangle is translated 0.3 units in NDC to the left

# %%
from modelviewprojection.mathutils2d import Vector2D, scale, translate

# %%
ndc_to_screen: InvertibleFunction[Vector2D] = compose(
    translate(Vector2D((WIDTH + 0.5) // 2, (HEIGHT + 0.5) // 2)),
    scale((WIDTH + 0.5) // 2, (HEIGHT + 0.5) // 2),
)

# %%
# Example: draw a white triangle

triangle_in_NDC: Tuple[Vector2D] = (
    Vector2D(0.0, 0.0),
    Vector2D(0.2, 0.0),
    Vector2D(0.2, 0.2),
)

# %%
triangle_in_screen: List[Vector2D] = [ndc_to_screen(x) for x in triangle_in_NDC]
print(triangle_in_screen)


clear_framebuffer()
draw_filled_triangle(
    triangle_in_screen[0],
    triangle_in_screen[1],
    triangle_in_screen[2],
    color=(255, 255, 255),
)
show_framebuffer()

# %%
move: InvertibleFunction[Vector2D] = translate(Vector2D(0, 0.5))

triangle_in_screen = [compose(ndc_to_screen, move)(x) for x in triangle_in_NDC]
print(triangle_in_screen)


clear_framebuffer()
draw_filled_triangle(*triangle_in_screen, color=(255, 255, 255))
show_framebuffer()

# %%

# %%
