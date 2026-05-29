# bezier.py
# Demonstrates an OpenGL evaluator drawing a 2D Bezier curve from four
# control points.
# OpenGL SuperBible, Chapter 10
# Python port of Bezier.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item


ctrl_points = np.array(
    [
        [-4.0, 0.0, 0.0],
        [-6.0, 4.0, 0.0],
        [6.0, -4.0, 0.0],
        [4.0, 0.0, 0.0],
    ],
    dtype=np.float32,
)


def draw_points() -> None:
    GL.glPointSize(5.0)
    GL.glBegin(GL.GL_POINTS)
    for p in ctrl_points:
        GL.glVertex2f(p[0], p[1])
    GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    # PyOpenGL's glMap1f is a 4-arg wrapper -- stride/order come from
    # the array shape, not from explicit ints like the C signature.
    GL.glMap1f(GL.GL_MAP1_VERTEX_3, 0.0, 100.0, ctrl_points)
    GL.glEnable(GL.GL_MAP1_VERTEX_3)

    GL.glBegin(GL.GL_LINE_STRIP)
    for i in range(101):
        GL.glEvalCoord1f(float(i))
    GL.glEnd()

    draw_points()


def setup_rc() -> None:
    GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    GL.glColor3f(0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluOrtho2D(-10.0, 10.0, -10.0, 10.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    # All controls in the top menubar. This demo has no movement keys, so
    # only File -> Quit is offered.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "2D Bezier Curve", None, None)
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

    setup_rc()
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
