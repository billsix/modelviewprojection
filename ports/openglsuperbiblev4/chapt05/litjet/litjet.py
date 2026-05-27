# litjet.py
# Same hand-modeled jet as chapt05/jet, but each face has a real
# normal computed via find_normal so OpenGL's fixed-function lighting
# can shade it. Uses ambient + diffuse light.
# OpenGL SuperBible, Chapter 5
# Python port of LitJet.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

from modelviewprojection.mathutils import Vector3D, find_normal



x_rot: float = 0.0
y_rot: float = 0.0


def _emit_face(p1: Vector3D, p2: Vector3D, p3: Vector3D) -> None:
    """Compute the face normal via mathutils.find_normal (CCW
    convention -- same direction as math3d.cpp's m3dFindNormal),
    issue glNormal3f, then issue the three glVertex3f calls."""
    n = find_normal(p1, p2, p3)
    GL.glNormal3f(n.x, n.y, n.z)
    GL.glVertex3f(p1.x, p1.y, p1.z)
    GL.glVertex3f(p2.x, p2.y, p2.z)
    GL.glVertex3f(p3.x, p3.y, p3.z)


def draw_jet() -> None:
    GL.glBegin(GL.GL_TRIANGLES)

    # --- Nose cone ---
    GL.glColor3ub(128, 128, 128)
    # Bottom of nose -- explicit normal in the source
    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(0.0, 0.0, 60.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(15.0, 0.0, 30.0)

    _emit_face(
        Vector3D(15.0, 0.0, 30.0),
        Vector3D(0.0, 15.0, 30.0),
        Vector3D(0.0, 0.0, 60.0),
    )
    _emit_face(
        Vector3D(0.0, 0.0, 60.0),
        Vector3D(0.0, 15.0, 30.0),
        Vector3D(-15.0, 0.0, 30.0),
    )

    # --- Body ---
    _emit_face(
        Vector3D(-15.0, 0.0, 30.0),
        Vector3D(0.0, 15.0, 30.0),
        Vector3D(0.0, 0.0, -56.0),
    )
    _emit_face(
        Vector3D(0.0, 0.0, -56.0),
        Vector3D(0.0, 15.0, 30.0),
        Vector3D(15.0, 0.0, 30.0),
    )

    # Bottom of body
    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(15.0, 0.0, 30.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(0.0, 0.0, -56.0)

    # --- Wing (top) ---
    _emit_face(
        Vector3D(0.0, 2.0, 27.0),
        Vector3D(-60.0, 2.0, -8.0),
        Vector3D(60.0, 2.0, -8.0),
    )
    _emit_face(
        Vector3D(60.0, 2.0, -8.0),
        Vector3D(0.0, 7.0, -8.0),
        Vector3D(0.0, 2.0, 27.0),
    )
    _emit_face(
        Vector3D(60.0, 2.0, -8.0),
        Vector3D(-60.0, 2.0, -8.0),
        Vector3D(0.0, 7.0, -8.0),
    )
    _emit_face(
        Vector3D(0.0, 2.0, 27.0),
        Vector3D(0.0, 7.0, -8.0),
        Vector3D(-60.0, 2.0, -8.0),
    )

    # --- Tail ---
    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(-30.0, -0.50, -57.0)
    GL.glVertex3f(30.0, -0.50, -57.0)
    GL.glVertex3f(0.0, -0.50, -40.0)

    _emit_face(
        Vector3D(0.0, -0.5, -40.0),
        Vector3D(30.0, -0.5, -57.0),
        Vector3D(0.0, 4.0, -57.0),
    )
    _emit_face(
        Vector3D(0.0, 4.0, -57.0),
        Vector3D(-30.0, -0.5, -57.0),
        Vector3D(0.0, -0.5, -40.0),
    )
    _emit_face(
        Vector3D(30.0, -0.5, -57.0),
        Vector3D(-30.0, -0.5, -57.0),
        Vector3D(0.0, 4.0, -57.0),
    )

    # Vertical fin
    _emit_face(
        Vector3D(0.0, 0.5, -40.0),
        Vector3D(3.0, 0.5, -57.0),
        Vector3D(0.0, 25.0, -65.0),
    )
    _emit_face(
        Vector3D(0.0, 25.0, -65.0),
        Vector3D(-3.0, 0.5, -57.0),
        Vector3D(0.0, 0.5, -40.0),
    )
    _emit_face(
        Vector3D(3.0, 0.5, -57.0),
        Vector3D(-3.0, 0.5, -57.0),
        Vector3D(0.0, 25.0, -65.0),
    )

    GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    GL.glColor3ub(128, 128, 128)
    draw_jet()
    GL.glPopMatrix()


def setup_rc() -> None:
    ambient_light = (0.3, 0.3, 0.3, 1.0)
    diffuse_light = (0.7, 0.7, 0.7, 1.0)

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)

    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)

    GL.glClearColor(0.0, 0.0, 1.0, 1.0)
    GL.glEnable(GL.GL_NORMALIZE)


def change_size(w: int, h: int) -> None:
    light_pos = (-50.0, 50.0, 100.0, 1.0)
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    f_aspect = float(w) / float(h)
    GLU.gluPerspective(45.0, f_aspect, 1.0, 225.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glTranslatef(0.0, 0.0, -150.0)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


# Rotation rate while an arrow key is held. Multiplied by frame delta
# so the rotation speed is independent of the render framerate.
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

    window = glfw.create_window(800, 600, "Lighted Jet", None, None)
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
