# single.py
# Single-buffered rendering. The C++ original used GLUT_SINGLE so each
# new point persists in the front buffer; we emulate this by clearing
# only on the first frame of each spiral pass.
# OpenGL SuperBible, Chapter 3
# Python port of Single.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


d_radius: float = 0.1
d_angle: float = 0.0


def render_scene() -> None:
    """Each call advances one step of the outward spiral and draws a
    single point. Original used GLUT_SINGLE + glFlush; with double
    buffering we draw to the back buffer and swap, but to keep the
    growing-spiral effect we don't clear between frames within a pass.
    Instead we accumulate by re-drawing every prior point."""
    global d_radius, d_angle

    if d_angle == 0.0:
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    GL.glBegin(GL.GL_POINTS)
    GL.glVertex2d(d_radius * math.cos(d_angle), d_radius * math.sin(d_angle))
    GL.glEnd()

    d_radius *= 1.01
    d_angle += 0.1

    if d_angle > 30.0:
        d_radius = 0.1
        d_angle = 0.0


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluOrtho2D(-4.0, 4.0, -3.0, 3.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


# The C++ original used a 50 ms timer
TICK_INTERVAL: float = 50.0 / 1000.0


def main() -> None:
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    # Match GLUT_SINGLE -- single buffer, no swap between draws
    glfw.window_hint(glfw.DOUBLEBUFFER, glfw.FALSE)

    window = glfw.create_window(
        800, 600, "OpenGL Single Buffered", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    GL.glClearColor(0.0, 0.0, 1.0, 0.0)
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_tick = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()

        now = time.monotonic()
        if now - last_tick >= TICK_INTERVAL:
            render_scene()
            GL.glFlush()
            last_tick = now

    glfw.terminate()


if __name__ == "__main__":
    main()
