# scissor.py
# Demonstrates the scissor test
# OpenGL SuperBible, Chapter 3
# Python port of Scissor.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU



def render_scene() -> None:
    # Clear blue window
    GL.glClearColor(0.0, 0.0, 1.0, 0.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    # Scissor a smaller red region
    GL.glClearColor(1.0, 0.0, 0.0, 0.0)
    GL.glScissor(100, 100, 600, 400)
    GL.glEnable(GL.GL_SCISSOR_TEST)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    # And an even smaller green rectangle inside
    GL.glClearColor(0.0, 1.0, 0.0, 0.0)
    GL.glScissor(200, 200, 400, 200)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    GL.glDisable(GL.GL_SCISSOR_TEST)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluOrtho2D(-4.0, 4.0, -3.0, 3.0)
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

    window = glfw.create_window(800, 600, "OpenGL Scissor", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
