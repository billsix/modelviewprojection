# simple.py
# The Simplest OpenGL program with GLFW (was GLUT in the original)
# OpenGL SuperBible, Chapter 2
# Python port of Simple.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import OpenGL.GL as GL



def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glFlush()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 1.0, 1.0)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    # The original used GLUT_SINGLE | GLUT_RGBA -- single-buffered.
    # GLFW windows are double-buffered by default; the result is the
    # same blue rectangle once swap_buffers runs.
    window = glfw.create_window(250, 250, "Simple", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    setup_rc()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
