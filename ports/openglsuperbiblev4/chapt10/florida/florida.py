# florida.py
# Polygon tessellation: an outline of Florida (with Lake Okeechobee)
# rendered three ways -- as line loops, as a tessellated concave
# polygon, and as a complex polygon with the lake as a hole.
# C++ used a right-click GLUT menu; replaced with an ImGui radio panel.
# OpenGL SuperBible, Chapter 10
# Python port of Florida.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


COAST: np.ndarray = np.array(
    [
        [-70.0, 30.0, 0.0], [-50.0, 30.0, 0.0], [-50.0, 27.0, 0.0],
        [-5.0, 27.0, 0.0], [0.0, 20.0, 0.0], [8.0, 10.0, 0.0],
        [12.0, 5.0, 0.0], [10.0, 0.0, 0.0], [15.0, -10.0, 0.0],
        [20.0, -20.0, 0.0], [20.0, -35.0, 0.0], [10.0, -40.0, 0.0],
        [0.0, -30.0, 0.0], [-5.0, -20.0, 0.0], [-12.0, -10.0, 0.0],
        [-13.0, -5.0, 0.0], [-12.0, 5.0, 0.0], [-20.0, 10.0, 0.0],
        [-30.0, 20.0, 0.0], [-40.0, 15.0, 0.0], [-50.0, 15.0, 0.0],
        [-55.0, 20.0, 0.0], [-60.0, 25.0, 0.0], [-70.0, 25.0, 0.0],
    ],
    dtype=np.float64,
)
LAKE: np.ndarray = np.array(
    [[10.0, -20.0, 0.0], [15.0, -25.0, 0.0],
     [10.0, -30.0, 0.0], [5.0, -25.0, 0.0]],
    dtype=np.float64,
)

DRAW_LOOPS = 0
DRAW_CONCAVE = 1
DRAW_COMPLEX = 2

i_method: int = DRAW_LOOPS


def _tess_loops() -> None:
    GL.glColor3f(0.0, 0.0, 0.0)
    GL.glBegin(GL.GL_LINE_LOOP)
    for p in COAST:
        GL.glVertex3dv(p)
    GL.glEnd()
    GL.glBegin(GL.GL_LINE_LOOP)
    for p in LAKE:
        GL.glVertex3dv(p)
    GL.glEnd()


def _tess_polygon(contours: list[np.ndarray]) -> None:
    GL.glColor3f(0.0, 1.0, 0.0)
    tess = GLU.gluNewTess()
    GLU.gluTessCallback(tess, GLU.GLU_TESS_BEGIN, GL.glBegin)
    GLU.gluTessCallback(tess, GLU.GLU_TESS_END, GL.glEnd)
    GLU.gluTessCallback(tess, GLU.GLU_TESS_VERTEX, GL.glVertex3dv)
    GLU.gluTessProperty(tess, GLU.GLU_TESS_WINDING_RULE,
                        GLU.GLU_TESS_WINDING_ODD)
    GLU.gluTessBeginPolygon(tess, None)
    for contour in contours:
        GLU.gluTessBeginContour(tess)
        for p in contour:
            GLU.gluTessVertex(tess, p, p)
        GLU.gluTessEndContour(tess)
    GLU.gluTessEndPolygon(tess)
    GLU.gluDeleteTess(tess)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    if i_method == DRAW_LOOPS:
        _tess_loops()
    elif i_method == DRAW_CONCAVE:
        _tess_polygon([COAST])
    else:  # DRAW_COMPLEX
        _tess_polygon([COAST, LAKE])


def setup_rc() -> None:
    GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    GL.glLineWidth(2.0)
    GL.glEnable(GL.GL_LINE_SMOOTH)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluOrtho2D(-80, 35, -50, 50)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_panel() -> None:
    global i_method
    imgui.begin("Florida")
    for label, value in [("Line Loops", DRAW_LOOPS),
                         ("Concave Polygon", DRAW_CONCAVE),
                         ("Complex Polygon", DRAW_COMPLEX)]:
        if imgui.radio_button(label, i_method == value):
            i_method = value
    imgui.end()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(500, 400, "Tesselated Florida", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        render_scene()
        imgui.new_frame()
        imgui_panel()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
