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

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


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

    GL.glMap1f(GL.GL_MAP1_VERTEX_3, 0.0, 100.0, 3, len(ctrl_points),
               ctrl_points)
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


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    
    window_width, window_height = _common.resolve_default_window_size()
    window = glfw.create_window(window_width, window_height, "2D Bezier Curve", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    impl = _common.init_imgui(window)
    win_state = _common.WindowState()

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        render_scene()
        
        imgui.new_frame()
        _common.draw_menubar(window, win_state)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()

    glfw.terminate()


if __name__ == "__main__":
    main()
