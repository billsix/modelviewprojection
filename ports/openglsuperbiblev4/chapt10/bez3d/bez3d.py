# bez3d.py
# 3D Bezier surface using OpenGL evaluator (glMap2f).
# OpenGL SuperBible, Chapter 10
# Python port of Bez3d.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


ctrl_points = np.array(
    [
        [[-4.0, 0.0, 4.0], [-2.0, 4.0, 4.0], [4.0, 0.0, 4.0]],
        [[-4.0, 0.0, 0.0], [-2.0, 4.0, 0.0], [4.0, 0.0, 0.0]],
        [[-4.0, 0.0, -4.0], [-2.0, 4.0, -4.0], [4.0, 0.0, -4.0]],
    ],
    dtype=np.float32,
)


def draw_points() -> None:
    GL.glPointSize(5.0)
    GL.glBegin(GL.GL_POINTS)
    for row in ctrl_points:
        for p in row:
            GL.glVertex3f(*p)
    GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glRotatef(45.0, 0.0, 1.0, 0.0)
    GL.glRotatef(60.0, 1.0, 0.0, 0.0)

    GL.glMap2f(GL.GL_MAP2_VERTEX_3,
               0.0, 10.0, 3, 3,
               0.0, 10.0, 9, 3,
               ctrl_points)
    GL.glEnable(GL.GL_MAP2_VERTEX_3)

    GL.glMapGrid2f(10, 0.0, 10.0, 10, 0.0, 10.0)
    GL.glEvalMesh2(GL.GL_LINE, 0, 10, 0, 10)

    draw_points()
    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    GL.glColor3f(0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(-10.0, 10.0, -10.0, 10.0, -10.0, 10.0)
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
    window = glfw.create_window(800, 600, "3D Bezier Surface", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
