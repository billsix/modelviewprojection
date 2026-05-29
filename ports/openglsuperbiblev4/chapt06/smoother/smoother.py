# smoother.py
# Antialiasing demo: a starry-night scene that toggles between
# point/line/polygon smoothing and "normal" (jaggy) rendering. The C++
# original used a GLUT right-click menu; replaced here with an ImGui
# checkbox.
# OpenGL SuperBible, Chapter 6
# Python port of Smoother.cpp by Richard S. Wright Jr.

import math
import os
import random
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer



PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit control button
SCREEN_X = 800
SCREEN_Y = 600
SMALL_STARS = 100
MEDIUM_STARS = 40
LARGE_STARS = 15

small_stars = []
medium_stars = []
large_stars = []

antialiased: bool = True


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glColor3f(1.0, 1.0, 1.0)

    # Small stars
    GL.glPointSize(1.0)
    GL.glBegin(GL.GL_POINTS)
    for sx, sy in small_stars:
        GL.glVertex2f(sx, sy)
    GL.glEnd()

    GL.glPointSize(3.05)
    GL.glBegin(GL.GL_POINTS)
    for sx, sy in medium_stars:
        GL.glVertex2f(sx, sy)
    GL.glEnd()

    GL.glPointSize(5.5)
    GL.glBegin(GL.GL_POINTS)
    for sx, sy in large_stars:
        GL.glVertex2f(sx, sy)
    GL.glEnd()

    # The "moon"
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    x, y, r = 700.0, 500.0, 50.0
    GL.glVertex2f(x, y)
    angle = 0.0
    while angle < 2.0 * 3.141592:
        GL.glVertex2f(x + math.cos(angle) * r, y + math.sin(angle) * r)
        angle += 0.1
    GL.glVertex2f(x + r, y)
    GL.glEnd()

    # Distant horizon
    GL.glLineWidth(3.5)
    GL.glBegin(GL.GL_LINE_STRIP)
    for px, py in [
        (0.0, 25.0), (50.0, 100.0), (100.0, 25.0), (225.0, 125.0),
        (300.0, 50.0), (375.0, 100.0), (460.0, 25.0), (525.0, 100.0),
        (600.0, 20.0), (675.0, 70.0), (750.0, 25.0), (800.0, 90.0),
    ]:
        GL.glVertex2f(px, py)
    GL.glEnd()


def apply_antialiasing(enabled: bool) -> None:
    if enabled:
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_BLEND)
        GL.glEnable(GL.GL_POINT_SMOOTH)
        GL.glHint(GL.GL_POINT_SMOOTH_HINT, GL.GL_NICEST)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)
        GL.glEnable(GL.GL_POLYGON_SMOOTH)
        GL.glHint(GL.GL_POLYGON_SMOOTH_HINT, GL.GL_NICEST)
    else:
        GL.glDisable(GL.GL_BLEND)
        GL.glDisable(GL.GL_LINE_SMOOTH)
        GL.glDisable(GL.GL_POINT_SMOOTH)
        GL.glDisable(GL.GL_POLYGON_SMOOTH)


def setup_rc() -> None:
    random.seed(0)
    for _ in range(SMALL_STARS):
        sx = float(random.randint(0, SCREEN_X - 1))
        sy = float(random.randint(0, SCREEN_Y - 100 - 1)) + 100.0
        small_stars.append((sx, sy))
    for _ in range(MEDIUM_STARS):
        sx = float(random.randint(0, SCREEN_X * 10 - 1)) / 10.0
        sy = float(random.randint(0, SCREEN_Y - 100 - 1)) + 100.0
        medium_stars.append((sx, sy))
    for _ in range(LARGE_STARS):
        sx = float(random.randint(0, SCREEN_X * 10 - 1)) / 10.0
        sy = float(random.randint(0, (SCREEN_Y - 100) * 10 - 1)) / 10.0 + 100.0
        large_stars.append((sx, sy))

    GL.glClearColor(0.0, 0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluOrtho2D(0.0, SCREEN_X, 0.0, SCREEN_Y)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    global antialiased
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Render", True):
        changed, antialiased = imgui.menu_item(
            "Antialiased rendering", "", antialiased, True)
        if changed:
            apply_antialiasing(antialiased)
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(
        800, 600, "Smoothing Out The Jaggies", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)

    _window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw
    # key callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    apply_antialiasing(antialiased)
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

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
