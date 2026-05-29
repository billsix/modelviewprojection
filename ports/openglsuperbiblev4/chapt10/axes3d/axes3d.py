# axes3d.py
# 3D unit axis model -- a useful visualization aid showing the X, Y, Z
# axes as colored arrows. Reimplemented inline; the original called
# gltDrawUnitAxes from gltools.
# OpenGL SuperBible, Chapter 10
# Python port of Axes3D.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _primitives  # noqa: E402



x_rot: float = 0.0
y_rot: float = 0.0

# Axis-arrow dimensions (rod + cone arrowhead). The originals regenerated
# all of this trig every frame for three axes; precompute each piece once.
ROD_RADIUS = 0.025
CONE_RADIUS = 0.06
ROD_LENGTH = 0.85
CONE_LENGTH = 0.15
AXIS_SLICES = 20


def _build_cylinder_rings(base_radius: float, top_radius: float, height: float,
                          slices: int) -> list:
    """Precompute the cylinder side surface's per-segment rings. The original
    gluCylinder replacement emits ONE normal shared by each segment's base+top
    vertex pair, which neither draw_mesh mode expresses, so _draw_cylinder
    replays these directly. The trig still runs only once, here."""
    rings = []
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        c, s = math.cos(a), math.sin(a)
        rings.append((c, s,
                      (c * base_radius, s * base_radius, 0.0),
                      (c * top_radius, s * top_radius, height)))
    return rings


def _draw_cylinder() -> None:
    GL.glBegin(GL.GL_QUAD_STRIP)
    for c, s, base_v, top_v in CYLINDER_RINGS:
        GL.glNormal3f(c, s, 0.0)
        GL.glVertex3f(*base_v)
        GL.glVertex3f(*top_v)
    GL.glEnd()


def _build_cone_disk(radius: float, slices: int) -> "_primitives.Mesh":
    """The cone's base cap: a -Z-facing GL_TRIANGLE_FAN wound in reverse, one
    flat normal for the whole fan (replay with draw_mesh(flat=True))."""
    band: list = [(0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0)]
    for i in range(slices, -1, -1):
        a = 2.0 * math.pi * float(i) / slices
        band.append((0.0, 0.0, -1.0, 0.0, 0.0,
                     math.cos(a) * radius, math.sin(a) * radius, 0.0))
    return (GL.GL_TRIANGLE_FAN, [band])


CYLINDER_RINGS = _build_cylinder_rings(ROD_RADIUS, ROD_RADIUS, ROD_LENGTH,
                                       AXIS_SLICES)
CONE_BODY = _primitives.build_cone(CONE_RADIUS, CONE_LENGTH, AXIS_SLICES)
CONE_DISK = _build_cone_disk(CONE_RADIUS, AXIS_SLICES)
ORIGIN_SPHERE = _primitives.build_sphere(0.05, 15, 15, swap_winding=True)


def draw_unit_axes() -> None:
    """Draw three colored axes with cones at their tips. The original
    gltDrawUnitAxes drew red X, green Y, blue Z axes from origin to 1.0,
    each with a small cone arrowhead."""
    # +X axis -- red, rotated about Y so cylinder runs along +X
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(90.0, 0.0, 1.0, 0.0)
    _draw_axis_arrow()
    GL.glPopMatrix()

    # +Y axis -- green, rotated about X so cylinder runs along +Y
    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    _draw_axis_arrow()
    GL.glPopMatrix()

    # +Z axis -- blue, default orientation
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glPushMatrix()
    _draw_axis_arrow()
    GL.glPopMatrix()

    # White sphere at the origin -- the original gltDrawUnitAxes finished
    # with gluSphere(0.05, 15, 15).
    GL.glColor3f(1.0, 1.0, 1.0)
    _primitives.draw_mesh(ORIGIN_SPHERE)


def _draw_axis_arrow() -> None:
    """Rod + cone arrowhead (body then base disk), all precomputed."""
    _draw_cylinder()
    GL.glTranslatef(0.0, 0.0, ROD_LENGTH)
    _primitives.draw_mesh(CONE_BODY, flat=True)
    _primitives.draw_mesh(CONE_DISK, flat=True)


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
    window = glfw.create_window(800, 600, "Unit Axis", None, None)
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
