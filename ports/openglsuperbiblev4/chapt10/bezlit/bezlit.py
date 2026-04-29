# bezlit.py
# Lit Bezier surface -- chapt10/bez3d with normal-vector evaluation
# (GL_AUTO_NORMAL) and lighting added.
# OpenGL SuperBible, Chapter 10
# Python port of Bezlit.cpp by Richard S. Wright Jr.

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


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    GL.glRotatef(45.0, 0.0, 1.0, 0.0)
    GL.glRotatef(60.0, 1.0, 0.0, 0.0)

    GL.glMap2f(GL.GL_MAP2_VERTEX_3, 0.0, 10.0, 3, 3, 0.0, 10.0, 9, 3,
               ctrl_points)
    GL.glEnable(GL.GL_MAP2_VERTEX_3)
    GL.glMapGrid2f(10, 0.0, 10.0, 10, 0.0, 10.0)
    GL.glEvalMesh2(GL.GL_FILL, 0, 10, 0, 10)
    GL.glPopMatrix()


def setup_rc() -> None:
    ambient = (0.3, 0.3, 0.3, 1.0)
    diffuse = (0.7, 0.7, 0.7, 1.0)
    light_pos = (20.0, 0.0, 0.0, 0.0)

    GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_AUTO_NORMAL)


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
    window = glfw.create_window(800, 600, "Lit Bezier Surface", None, None)
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
