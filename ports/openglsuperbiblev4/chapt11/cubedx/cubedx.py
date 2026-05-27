# cubedx.py
# Demonstrates rendering with indexed vertex arrays via
# glVertexPointer + glDrawElements.
# OpenGL SuperBible, Chapter 11
# Python port of CubeDX.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU



corners: np.ndarray = np.array(
    [-25.0, 25.0, 25.0,    # 0 -- front
     25.0, 25.0, 25.0,     # 1
     25.0, -25.0, 25.0,    # 2
     -25.0, -25.0, 25.0,   # 3
     -25.0, 25.0, -25.0,   # 4 -- back
     25.0, 25.0, -25.0,    # 5
     25.0, -25.0, -25.0,   # 6
     -25.0, -25.0, -25.0],
    dtype=np.float32,
)

indexes: np.ndarray = np.array(
    [0, 1, 2, 3,   # Front
     4, 5, 1, 0,   # Top
     3, 2, 6, 7,   # Bottom
     5, 4, 7, 6,   # Back
     1, 5, 6, 2,   # Right
     4, 0, 3, 7],  # Left
    dtype=np.uint8,
)

x_rot: float = 0.0
y_rot: float = 0.0


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -200.0)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    # C++ original wrote (0,0,1) here -- y_rot rotating about Z, which
    # makes LEFT/RIGHT spin the cube like a steering wheel and looks
    # like warping once x_rot has tilted the cube.  Use the Y axis so
    # LEFT/RIGHT does the expected yaw.
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)

    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glVertexPointer(3, GL.GL_FLOAT, 0, corners)
    GL.glDrawElements(GL.GL_QUADS, 24, GL.GL_UNSIGNED_BYTE, indexes)

    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    GL.glColor3ub(0, 0, 0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 1000.0)
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
    window = glfw.create_window(800, 600, "Cube DX", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

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
