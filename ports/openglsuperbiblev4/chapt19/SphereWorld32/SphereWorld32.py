# SphereWorld32.py
# A camera flying through a textured "sphere world" with a stenciled
# planar shadow on the ground. The original is a Win32 (no MFC)
# program that wrappered raw OpenGL with FSAA + VSync setup; the
# Python port uses GLFW with samples=4 for antialiasing.
#
# Keys: Up/Down/Left/Right move the camera; Esc to quit.
#
# OpenGL SuperBible, Chapter 19
# Python port of SphereWorld32.cpp by Richard S. Wright Jr.

import math
import os
import random
import sys
import time

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU

from modelviewprojection.mathutils import Vector3D, plane_equation



PWD = os.path.dirname(os.path.abspath(__file__))
NUM_SPHERES = 30
GROUND_TEXTURE, TORUS_TEXTURE, SPHERE_TEXTURE = 0, 1, 2
texture_files = ["grass.tga", "wood.tga", "orb.tga"]

window_width: int = 800
window_height: int = 600

light_pos = [-100.0, 100.0, 50.0, 1.0]
no_light = [0.0, 0.0, 0.0, 0.0]
low_light = [0.25, 0.25, 0.25, 1.0]
bright_light = [1.0, 1.0, 1.0, 1.0]

texture_objects = [0, 0, 0]
sphere_positions: list = []
shadow_matrix = np.identity(4, dtype=np.float32)
torus_list: int = 0
sphere_list: int = 0

camera_x: float = 0.0
camera_y: float = 0.0
camera_z: float = 0.0
camera_yaw: float = 0.0
y_rot: float = 0.0


def make_planar_shadow_matrix(
    plane_pts: "tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]",
) -> np.ndarray:
    """Cast light at light_pos onto the plane through plane_pts. Same
    column-major form as math3d.cpp's m3dMakePlanarShadowMatrix and
    chapt05/sphereworld -- the C++ original. The CCW plane_equation
    can flip w<0 on the transformed vertices, which OpenGL clips
    before perspective divide and the shadow disappears; negate the
    matrix when needed. See plans/notes-planar-shadow-w-clipping.md."""
    p1, p2, p3 = plane_pts
    pn, pd = plane_equation(Vector3D(*p1), Vector3D(*p2), Vector3D(*p3))
    a, b, c, d = pn.x, pn.y, pn.z, pd
    dx, dy, dz = -light_pos[0], -light_pos[1], -light_pos[2]
    s = 1.0 if (a * dx + b * dy + c * dz) > 0.0 else -1.0
    return np.array(
        [
            s*(b*dy + c*dz), s*-a*dy, s*-a*dz, 0.0,
            s*-b*dx, s*(a*dx + c*dz), s*-b*dz, 0.0,
            s*-c*dx, s*-c*dy, s*(a*dx + b*dy), 0.0,
            s*-d*dx, s*-d*dy, s*-d*dz, s*(a*dx + b*dy + c*dz),
        ],
        dtype=np.float32,
    )


def gl_draw_torus(major: float, minor: float, n_major: int, n_minor: int) -> None:
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
            u, v = float(i) / n_major, float(j) / n_minor
            GL.glNormal3f(x0 * cb, y0 * cb, sb)
            GL.glTexCoord2f(u, v)
            GL.glVertex3f(x0 * r, y0 * r, z)
            GL.glNormal3f(x1 * cb, y1 * cb, sb)
            GL.glTexCoord2f(u + 1.0 / n_major, v)
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()


def gl_draw_sphere(radius: float, slices: int, stacks: int) -> None:
    obj = GLU.gluNewQuadric()
    GLU.gluQuadricNormals(obj, GLU.GLU_SMOOTH)
    GLU.gluQuadricTexture(obj, GL.GL_TRUE)
    GLU.gluSphere(obj, radius, slices, stacks)
    GLU.gluDeleteQuadric(obj)


def draw_ground() -> None:
    f_extent = 20.0
    step = 1.0
    y = -0.4
    tex_step = 1.0 / (f_extent * 0.075)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[GROUND_TEXTURE])
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    s = 0.0
    strip = -f_extent
    while strip <= f_extent:
        t = 0.0
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        run = f_extent
        while run >= -f_extent:
            GL.glTexCoord2f(s, t); GL.glNormal3f(0.0, 1.0, 0.0)
            GL.glVertex3f(strip, y, run)
            GL.glTexCoord2f(s + tex_step, t); GL.glNormal3f(0.0, 1.0, 0.0)
            GL.glVertex3f(strip + step, y, run)
            t += tex_step
            run -= step
        GL.glEnd()
        s += tex_step
        strip += step


def draw_inhabitants(shadow: int) -> None:
    if shadow == 0:
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)
    else:
        GL.glColor4f(0.0, 0.0, 0.0, 0.75)

    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[SPHERE_TEXTURE])
    for sx, sz in sphere_positions:
        GL.glPushMatrix()
        GL.glTranslatef(sx, 0.0, sz)
        GL.glCallList(sphere_list)
        GL.glPopMatrix()

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.1, -2.5)
    GL.glPushMatrix()
    GL.glRotatef(-y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    GL.glCallList(sphere_list)
    GL.glPopMatrix()
    if shadow == 0:
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, bright_light)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[TORUS_TEXTURE])
    GL.glCallList(torus_list)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, no_light)
    GL.glPopMatrix()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT
               | GL.GL_STENCIL_BUFFER_BIT)
    GL.glPushMatrix()
    GL.glRotatef(-camera_yaw, 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera_x, -camera_y, -camera_z)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)

    GL.glColor3f(1.0, 1.0, 1.0)
    draw_ground()

    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnable(GL.GL_STENCIL_TEST)
    GL.glPushMatrix()
    GL.glMultMatrixf(shadow_matrix)
    draw_inhabitants(1)
    GL.glPopMatrix()
    GL.glDisable(GL.GL_STENCIL_TEST)
    GL.glDisable(GL.GL_BLEND)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_DEPTH_TEST)

    draw_inhabitants(0)
    GL.glPopMatrix()


def setup_rc() -> None:
    global shadow_matrix, torus_list, sphere_list, texture_objects
    GL.glStencilOp(GL.GL_INCR, GL.GL_INCR, GL.GL_INCR)
    GL.glClearStencil(0)
    GL.glStencilFunc(GL.GL_EQUAL, 0x0, 0x01)
    GL.glClearColor(*low_light)
    GL.glCullFace(GL.GL_BACK)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, no_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, low_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, bright_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, bright_light)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)

    plane_pts = [(0.0, -0.4, 0.0), (10.0, -0.4, 0.0), (5.0, -0.4, -5.0)]
    shadow_matrix = make_planar_shadow_matrix(plane_pts)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    random.seed(42)
    for _ in range(NUM_SPHERES):
        sx = ((random.randint(0, 399) - 200) * 0.1)
        sz = ((random.randint(0, 399) - 200) * 0.1)
        sphere_positions.append((sx, sz))

    GL.glEnable(GL.GL_TEXTURE_2D)
    texture_objects = list(GL.glGenTextures(3))
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
    for i, name in enumerate(texture_files):
        img = iio.imread(os.path.join(PWD, name))
        img = np.flipud(img)
        if img.ndim == 3 and img.shape[2] == 4:
            img = img[:, :, :3]
        img = np.ascontiguousarray(img, dtype=np.uint8)
        h, w = img.shape[:2]
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[i])
        GLU.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, GL.GL_RGB, w, h,
                              GL.GL_RGB, GL.GL_UNSIGNED_BYTE, img)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                           GL.GL_LINEAR_MIPMAP_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)

    GL.glLightModeli(GL.GL_LIGHT_MODEL_COLOR_CONTROL,
                     GL.GL_SEPARATE_SPECULAR_COLOR)

    torus_list = GL.glGenLists(2)
    sphere_list = torus_list + 1
    GL.glNewList(torus_list, GL.GL_COMPILE)
    gl_draw_torus(0.35, 0.15, 61, 37)
    GL.glEndList()
    GL.glNewList(sphere_list, GL.GL_COMPILE)
    gl_draw_sphere(0.1, 26, 13)
    GL.glEndList()


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    if h == 0:
        h = 1
    window_width, window_height = w, h
    GL.glViewport(0, 0, w, h)
    aspect = float(w) / float(h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, aspect, 1.0, 50.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


MOVE_UNITS_PER_SEC: float = 3.0
YAW_DEG_PER_SEC: float = 90.0
TORUS_DEG_PER_SEC: float = 30.0


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def handle_camera_keys(window, dt: float) -> None:
    global camera_x, camera_z, camera_yaw
    move = MOVE_UNITS_PER_SEC * dt
    yaw_rad = math.radians(camera_yaw)
    fwd_x = -math.sin(yaw_rad) * move
    fwd_z = -math.cos(yaw_rad) * move
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera_x += fwd_x
        camera_z += fwd_z
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera_x -= fwd_x
        camera_z -= fwd_z
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera_yaw += YAW_DEG_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera_yaw -= YAW_DEG_PER_SEC * dt


def main() -> None:
    global y_rot

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.SAMPLES, 4)
    glfw.window_hint(glfw.DEPTH_BITS, 24)
    glfw.window_hint(glfw.STENCIL_BITS, 8)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(window_width, window_height,
                                "SphereWorld32", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)
    GL.glEnable(GL.GL_MULTISAMPLE)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_frame = time.monotonic()

    while not glfw.window_should_close(window):
        now = time.monotonic()
        dt = now - last_frame
        last_frame = now

        glfw.poll_events()
        handle_camera_keys(window, dt)
        y_rot = (y_rot + TORUS_DEG_PER_SEC * dt) % 360.0
        render_scene()
        glfw.swap_buffers(window)
    glfw.terminate()


if __name__ == "__main__":
    main()
