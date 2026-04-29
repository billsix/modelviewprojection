# snowman.py
# A snowman built from GLU quadric primitives (spheres, cylinder, disk).
# OpenGL SuperBible, Chapter 10
# Python port of Snowman.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


x_rot: float = 0.0
y_rot: float = 0.0


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPushMatrix()
    GL.glTranslatef(0.0, -1.0, -5.0)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)

    obj = GLU.gluNewQuadric()
    GLU.gluQuadricNormals(obj, GLU.GLU_SMOOTH)

    # Body
    GL.glPushMatrix()
    GL.glColor3f(1.0, 1.0, 1.0)
    GLU.gluSphere(obj, 0.40, 26, 13)            # Bottom

    GL.glTranslatef(0.0, 0.55, 0.0)             # Mid
    GLU.gluSphere(obj, 0.30, 26, 13)

    GL.glTranslatef(0.0, 0.45, 0.0)             # Head
    GLU.gluSphere(obj, 0.24, 26, 13)

    # Eyes
    GL.glColor3f(0.0, 0.0, 0.0)
    GL.glTranslatef(0.1, 0.1, 0.21)
    GLU.gluSphere(obj, 0.02, 26, 13)
    GL.glTranslatef(-0.2, 0.0, 0.0)
    GLU.gluSphere(obj, 0.02, 26, 13)

    # Nose
    GL.glColor3f(1.0, 0.3, 0.3)
    GL.glTranslatef(0.1, -0.12, 0.0)
    GLU.gluCylinder(obj, 0.04, 0.0, 0.3, 26, 13)
    GL.glPopMatrix()

    # Hat
    GL.glPushMatrix()
    GL.glColor3f(0.0, 0.0, 0.0)
    GL.glTranslatef(0.0, 1.17, 0.0)
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GLU.gluCylinder(obj, 0.17, 0.17, 0.4, 26, 13)

    # Brim
    GL.glDisable(GL.GL_CULL_FACE)
    GLU.gluDisk(obj, 0.17, 0.28, 26, 13)
    GL.glEnable(GL.GL_CULL_FACE)

    GL.glTranslatef(0.0, 0.0, 0.4)
    GLU.gluDisk(obj, 0.0, 0.17, 26, 13)
    GL.glPopMatrix()

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
    GL.glClearColor(0.25, 0.25, 0.50, 1.0)


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
    window = glfw.create_window(800, 600, "Modeling with Quadrics", None, None)
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
