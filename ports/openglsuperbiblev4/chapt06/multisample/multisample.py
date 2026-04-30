# multisample.py
# Sphereworld with GL_MULTISAMPLE enabled. Same body as
# chapt05/sphereworld; only the window hint and glEnable differ.
# OpenGL SuperBible, Chapter 6
# Python port of multisample.cpp by Richard S. Wright Jr.

import math
import os
import random
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU

from modelviewprojection.mathutils import Vector3D, plane_equation



NUM_SPHERES = 30
sphere_positions = []
camera_x: float = 0.0
camera_y: float = 0.0
camera_z: float = 0.0
camera_yaw: float = 0.0
f_light_pos = (-100.0, 100.0, 50.0, 1.0)
f_no_light = (0.0, 0.0, 0.0, 0.0)
f_low_light = (0.25, 0.25, 0.25, 1.0)
f_bright_light = (1.0, 1.0, 1.0, 1.0)
shadow_mat = None
y_rot: float = 0.0


def make_planar_shadow_matrix(
    pn: Vector3D, pd: float, lp: "tuple[float, float, float, float]"
) -> "np.ndarray":
    a, b, c, d = pn.x, pn.y, pn.z, pd
    dx, dy, dz = -lp[0], -lp[1], -lp[2]
    return np.array(
        [
            b*dy+c*dz, -a*dy, -a*dz, 0.0,
            -b*dx, a*dx+c*dz, -b*dz, 0.0,
            -c*dx, -c*dy, a*dx+b*dy, 0.0,
            -d*dx, -d*dy, -d*dz, a*dx+b*dy+c*dz,
        ], dtype=np.float32,
    )


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


def apply_camera_transform() -> None:
    GL.glRotatef(-math.degrees(camera_yaw), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera_x, -camera_y, -camera_z)


def draw_ground() -> None:
    strip = -20.0
    while strip <= 20.0:
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        GL.glNormal3f(0.0, 1.0, 0.0)
        run = 20.0
        while run >= -20.0:
            GL.glVertex3f(strip, -0.4, run)
            GL.glVertex3f(strip + 1.0, -0.4, run)
            run -= 1.0
        GL.glEnd()
        strip += 1.0


def draw_inhabitants(n_shadow: int) -> None:
    global y_rot
    if n_shadow == 0:
        y_rot += 0.5
    else:
        GL.glColor3f(0.0, 0.0, 0.0)
    if n_shadow == 0:
        GL.glColor3f(0.0, 1.0, 0.0)
    for sx, sy, sz in sphere_positions:
        GL.glPushMatrix()
        GL.glTranslatef(sx, sy, sz)
        draw_solid_sphere(0.3, 17, 9)
        GL.glPopMatrix()
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.1, -2.5)
    if n_shadow == 0:
        GL.glColor3f(0.0, 0.0, 1.0)
    GL.glPushMatrix()
    GL.glRotatef(-y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    draw_solid_sphere(0.1, 17, 9)
    GL.glPopMatrix()
    if n_shadow == 0:
        GL.glColor3f(1.0, 0.0, 0.0)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_bright_light)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_torus(0.35, 0.15, 61, 37)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_no_light)
    GL.glPopMatrix()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    apply_camera_transform()
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, f_light_pos)
    GL.glColor3f(0.60, 0.40, 0.10)
    draw_ground()
    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glPushMatrix()
    GL.glMultMatrixf(shadow_mat)
    draw_inhabitants(1)
    GL.glPopMatrix()
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_DEPTH_TEST)
    draw_inhabitants(0)
    GL.glPopMatrix()


def setup_rc() -> None:
    global shadow_mat
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

    p1, p2, p3 = (Vector3D(0.0, -0.4, 0.0), Vector3D(10.0, -0.4, 0.0),
                  Vector3D(5.0, -0.4, -5.0))
    pn, pd = plane_equation(p1, p2, p3)
    shadow_mat = make_planar_shadow_matrix(pn, pd, f_light_pos)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    random.seed(0)
    for _ in range(NUM_SPHERES):
        sx = (random.randint(0, 399) - 200) * 0.1
        sz = (random.randint(0, 399) - 200) * 0.1
        sphere_positions.append((sx, 0.0, sz))

    # Multisample -- the difference from chapt05/sphereworld
    GL.glEnable(GL.GL_MULTISAMPLE)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 50.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def handle_camera_keys(window) -> None:
    global camera_x, camera_z, camera_yaw
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera_x += 0.1 * math.sin(camera_yaw)
        camera_z -= 0.1 * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera_x -= 0.1 * math.sin(camera_yaw)
        camera_z += 0.1 * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera_yaw += 0.1
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera_yaw -= 0.1


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(
        800, 600, "OpenGL SphereWorld Demo Multisamples", None, None
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

    while not glfw.window_should_close(window):
        glfw.poll_events()
        handle_camera_keys(window)
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
