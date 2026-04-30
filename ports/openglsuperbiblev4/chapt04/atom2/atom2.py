# atom2.py
# Same atom as chapt04/atom, but with perspective projection instead of
# orthographic. Demonstrates how nested transformations look when the
# scene has depth foreshortening.
# OpenGL SuperBible, Chapter 4
# Python port of Atom2.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU



x_rot: float = 0.0
y_rot: float = 0.0
f_elect1: float = 0.0


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        sin0, cos0 = math.sin(lat0), math.cos(lat0)
        sin1, cos1 = math.sin(lat1), math.cos(lat1)
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            GL.glNormal3f(cl * cos0, sl * cos0, sin0)
            GL.glVertex3f(radius * cl * cos0, radius * sl * cos0, radius * sin0)
            GL.glNormal3f(cl * cos1, sl * cos1, sin1)
            GL.glVertex3f(radius * cl * cos1, radius * sl * cos1, radius * sin1)
        GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # Red nucleus
    GL.glColor3ub(255, 0, 0)
    draw_solid_sphere(10.0, 15, 15)

    # Yellow electrons
    GL.glColor3ub(255, 255, 0)

    GL.glPushMatrix()
    GL.glRotatef(f_elect1, 0.0, 1.0, 0.0)
    GL.glTranslatef(90.0, 0.0, 0.0)
    draw_solid_sphere(6.0, 15, 15)
    GL.glPopMatrix()

    GL.glPushMatrix()
    GL.glRotatef(45.0, 0.0, 0.0, 1.0)
    GL.glRotatef(f_elect1, 0.0, 1.0, 0.0)
    GL.glTranslatef(-70.0, 0.0, 0.0)
    draw_solid_sphere(6.0, 15, 15)
    GL.glPopMatrix()

    GL.glPushMatrix()
    GL.glRotatef(360.0 - 45.0, 0.0, 0.0, 1.0)
    GL.glRotatef(f_elect1, 0.0, 1.0, 0.0)
    GL.glTranslatef(0.0, 0.0, 60.0)
    draw_solid_sphere(6.0, 15, 15)
    GL.glPopMatrix()


def tick() -> None:
    global f_elect1
    f_elect1 += 10.0
    if f_elect1 > 360.0:
        f_elect1 = 0.0


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    f_aspect = float(w) / float(h)
    GLU.gluPerspective(45.0, f_aspect, 1.0, 500.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -250.0)


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


TICK_INTERVAL: float = 100.0 / 1000.0


def main() -> None:
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(
        800, 600, "OpenGL Atom - Part Duex", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_tick = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        handle_special_keys(window)

        now = time.monotonic()
        if now - last_tick >= TICK_INTERVAL:
            tick()
            last_tick = now

        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
