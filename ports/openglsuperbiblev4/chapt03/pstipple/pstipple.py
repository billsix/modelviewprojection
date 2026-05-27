# pstipple.py
# Demonstrates polygon stippling
# OpenGL SuperBible, Chapter 3
# Python port of PStipple.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import numpy as np
import OpenGL.GL as GL



x_rot: float = 0.0
y_rot: float = 0.0

# Bitmap of camp fire (32x32 pixels = 128 bytes)
fire = np.array(
    [
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0xc0, 0x00, 0x00, 0x01, 0xf0,
        0x00, 0x00, 0x07, 0xf0, 0x0f, 0x00, 0x1f, 0xe0,
        0x1f, 0x80, 0x1f, 0xc0, 0x0f, 0xc0, 0x3f, 0x80,
        0x07, 0xe0, 0x7e, 0x00, 0x03, 0xf0, 0xff, 0x80,
        0x03, 0xf5, 0xff, 0xe0, 0x07, 0xfd, 0xff, 0xf8,
        0x1f, 0xfc, 0xff, 0xe8, 0xff, 0xe3, 0xbf, 0x70,
        0xde, 0x80, 0xb7, 0x00, 0x71, 0x10, 0x4a, 0x80,
        0x03, 0x10, 0x4e, 0x40, 0x02, 0x88, 0x8c, 0x20,
        0x05, 0x05, 0x04, 0x40, 0x02, 0x82, 0x14, 0x40,
        0x02, 0x40, 0x10, 0x80, 0x02, 0x64, 0x1a, 0x80,
        0x00, 0x92, 0x29, 0x00, 0x00, 0xb0, 0x48, 0x00,
        0x00, 0xc8, 0x90, 0x00, 0x00, 0x85, 0x10, 0x00,
        0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00,
    ],
    dtype=np.uint8,
)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    GL.glPushMatrix()
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)

    # Stop sign shape, drawn as a single polygon
    GL.glBegin(GL.GL_POLYGON)
    GL.glVertex2f(-20.0, 50.0)
    GL.glVertex2f(20.0, 50.0)
    GL.glVertex2f(50.0, 20.0)
    GL.glVertex2f(50.0, -20.0)
    GL.glVertex2f(20.0, -50.0)
    GL.glVertex2f(-20.0, -50.0)
    GL.glVertex2f(-50.0, -20.0)
    GL.glVertex2f(-50.0, 20.0)
    GL.glEnd()

    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glEnable(GL.GL_POLYGON_STIPPLE)
    GL.glPolygonStipple(fire)


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


ROT_DEG_PER_SEC: float = 90.0


def handle_special_keys(window, dt: float) -> None:
    global x_rot, y_rot
    step = ROT_DEG_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        x_rot -= step
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        x_rot += step
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        y_rot -= step
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        y_rot += step


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "Polygon Stippling", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    glfw.swap_interval(1)
    last_frame = time.monotonic()

    while not glfw.window_should_close(window):
        now = time.monotonic()
        dt = now - last_frame
        last_frame = now

        glfw.poll_events()
        handle_special_keys(window, dt)
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
