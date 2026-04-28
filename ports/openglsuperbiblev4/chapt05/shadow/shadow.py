# shadow.py
# Demonstrates planar shadows: the lit jet drops a darkened copy of
# itself onto a green ground plane via a shadow projection matrix.
# Uses mathutils.plane_equation to derive the plane, and an inline
# planar-shadow matrix builder (will move to pyMatrixStack with
# Tier-1 task #3).
# OpenGL SuperBible, Chapter 5
# Python port of Shadow.cpp by Richard S. Wright Jr.

import math
import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui

from modelviewprojection.mathutils import (
    Vector3D,
    find_normal,
    plane_equation,
)

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


x_rot: float = 0.0
y_rot: float = 0.0

ambient_light = (0.3, 0.3, 0.3, 1.0)
diffuse_light = (0.7, 0.7, 0.7, 1.0)
specular = (1.0, 1.0, 1.0, 1.0)
light_pos = (-75.0, 150.0, -50.0, 0.0)
specref = (1.0, 1.0, 1.0, 1.0)

shadow_mat = None  # built in setup_rc -- 4x4 column-major np array


def make_planar_shadow_matrix(plane_normal, plane_d, light_pos_4):
    """4x4 column-major shadow projection matrix. Same formula as
    chapt01/block; will move to pyMatrixStack with Tier-1 task #3."""
    a, b, c = plane_normal.x, plane_normal.y, plane_normal.z
    d = plane_d
    dx = -light_pos_4[0]
    dy = -light_pos_4[1]
    dz = -light_pos_4[2]
    return np.array(
        [
            b * dy + c * dz, -a * dy, -a * dz, 0.0,
            -b * dx, a * dx + c * dz, -b * dz, 0.0,
            -c * dx, -c * dy, a * dx + b * dy, 0.0,
            -d * dx, -d * dy, -d * dz, a * dx + b * dy + c * dz,
        ],
        dtype=np.float32,
    )


def _emit_face(p1, p2, p3) -> None:
    n = find_normal(p1, p2, p3)
    GL.glNormal3f(n.x, n.y, n.z)
    GL.glVertex3f(p1.x, p1.y, p1.z)
    GL.glVertex3f(p2.x, p2.y, p2.z)
    GL.glVertex3f(p3.x, p3.y, p3.z)


def draw_jet(n_shadow: int) -> None:
    if n_shadow == 0:
        GL.glColor3ub(128, 128, 128)
    else:
        GL.glColor3ub(0, 0, 0)

    GL.glBegin(GL.GL_TRIANGLES)

    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(0.0, 0.0, 60.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(15.0, 0.0, 30.0)

    _emit_face(Vector3D(15.0, 0.0, 30.0), Vector3D(0.0, 15.0, 30.0),
               Vector3D(0.0, 0.0, 60.0))
    _emit_face(Vector3D(0.0, 0.0, 60.0), Vector3D(0.0, 15.0, 30.0),
               Vector3D(-15.0, 0.0, 30.0))

    _emit_face(Vector3D(-15.0, 0.0, 30.0), Vector3D(0.0, 15.0, 30.0),
               Vector3D(0.0, 0.0, -56.0))
    _emit_face(Vector3D(0.0, 0.0, -56.0), Vector3D(0.0, 15.0, 30.0),
               Vector3D(15.0, 0.0, 30.0))

    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(15.0, 0.0, 30.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(0.0, 0.0, -56.0)

    _emit_face(Vector3D(0.0, 2.0, 27.0), Vector3D(-60.0, 2.0, -8.0),
               Vector3D(60.0, 2.0, -8.0))
    _emit_face(Vector3D(60.0, 2.0, -8.0), Vector3D(0.0, 7.0, -8.0),
               Vector3D(0.0, 2.0, 27.0))
    _emit_face(Vector3D(60.0, 2.0, -8.0), Vector3D(-60.0, 2.0, -8.0),
               Vector3D(0.0, 7.0, -8.0))
    _emit_face(Vector3D(0.0, 2.0, 27.0), Vector3D(0.0, 7.0, -8.0),
               Vector3D(-60.0, 2.0, -8.0))

    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(-30.0, -0.50, -57.0)
    GL.glVertex3f(30.0, -0.50, -57.0)
    GL.glVertex3f(0.0, -0.50, -40.0)

    _emit_face(Vector3D(0.0, -0.5, -40.0), Vector3D(30.0, -0.5, -57.0),
               Vector3D(0.0, 4.0, -57.0))
    _emit_face(Vector3D(0.0, 4.0, -57.0), Vector3D(-30.0, -0.5, -57.0),
               Vector3D(0.0, -0.5, -40.0))
    _emit_face(Vector3D(30.0, -0.5, -57.0), Vector3D(-30.0, -0.5, -57.0),
               Vector3D(0.0, 4.0, -57.0))

    _emit_face(Vector3D(0.0, 0.5, -40.0), Vector3D(3.0, 0.5, -57.0),
               Vector3D(0.0, 25.0, -65.0))
    _emit_face(Vector3D(0.0, 25.0, -65.0), Vector3D(-3.0, 0.5, -57.0),
               Vector3D(0.0, 0.5, -40.0))
    _emit_face(Vector3D(3.0, 0.5, -57.0), Vector3D(-3.0, 0.5, -57.0),
               Vector3D(0.0, 25.0, -65.0))

    GL.glEnd()


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

    # Ground -- darker green at the back, lighter at the front, gives an
    # illusion of depth on a flat quad
    GL.glBegin(GL.GL_QUADS)
    GL.glColor3ub(0, 32, 0)
    GL.glVertex3f(400.0, -150.0, -200.0)
    GL.glVertex3f(-400.0, -150.0, -200.0)
    GL.glColor3ub(0, 255, 0)
    GL.glVertex3f(-400.0, -150.0, 200.0)
    GL.glVertex3f(400.0, -150.0, 200.0)
    GL.glEnd()

    GL.glPushMatrix()

    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_jet(0)
    GL.glPopMatrix()

    # Shadow pass: same jet, projected onto the ground
    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glPushMatrix()
    GL.glMultMatrixf(shadow_mat)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_jet(1)
    GL.glPopMatrix()

    # Light source visualization (yellow sphere where the light is)
    GL.glPushMatrix()
    GL.glTranslatef(light_pos[0], light_pos[1], light_pos[2])
    GL.glColor3ub(255, 255, 0)
    draw_solid_sphere(5.0, 10, 10)
    GL.glPopMatrix()

    GL.glEnable(GL.GL_DEPTH_TEST)


def setup_rc() -> None:
    global shadow_mat

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)

    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, specular)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, specref)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    GL.glClearColor(0.0, 0.0, 1.0, 1.0)

    # Three points on the ground plane
    p1 = Vector3D(-30.0, -149.0, -20.0)
    p2 = Vector3D(-30.0, -149.0, 20.0)
    p3 = Vector3D(40.0, -149.0, 20.0)
    plane_normal, plane_d = plane_equation(p1, p2, p3)
    shadow_mat = make_planar_shadow_matrix(plane_normal, plane_d, light_pos)

    GL.glEnable(GL.GL_NORMALIZE)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    f_aspect = float(w) / float(h)
    GLU.gluPerspective(60.0, f_aspect, 200.0, 500.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -400.0)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)


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

    
    window_width, window_height = _common.resolve_default_window_size()

    window = glfw.create_window(window_width, window_height, "Shadow", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    impl = _common.init_imgui(window)
    win_state = _common.WindowState()

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        handle_special_keys(window)
        render_scene()
        
        imgui.new_frame()
        _common.draw_menubar(window, win_state)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()

    glfw.terminate()


if __name__ == "__main__":
    main()
