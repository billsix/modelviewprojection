# glrect.py
# Just draw a single rectangle in the middle of the screen
# OpenGL SuperBible, Chapter 2
# Python port of GLRect.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import OpenGL.GL as GL



def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glRectf(-25.0, 25.0, 25.0, -25.0)
    GL.glFlush()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 1.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1

    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()

    aspect_ratio = float(w) / float(h)
    if w <= h:
        GL.glOrtho(-100.0, 100.0, -100.0 / aspect_ratio,
                   100.0 / aspect_ratio, 1.0, -1.0)
    else:
        GL.glOrtho(-100.0 * aspect_ratio, 100.0 * aspect_ratio,
                   -100.0, 100.0, 1.0, -1.0)

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

    window = glfw.create_window(800, 600, "GLRect", None, None)
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
