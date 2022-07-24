import sys
import os
import math
from OpenGL.GL import *
import glfw
import numpy as np

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

glClearColor(0.0, 0.0, 0.0, 1.0)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()


def draw_in_square_viewport() -> None:

    glClearColor(0.2, 0.2, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)

    min = width if width < height else height

    glEnable(GL_SCISSOR_TEST)
    glScissor(
        int((width - min) / 2.0),
        int((height - min) / 2.0),
        min,
        min,
    )

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    glViewport(
        int(0.0 + (width - min) / 2.0),
        int(0.0 + (height - min) / 2.0),
        min,
        min,
    )


program_start_time = glfw.get_time()


while not glfw.window_should_close(window):
    glfw.poll_events()

    elapsed_time_in_seconds = glfw.get_time() - program_start_time

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    draw_in_square_viewport()

    glColor3f(0.578123, 0.0, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(-1.0, -0.3)
    glVertex2f(-0.8, -0.3)
    glVertex2f(-0.8, 0.3)
    glVertex2f(-1.0, 0.3)
    glEnd()

    # math.sin uses radians
    offset_x = math.sin(elapsed_time_in_seconds)
    # to use degrees, you would do
    # offset_x = math.sin(math.radians(elapsed_time_in_seconds))

    float_between_0_and_1 = abs(math.sin(elapsed_time_in_seconds))
    # a float between 0 and 1 so that the color of the triagle changes over time
    glColor3f(float_between_0_and_1, float_between_0_and_1, 1.0)
    glBegin(GL_TRIANGLES)
    glVertex2f(0.0 + offset_x, 0.0)
    glVertex2f(0.5 + offset_x, 0.0)
    glVertex2f(0.0 + offset_x, 0.5)
    glEnd()

    # f(x) = x^2

    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINES)
    glVertex2f(-1.0, 1.0)
    glVertex2f(-0.9, 0.81)

    glVertex2f(-0.9, 0.81)
    glVertex2f(-0.8, 0.6400000000000001)

    glVertex2f(-0.8, 0.6400000000000001)
    glVertex2f(-0.7, 0.48999999999999994)

    glVertex2f(-0.7, 0.48999999999999994)
    glVertex2f(-0.6, 0.36)

    glVertex2f(-0.6, 0.36)
    glVertex2f(-0.5, 0.25)

    glVertex2f(-0.5, 0.25)
    glVertex2f(-0.4, 0.16000000000000003)

    glVertex2f(-0.4, 0.16000000000000003)
    glVertex2f(-0.3, 0.09)

    glVertex2f(-0.3, 0.09)
    glVertex2f(-0.2, 0.04000000000000001)

    glVertex2f(-0.2, 0.04000000000000001)
    glVertex2f(-0.1, 0.010000000000000002)

    glVertex2f(-0.1, 0.010000000000000002)
    glVertex2f(0.0, 0.0)

    glVertex2f(0.0, 0.0)
    glVertex2f(0.1, 0.010000000000000002)

    glVertex2f(0.1, 0.010000000000000002)
    glVertex2f(0.2, 0.04000000000000001)

    glVertex2f(0.2, 0.04000000000000001)
    glVertex2f(0.3, 0.09)

    glVertex2f(0.3, 0.09)
    glVertex2f(0.4, 0.16000000000000003)

    glVertex2f(0.4, 0.16000000000000003)
    glVertex2f(0.5, 0.25)

    glVertex2f(0.5, 0.25)
    glVertex2f(0.6, 0.36)

    glVertex2f(0.6, 0.36)
    glVertex2f(0.7, 0.48999999999999994)

    glVertex2f(0.7, 0.48999999999999994)
    glVertex2f(0.8, 0.6400000000000001)

    glVertex2f(0.8, 0.6400000000000001)
    glVertex2f(0.9, 0.81)

    glVertex2f(0.9, 0.81)
    glVertex2f(1.0, 1.0)

    glEnd()

    # generic plot function
    def plot(fn, domain, interval):
        glBegin(GL_LINES)
        glVertex2f(domain[0], fn(domain[0]))

        # >>> range(0,10)
        # range(0, 10)
        # >>> list(range(0,10))
        # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        # >>> list(range(0,10,2))
        # [0, 2, 4, 6, 8]
        # >>> np.arange(0.0,1.0,0.2)
        # array([0. , 0.2, 0.4, 0.6, 0.8])
        for x in np.arange(domain[0], domain[1], interval):
            # glVertex is here twice because line segments are assumed to be in pairs
            glVertex2f(x, fn(x))
            glVertex2f(x, fn(x))
        glEnd()

    def x_minus_onehalf_squared(x):
        return (x - 0.5) ** 2

    glColor3f(1.0, 0.0, 0.0)
    plot(fn=x_minus_onehalf_squared, domain=(-1, 1), interval=0.001)

    glColor3f(1.0, 0.0, 1.0)
    plot(
        fn=lambda x: math.cos(x + elapsed_time_in_seconds * 3.0),
        domain=(-1, 1),
        interval=0.01,
    )

    glfw.swap_buffers(window)

glfw.terminate()
