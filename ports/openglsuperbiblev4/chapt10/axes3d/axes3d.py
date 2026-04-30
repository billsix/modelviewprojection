# axes3d.py
# 3D unit axis model -- a useful visualization aid showing the X, Y, Z
# axes as colored arrows. Reimplemented inline; the original called
# gltDrawUnitAxes from gltools.
# OpenGL SuperBible, Chapter 10
# Python port of Axes3D.cpp by Richard S. Wright Jr.

import math
import os
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU



x_rot: float = 0.0
y_rot: float = 0.0


def draw_solid_cylinder(base_radius: float, top_radius: float, height: float, slices: int) -> None:
    """Replacement for gluCylinder side surface."""
    GL.glBegin(GL.GL_QUAD_STRIP)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        c, s = math.cos(a), math.sin(a)
        GL.glNormal3f(c, s, 0.0)
        GL.glVertex3f(c * base_radius, s * base_radius, 0.0)
        GL.glVertex3f(c * top_radius, s * top_radius, height)
    GL.glEnd()


def draw_solid_cone(base: float, height: float, slices: int) -> None:
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, 1.0)
    GL.glVertex3f(0.0, 0.0, height)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        c, s = math.cos(a), math.sin(a)
        GL.glVertex3f(c * base, s * base, 0.0)
    GL.glEnd()
    # Base disk
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, -1.0)
    GL.glVertex3f(0.0, 0.0, 0.0)
    for i in range(slices, -1, -1):
        a = 2.0 * math.pi * float(i) / slices
        GL.glVertex3f(math.cos(a) * base, math.sin(a) * base, 0.0)
    GL.glEnd()


def draw_unit_axes() -> None:
    """Draw three colored axes with cones at their tips. The original
    gltDrawUnitAxes drew red X, green Y, blue Z axes from origin to 1.0,
    each with a small cone arrowhead."""
    rod_radius = 0.025
    cone_radius = 0.06
    rod_length = 0.85
    cone_length = 0.15

    # +X axis -- red, rotated about Y so cylinder runs along +X
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(90.0, 0.0, 1.0, 0.0)
    draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    draw_solid_cone(cone_radius, cone_length, 20)
    GL.glPopMatrix()

    # +Y axis -- green, rotated about X so cylinder runs along +Y
    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    draw_solid_cone(cone_radius, cone_length, 20)
    GL.glPopMatrix()

    # +Z axis -- blue, default orientation
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glPushMatrix()
    draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    draw_solid_cone(cone_radius, cone_length, 20)
    GL.glPopMatrix()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -5.0)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_unit_axes()
    GL.glPopMatrix()


def setup_rc() -> None:
    white_light = (0.05, 0.05, 0.05, 1.0)
    source_light = (0.25, 0.25, 0.25, 1.0)
    light_pos = (-10.0, 5.0, 5.0, 1.0)

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, white_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 40.0)
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
    window = glfw.create_window(800, 600, "Unit Axis", None, None)
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
