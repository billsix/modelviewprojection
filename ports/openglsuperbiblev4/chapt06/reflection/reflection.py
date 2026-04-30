# reflection.py
# Planar reflection: the world is drawn twice -- once mirrored below
# the floor with the light flipped, then a transparent checkerboard
# floor is blended on top, then the world is drawn upright. Demonstrates
# blending + glScalef(1, -1, 1).
# OpenGL SuperBible, Chapter 6
# Python port of Reflection.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU



f_light_pos = (-100.0, 100.0, 50.0, 1.0)
f_light_pos_mirror = (-100.0, -100.0, 50.0, 1.0)
f_no_light = (0.0, 0.0, 0.0, 0.0)
f_low_light = (0.25, 0.25, 0.25, 1.0)
f_bright_light = (1.0, 1.0, 1.0, 1.0)

y_rot: float = 0.0


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        s0, c0 = math.sin(lat0), math.cos(lat0)
        s1, c1 = math.sin(lat1), math.cos(lat1)
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            GL.glNormal3f(cl * c0, sl * c0, s0)
            GL.glVertex3f(radius * cl * c0, radius * sl * c0, radius * s0)
            GL.glNormal3f(cl * c1, sl * c1, s1)
            GL.glVertex3f(radius * cl * c1, radius * sl * c1, radius * s1)
        GL.glEnd()


def draw_torus(major: float, minor: float, n_major: int, n_minor: int) -> None:
    major_step = 2.0 * math.pi / n_major
    minor_step = 2.0 * math.pi / n_minor
    for i in range(n_major):
        a0, a1 = i * major_step, (i + 1) * major_step
        x0, y0 = math.cos(a0), math.sin(a0)
        x1, y1 = math.cos(a1), math.sin(a1)
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        for j in range(n_minor + 1):
            b = j * minor_step
            cb, sb = math.cos(b), math.sin(b)
            r = minor * cb + major
            z = minor * sb
            GL.glNormal3f(x0 * cb, y0 * cb, sb)
            GL.glVertex3f(x0 * r, y0 * r, z)
            GL.glNormal3f(x1 * cb, y1 * cb, sb)
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()


def draw_ground() -> None:
    """Black-and-white transparent checkerboard at y=0."""
    extent = 20.0
    step = 0.5
    bounce = 0
    GL.glShadeModel(GL.GL_FLAT)
    strip = -extent
    while strip <= extent:
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        run = extent
        while run >= -extent:
            color = 1.0 if bounce % 2 == 0 else 0.0
            GL.glColor4f(color, color, color, 0.5)
            GL.glVertex3f(strip, 0.0, run)
            GL.glVertex3f(strip + step, 0.0, run)
            bounce += 1
            run -= step
        GL.glEnd()
        strip += step
    GL.glShadeModel(GL.GL_SMOOTH)


def draw_world() -> None:
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.5, -3.5)

    GL.glPushMatrix()
    GL.glRotatef(-y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    draw_solid_sphere(0.1, 17, 9)
    GL.glPopMatrix()

    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_torus(0.35, 0.15, 61, 37)
    GL.glPopMatrix()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPushMatrix()
    # Mirrored world: flip light below the floor too
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, f_light_pos_mirror)
    GL.glPushMatrix()
    GL.glFrontFace(GL.GL_CW)  # geometry mirrored, so CW now points "out"
    GL.glScalef(1.0, -1.0, 1.0)
    draw_world()
    GL.glFrontFace(GL.GL_CCW)
    GL.glPopMatrix()

    # Transparent floor on top of the reflection
    GL.glDisable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    draw_ground()
    GL.glDisable(GL.GL_BLEND)
    GL.glEnable(GL.GL_LIGHTING)

    # The real world above the floor
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, f_light_pos)
    draw_world()
    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(*f_low_light)
    GL.glCullFace(GL.GL_BACK)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, f_no_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, f_low_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, f_bright_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, f_bright_light)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 50.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, -0.4, 0.0)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


TICK_INTERVAL: float = 10.0 / 1000.0


def tick() -> None:
    global y_rot
    y_rot += 1.0


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(
        800, 600, "OpenGL Blending and Transparency", None, None
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
        now = time.monotonic()
        if now - last_tick >= TICK_INTERVAL:
            tick()
            last_tick = now
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
