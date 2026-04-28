# nurbs.py
# A NURBS surface rendered with gluNurbsSurface. 4x4 control point grid;
# the surface is filled and lit, with red control points shown.
# OpenGL SuperBible, Chapter 10
# Python port of Nurbs.cpp by Richard S. Wright Jr.

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


# 4x4 grid of control points
ctrl_points: np.ndarray = np.array(
    [
        [[-6.0, -6.0, 0.0], [-6.0, -2.0, 0.0], [-6.0, 2.0, 0.0], [-6.0, 6.0, 0.0]],
        [[-2.0, -6.0, 0.0], [-2.0, -2.0, 8.0], [-2.0, 2.0, 8.0], [-2.0, 6.0, 0.0]],
        [[2.0, -6.0, 0.0], [2.0, -2.0, 8.0], [2.0, 2.0, 8.0], [2.0, 6.0, 0.0]],
        [[6.0, -6.0, 0.0], [6.0, -2.0, 0.0], [6.0, 2.0, 0.0], [6.0, 6.0, 0.0]],
    ],
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
    for row in ctrl_points:
        for p in row:
            GL.glVertex3f(*p)
    GL.glEnd()


def render_scene() -> None:
    GL.glColor3ub(0, 0, 220)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glRotatef(330.0, 1.0, 0.0, 0.0)

    GLU.gluBeginSurface(p_nurb)
    GLU.gluNurbsSurface(p_nurb, knots, knots, ctrl_points, GL.GL_MAP2_VERTEX_3)
    GLU.gluEndSurface(p_nurb)

    draw_points()
    GL.glPopMatrix()


def setup_rc() -> None:
    global p_nurb
    specular = (0.7, 0.7, 0.7, 1.0)
    shine = (100.0,)

    GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, specular)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SHININESS, shine)
    GL.glEnable(GL.GL_AUTO_NORMAL)

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


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    
    window_width, window_height = _common.resolve_default_window_size()
    window = glfw.create_window(window_width, window_height, "NURBS Surface", None, None)
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
