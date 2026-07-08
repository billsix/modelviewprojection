# stencil.py
# Stencil test demo: a spiral pattern is etched into the stencil buffer,
# then a bouncing red square is drawn only outside the spiral.
# OpenGL SuperBible, Chapter 3
# Python port of Stencil.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item


def imgui_menubar() -> None:
    # All controls in the top menubar; this demo has only Quit.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


x: float = 0.0
y: float = 0.0
rsize: float = 25.0
xstep: float = 1.0
ystep: float = 1.0
window_width: float = 100.0
window_height: float = 100.0


def render_scene() -> None:
    GL.glClearColor(0.0, 0.0, 1.0, 0.0)
    GL.glClearStencil(0)
    GL.glEnable(GL.GL_STENCIL_TEST)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_STENCIL_BUFFER_BIT)

    # Drawing increments stencil but writes no color
    GL.glStencilFunc(GL.GL_NEVER, 0x0, 0x0)
    GL.glStencilOp(GL.GL_INCR, GL.GL_INCR, GL.GL_INCR)

    GL.glColor3f(1.0, 1.0, 1.0)
    GL.glBegin(GL.GL_LINE_STRIP)
    d_radius = 0.1
    d_angle = 0.0
    while d_angle < 400.0:
        GL.glVertex2d(
            d_radius * math.cos(d_angle), d_radius * math.sin(d_angle)
        )
        d_radius *= 1.002
        d_angle += 0.1
    GL.glEnd()

    # Draw only where stencil != 1
    GL.glStencilFunc(GL.GL_NOTEQUAL, 0x1, 0x1)
    GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_KEEP)

    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glRectf(x, y, x + rsize, y - rsize)

    # Disable so the imgui menubar isn't clipped by the etched spiral
    # (re-enabled at the top of render_scene each frame).
    GL.glDisable(GL.GL_STENCIL_TEST)


def tick() -> None:
    global x, y, xstep, ystep
    if x > window_width - rsize or x < -window_width:
        xstep = -xstep
    if y > window_height or y < -window_height + rsize:
        ystep = -ystep
    if x > window_width - rsize:
        x = window_width - rsize - 1
    if y > window_height:
        y = window_height - 1
    x += xstep
    y += ystep


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    aspect = float(w) / float(h)
    if w <= h:
        window_width = 100.0
        window_height = 100.0 / aspect
        GL.glOrtho(-100.0, 100.0, -window_height, window_height, 1.0, -1.0)
    else:
        window_width = 100.0 * aspect
        window_height = 100.0
        GL.glOrtho(-window_width, window_width, -100.0, 100.0, 1.0, -1.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


TICK_INTERVAL: float = 33.0 / 1000.0


def main() -> None:
    global _window

    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    # Request a stencil buffer (matching GLUT_STENCIL)
    glfw.window_hint(glfw.STENCIL_BITS, 8)

    window = glfw.create_window(800, 600, "OpenGL Stencil Test", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_tick = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        now = time.monotonic()
        if now - last_tick >= TICK_INTERVAL:
            tick()
            last_tick = now

        render_scene()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
