# lines.py
# Demonstrates primitive GL_LINES
# OpenGL SuperBible, Chapter 3
# Python port of Lines.cpp by Richard S. Wright Jr.

import math
import os
import sys

import glfw
import OpenGL.GL as GL



GL_PI = 3.1415

x_rot: float = 0.0
y_rot: float = 0.0


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    GL.glPushMatrix()
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)

    GL.glBegin(GL.GL_LINES)
    z = 0.0
    angle = 0.0
    while angle <= GL_PI:
        x = 50.0 * math.sin(angle)
        y = 50.0 * math.cos(angle)
        GL.glVertex3f(x, y, z)
        x = 50.0 * math.sin(angle + GL_PI)
        y = 50.0 * math.cos(angle + GL_PI)
        GL.glVertex3f(x, y, z)
        angle += GL_PI / 20.0
    GL.glEnd()

    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glColor3f(0.0, 1.0, 0.0)


def change_size(w: int, h: int) -> None:
    n_range = 100.0
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if w <= h:
        GL.glOrtho(-n_range, n_range, -n_range * h / w, n_range * h / w,
                   -n_range, n_range)
    else:
        GL.glOrtho(-n_range * w / h, n_range * w / h, -n_range, n_range,
                   -n_range, n_range)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def handle_special_keys(window) -> None:
    global x_rot, y_rot
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        x_rot -= 5.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        x_rot += 5.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        y_rot -= 5.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        y_rot += 5.0


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "Lines Example", None, None)
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
        handle_special_keys(window)
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
