# Copyright (c) 2018-2025 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import math
import sys
from collections.abc import Callable

import glfw
import numpy as np
import OpenGL.GL as GL

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "Assignment 1", None, None)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0, 0.0, 0.0, 1.0)

GL.glMatrixMode(GL.GL_PROJECTION)
GL.glLoadIdentity()
GL.glMatrixMode(GL.GL_MODELVIEW)
GL.glLoadIdentity()


def draw_in_square_viewport() -> None:
    GL.glClearColor(0.2, 0.2, 0.2, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)

    min = width if width < height else height

    GL.glEnable(GL.GL_SCISSOR_TEST)
    GL.glScissor(
        int((width - min) / 2.0),
        int((height - min) / 2.0),
        min,
        min,
    )

    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glDisable(GL.GL_SCISSOR_TEST)

    GL.glViewport(
        int(0.0 + (width - min) / 2.0),
        int(0.0 + (height - min) / 2.0),
        min,
        min,
    )


program_start_time = glfw.get_time()


# doc-region-begin draw a triangle
def draw_a_quadrilateral() -> None:
    GL.glColor3f(0.578123, 0.0, 1.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex2f(-1.0, -0.3)
    GL.glVertex2f(-0.8, -0.3)
    GL.glVertex2f(-0.8, 0.3)
    GL.glVertex2f(-1.0, 0.3)
    GL.glEnd()


# doc-region-end draw a triangle


# doc-region-begin draw x squared precomputed
def draw_x_squared_with_precomputed_values() -> None:
    # f(x) = x^2

    GL.glColor3f(1.0, 1.0, 1.0)
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(-1.0, 1.0)
    GL.glVertex2f(-0.9, 0.81)

    GL.glVertex2f(-0.9, 0.81)
    GL.glVertex2f(-0.8, 0.64)

    GL.glVertex2f(-0.8, 0.64)
    GL.glVertex2f(-0.7, 0.49)

    GL.glVertex2f(-0.7, 0.49)
    GL.glVertex2f(-0.6, 0.36)

    GL.glVertex2f(-0.6, 0.36)
    GL.glVertex2f(-0.5, 0.25)

    GL.glVertex2f(-0.5, 0.25)
    GL.glVertex2f(-0.4, 0.16)

    GL.glVertex2f(-0.4, 0.16)
    GL.glVertex2f(-0.3, 0.09)

    GL.glVertex2f(-0.3, 0.09)
    GL.glVertex2f(-0.2, 0.04)

    GL.glVertex2f(-0.2, 0.04)
    GL.glVertex2f(-0.1, 0.01)

    GL.glVertex2f(-0.1, 0.01)
    GL.glVertex2f(0.0, 0.0)

    GL.glVertex2f(0.0, 0.0)
    GL.glVertex2f(0.1, 0.01)

    GL.glVertex2f(0.1, 0.01)
    GL.glVertex2f(0.2, 0.04)

    GL.glVertex2f(0.2, 0.04)
    GL.glVertex2f(0.3, 0.09)

    GL.glVertex2f(0.3, 0.09)
    GL.glVertex2f(0.4, 0.16)

    GL.glVertex2f(0.4, 0.16)
    GL.glVertex2f(0.5, 0.25)

    GL.glVertex2f(0.5, 0.25)
    GL.glVertex2f(0.6, 0.36)

    GL.glVertex2f(0.6, 0.36)
    GL.glVertex2f(0.7, 0.49)

    GL.glVertex2f(0.7, 0.49)
    GL.glVertex2f(0.8, 0.64)

    GL.glVertex2f(0.8, 0.64)
    GL.glVertex2f(0.9, 0.81)

    GL.glVertex2f(0.9, 0.81)
    GL.glVertex2f(1.0, 1.0)

    GL.glEnd()


# doc-region-end draw x squared precomputed


# doc-region-begin generic plot function
def plot(
    fn: Callable[[float], float], domain: tuple[float, float], interval: float
) -> None:
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(domain[0], fn(domain[0]))

    # >>> range(0,10)
    # range(0, 10)
    # >>> list(range(0,10))
    # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # >>> list(range(0,10,2))
    # [0, 2, 4, 6, 8]
    # >>> np.arange(.0,1.0,.2)
    # array([. , .2, .4, .6, .8])
    for x in np.arange(domain[0], domain[1], interval, dtype=float):
        # GL.glVertex is here twice because line segments are assumed to be in pairs
        GL.glVertex2f(x, fn(x))
        GL.glVertex2f(x, fn(x))
    GL.glEnd()


# doc-region-end generic plot function


# doc-region-begin draw (x minus 1/2)^2
def use_plot_function_for_x_minus_onehalf_squared() -> None:
    def x_minus_onehalf_squared(x) -> float:
        return (x - 0.5) ** 2

    GL.glColor3f(1.0, 0.0, 0.0)
    plot(fn=x_minus_onehalf_squared, domain=(-1, 1), interval=0.001)


# doc-region-end draw (x minus 1/2)^2


# doc-region-begin draw an oscillating triangle
def draw_an_oscillating_triangle(elapsed_time_in_seconds: float) -> None:
    # math.sin uses radians
    offset_x = math.sin(elapsed_time_in_seconds)
    # to use degrees, you would do
    # offset_x = math.sin(math.radians(elapsed_time_in_seconds))

    float_between_0_and_1 = abs(math.sin(elapsed_time_in_seconds))
    # a float between 0 and 1 so that the color of the triagle changes over time
    GL.glColor3f(float_between_0_and_1, float_between_0_and_1, 1.0)
    GL.glBegin(GL.GL_TRIANGLES)
    GL.glVertex2f(0.0 + offset_x, 0.0)
    GL.glVertex2f(0.5 + offset_x, 0.0)
    GL.glVertex2f(0.0 + offset_x, 0.5)
    GL.glEnd()


# doc-region-end draw an oscillating triangle


# doc-region-begin unnamed_function
def use_plot_function_with_unnamed_function(
    elapsed_time_in_seconds: float,
) -> None:
    GL.glColor3f(1.0, 0.0, 1.0)
    plot(
        fn=lambda x: math.cos(x + elapsed_time_in_seconds * 3.0),
        domain=(-1, 1),
        interval=0.01,
    )


# doc-region-end unnamed_function


# doc-region-begin circle
def draw_circle() -> None:
    GL.glBegin(GL.GL_TRIANGLES)

    theta_increment: float = 0.01
    scale_radius: float = 0.1

    GL.glColor3f(1.0, 1.0, 1.0)

    for theta in np.arange(0.0, 2 * math.pi, theta_increment):
        GL.glVertex2f(0.0, 0.0)
        GL.glVertex2f(
            scale_radius * math.cos(theta), scale_radius * math.sin(theta)
        )
        GL.glVertex2f(
            scale_radius * math.cos(theta + theta_increment),
            scale_radius * math.sin(theta + theta_increment),
        )
    GL.glEnd()


# doc-region-end circle


# doc-region-begin event loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    elapsed_time_in_seconds: float = glfw.get_time() - program_start_time

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    draw_in_square_viewport()
    draw_a_quadrilateral()
    draw_an_oscillating_triangle(elapsed_time_in_seconds)
    draw_x_squared_with_precomputed_values()
    use_plot_function_for_x_minus_onehalf_squared()
    use_plot_function_with_unnamed_function(elapsed_time_in_seconds)
    draw_circle()

    glfw.swap_buffers(window)
# doc-region-end event loop

glfw.terminate()
