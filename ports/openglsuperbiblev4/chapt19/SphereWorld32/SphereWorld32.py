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

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


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


def make_planar_shadow_matrix(plane_pts) -> np.ndarray:
    """Cast light at light_pos onto the plane through plane_pts."""
    p1, p2, p3 = plane_pts
    e1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
    e2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])
    n = (e1[1] * e2[2] - e1[2] * e2[1],
         e1[2] * e2[0] - e1[0] * e2[2],
         e1[0] * e2[1] - e1[1] * e2[0])
    nl = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
    a, b, c = n[0] / nl, n[1] / nl, n[2] / nl
    d = -(a * p1[0] + b * p1[1] + c * p1[2])
    lx, ly, lz, lw = light_pos
    dot = a * lx + b * ly + c * lz + d * lw
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = dot - a * lx; m[0, 1] = -a * ly; m[0, 2] = -a * lz; m[0, 3] = -a * lw
    m[1, 0] = -b * lx; m[1, 1] = dot - b * ly; m[1, 2] = -b * lz; m[1, 3] = -b * lw
    m[2, 0] = -c * lx; m[2, 1] = -c * ly; m[2, 2] = dot - c * lz; m[2, 3] = -c * lw
    m[3, 0] = -d * lx; m[3, 1] = -d * ly; m[3, 2] = -d * lz; m[3, 3] = dot - d * lw
    return m.T  # column-major for glMultMatrixf


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
    global y_rot
    if shadow == 0:
        y_rot += 0.5
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


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    global camera_x, camera_z, camera_yaw
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    yaw_rad = math.radians(camera_yaw)
    fwd_x = math.sin(yaw_rad) * 0.1
    fwd_z = -math.cos(yaw_rad) * 0.1
    if key == glfw.KEY_UP:
        camera_x += fwd_x; camera_z += fwd_z
    elif key == glfw.KEY_DOWN:
        camera_x -= fwd_x; camera_z -= fwd_z
    elif key == glfw.KEY_LEFT:
        camera_yaw -= 5.0
    elif key == glfw.KEY_RIGHT:
        camera_yaw += 5.0


def main() -> None:
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
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)
    GL.glEnable(GL.GL_MULTISAMPLE)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)
    while not glfw.window_should_close(window):
        glfw.poll_events()
        render_scene()
        glfw.swap_buffers(window)
    glfw.terminate()


if __name__ == "__main__":
    main()
