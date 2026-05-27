# atom.py
# Demonstrates OpenGL coordinate transformation: a nucleus with three
# orbiting electrons, each defined in a coordinate frame relative to
# the nucleus via glPushMatrix/glRotatef/glTranslatef/glPopMatrix.
# OpenGL SuperBible, Chapter 4
# Python port of Atom.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import OpenGL.GL as GL



x_rot: float = 0.0
y_rot: float = 0.0

# Angle of revolution around the nucleus, in degrees. Computed each
# frame from elapsed time; the C++ original advanced this by 10° on a
# 100 ms timer (= 100°/sec), but stepping it once per render call
# decouples motion smoothness from animation rate.
f_elect1: float = 0.0
ELECTRON_DEG_PER_SEC: float = 100.0
start_time: float = 0.0


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    """Replacement for glutSolidSphere. Builds the sphere as a stack of
    GL_QUAD_STRIPs, one per latitude band."""
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

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -100.0)

    # Red nucleus
    GL.glColor3ub(255, 0, 0)
    draw_solid_sphere(10.0, 15, 15)

    # Yellow electrons
    GL.glColor3ub(255, 255, 0)

    # First orbit
    GL.glPushMatrix()
    GL.glRotatef(f_elect1, 0.0, 1.0, 0.0)
    GL.glTranslatef(90.0, 0.0, 0.0)
    draw_solid_sphere(6.0, 15, 15)
    GL.glPopMatrix()

    # Second orbit
    GL.glPushMatrix()
    GL.glRotatef(45.0, 0.0, 0.0, 1.0)
    GL.glRotatef(f_elect1, 0.0, 1.0, 0.0)
    GL.glTranslatef(-70.0, 0.0, 0.0)
    draw_solid_sphere(6.0, 15, 15)
    GL.glPopMatrix()

    # Third orbit
    GL.glPushMatrix()
    GL.glRotatef(360.0 - 45.0, 0.0, 0.0, 1.0)
    GL.glRotatef(f_elect1, 0.0, 1.0, 0.0)
    GL.glTranslatef(0.0, 0.0, 60.0)
    draw_solid_sphere(6.0, 15, 15)
    GL.glPopMatrix()


def update_animation() -> None:
    """Advance the orbital angle based on elapsed time. Called every
    frame so motion stays smooth at the render framerate."""
    global f_elect1
    f_elect1 = ((time.monotonic() - start_time) * ELECTRON_DEG_PER_SEC) % 360.0


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    n_range = 100.0
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if w <= h:
        GL.glOrtho(-n_range, n_range, -n_range * h / w, n_range * h / w,
                   -n_range * 2.0, n_range * 2.0)
    else:
        GL.glOrtho(-n_range * w / h, n_range * w / h, -n_range, n_range,
                   -n_range * 2.0, n_range * 2.0)
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
    global start_time

    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "OpenGL Atom", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.swap_interval(1)  # vsync, ~60 Hz on standard displays
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    start_time = time.monotonic()
    last_frame = start_time

    while not glfw.window_should_close(window):
        now = time.monotonic()
        dt = now - last_frame
        last_frame = now

        glfw.poll_events()
        handle_special_keys(window, dt)
        update_animation()
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
