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
import IPython.display as display

# %%
import numpy as np
from PIL import Image

# Framebuffer dimensions
WIDTH, HEIGHT = 700, 700

# Global framebuffer (3 channels: RGB)
framebuffer = np.random.randint(0, 256, (HEIGHT, WIDTH, 3), dtype=np.uint8)

# Global default color (black)
BLACK = (0, 0, 0)


def show_framebuffer():
    """Display the framebuffer in the Jupyter notebook."""
    img = Image.fromarray(framebuffer, "RGB")
    display.display(img)


# Show initial random framebuffer
show_framebuffer()


# %%
def clear_framebuffer(color=BLACK):
    """Fill the framebuffer with the given color."""
    global framebuffer
    framebuffer[:, :] = color


# Clear to black and show
clear_framebuffer()
show_framebuffer()


# %%
def draw_filled_triangle(p1, p2, p3, color=(255, 255, 255)):
    """
    Draw a filled triangle using the edge function (cross product) method.
    p1, p2, p3 are (x, y) tuples in framebuffer coordinates.
    """
    global framebuffer

    def to_fb_coords(x, y):
        """Convert from OpenGL-style coords to framebuffer array coords."""
        return x, HEIGHT - 1 - y

    x1, y1 = to_fb_coords(*p1)
    x2, y2 = to_fb_coords(*p2)
    x3, y3 = to_fb_coords(*p3)

    # Triangle bounding box
    min_x = max(int(min(x1, x2, x3)), 0)
    max_x = min(int(max(x1, x2, x3)), WIDTH - 1)
    min_y = max(int(min(y1, y2, y3)), 0)
    max_y = min(int(max(y1, y2, y3)), HEIGHT - 1)

    # Edge function (cross product)
    def edge(ax, ay, bx, by, px, py):
        return (px - ax) * (by - ay) - (py - ay) * (bx - ax)

    # Precompute edge function signs for top-left rule
    area = edge(x1, y1, x2, y2, x3, y3)
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


# %%
# Example: draw a white triangle
clear_framebuffer()
draw_filled_triangle((350, 350), (420, 350), (420, 420), color=(255, 255, 255))
show_framebuffer()
