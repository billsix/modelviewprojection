# nurbc.py
# A NURBS curve rendered with gluNurbsCurve. Control points shown as
# red dots; curve drawn as filled mesh.
# OpenGL SuperBible, Chapter 10
# Python port of Nurbc.cpp by Richard S. Wright Jr.

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


ctrl_points: np.ndarray = np.array(
    [[-6.0, -6.0, 0.0], [2.0, -2.0, 8.0],
     [2.0, 6.0, 0.0], [6.0, 6.0, 0.0]],
    dtype=np.float32,
)
knots: np.ndarray = np.array(
    [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32,
)
p_nurb = None


def draw_points() -> None:
    GL.glPointSize(5.0)
    GL.glColor3ub(255, 0, 0)
    GL.glBegin(GL.GL_POINTS)
    for p in ctrl_points:
        GL.glVertex3f(*p)
    GL.glEnd()


def render_scene() -> None:
    GL.glColor3ub(0, 0, 220)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glRotatef(330.0, 1.0, 0.0, 0.0)

    GLU.gluBeginCurve(p_nurb)
    GLU.gluNurbsCurve(p_nurb, knots, ctrl_points, GL.GL_MAP1_VERTEX_3)
    GLU.gluEndCurve(p_nurb)

    draw_points()
    GL.glPopMatrix()


def setup_rc() -> None:
    global p_nurb
    GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    p_nurb = GLU.gluNewNurbsRenderer()
    GLU.gluNurbsProperty(p_nurb, GLU.GLU_SAMPLING_TOLERANCE, 25.0)
    GLU.gluNurbsProperty(p_nurb, GLU.GLU_DISPLAY_MODE, GLU.GLU_FILL)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, float(w) / float(h), 1.0, 40.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -20.0)


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
    window = glfw.create_window(800, 600, "NURBS Curve", None, None)
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
