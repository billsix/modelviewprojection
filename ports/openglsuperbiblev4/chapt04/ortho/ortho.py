# ortho.py
# Demonstrates orthographic projection with a hand-modeled hollow
# rectangular shape, lit by a single light source. Compare with the
# companion perspect.py to see how the same geometry looks under
# perspective projection.
# OpenGL SuperBible, Chapter 4
# Python port of Ortho.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import OpenGL.GL as GL

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


x_rot: float = 0.0
y_rot: float = 0.0


def render_scene() -> None:
    fz = 100.0
    bz = -100.0

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPushMatrix()
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)

    GL.glColor3f(1.0, 0.0, 0.0)

    # ---- Front face (frame) ----
    GL.glBegin(GL.GL_QUADS)
    GL.glNormal3f(0.0, 0.0, 1.0)

    # Left panel
    GL.glVertex3f(-50.0, 50.0, fz)
    GL.glVertex3f(-50.0, -50.0, fz)
    GL.glVertex3f(-35.0, -50.0, fz)
    GL.glVertex3f(-35.0, 50.0, fz)

    # Right panel
    GL.glVertex3f(50.0, 50.0, fz)
    GL.glVertex3f(35.0, 50.0, fz)
    GL.glVertex3f(35.0, -50.0, fz)
    GL.glVertex3f(50.0, -50.0, fz)

    # Top panel
    GL.glVertex3f(-35.0, 50.0, fz)
    GL.glVertex3f(-35.0, 35.0, fz)
    GL.glVertex3f(35.0, 35.0, fz)
    GL.glVertex3f(35.0, 50.0, fz)

    # Bottom panel
    GL.glVertex3f(-35.0, -35.0, fz)
    GL.glVertex3f(-35.0, -50.0, fz)
    GL.glVertex3f(35.0, -50.0, fz)
    GL.glVertex3f(35.0, -35.0, fz)

    # ---- Outer sides ----
    GL.glNormal3f(0.0, 1.0, 0.0)
    GL.glVertex3f(-50.0, 50.0, fz); GL.glVertex3f(50.0, 50.0, fz)
    GL.glVertex3f(50.0, 50.0, bz); GL.glVertex3f(-50.0, 50.0, bz)

    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(-50.0, -50.0, fz); GL.glVertex3f(-50.0, -50.0, bz)
    GL.glVertex3f(50.0, -50.0, bz); GL.glVertex3f(50.0, -50.0, fz)

    GL.glNormal3f(1.0, 0.0, 0.0)
    GL.glVertex3f(50.0, 50.0, fz); GL.glVertex3f(50.0, -50.0, fz)
    GL.glVertex3f(50.0, -50.0, bz); GL.glVertex3f(50.0, 50.0, bz)

    GL.glNormal3f(-1.0, 0.0, 0.0)
    GL.glVertex3f(-50.0, 50.0, fz); GL.glVertex3f(-50.0, 50.0, bz)
    GL.glVertex3f(-50.0, -50.0, bz); GL.glVertex3f(-50.0, -50.0, fz)
    GL.glEnd()

    GL.glFrontFace(GL.GL_CW)

    # ---- Back face (frame) ----
    GL.glBegin(GL.GL_QUADS)
    GL.glNormal3f(0.0, 0.0, -1.0)

    GL.glVertex3f(-50.0, 50.0, bz); GL.glVertex3f(-50.0, -50.0, bz)
    GL.glVertex3f(-35.0, -50.0, bz); GL.glVertex3f(-35.0, 50.0, bz)

    GL.glVertex3f(50.0, 50.0, bz); GL.glVertex3f(35.0, 50.0, bz)
    GL.glVertex3f(35.0, -50.0, bz); GL.glVertex3f(50.0, -50.0, bz)

    GL.glVertex3f(-35.0, 50.0, bz); GL.glVertex3f(-35.0, 35.0, bz)
    GL.glVertex3f(35.0, 35.0, bz); GL.glVertex3f(35.0, 50.0, bz)

    GL.glVertex3f(-35.0, -35.0, bz); GL.glVertex3f(-35.0, -50.0, bz)
    GL.glVertex3f(35.0, -50.0, bz); GL.glVertex3f(35.0, -35.0, bz)

    # ---- Inner walls ----
    GL.glColor3f(0.75, 0.75, 0.75)

    GL.glNormal3f(0.0, 1.0, 0.0)
    GL.glVertex3f(-35.0, 35.0, fz); GL.glVertex3f(35.0, 35.0, fz)
    GL.glVertex3f(35.0, 35.0, bz); GL.glVertex3f(-35.0, 35.0, bz)

    # NB: the C++ source has GL_NORMAL = (0,1,0) below too -- preserved
    # verbatim even though geometrically it should be (0,-1,0).
    GL.glNormal3f(0.0, 1.0, 0.0)
    GL.glVertex3f(-35.0, -35.0, fz); GL.glVertex3f(-35.0, -35.0, bz)
    GL.glVertex3f(35.0, -35.0, bz); GL.glVertex3f(35.0, -35.0, fz)

    GL.glNormal3f(1.0, 0.0, 0.0)
    GL.glVertex3f(-35.0, 35.0, fz); GL.glVertex3f(-35.0, 35.0, bz)
    GL.glVertex3f(-35.0, -35.0, bz); GL.glVertex3f(-35.0, -35.0, fz)

    GL.glNormal3f(-1.0, 0.0, 0.0)
    GL.glVertex3f(35.0, 35.0, fz); GL.glVertex3f(35.0, -35.0, fz)
    GL.glVertex3f(35.0, -35.0, bz); GL.glVertex3f(35.0, 35.0, bz)
    GL.glEnd()

    GL.glFrontFace(GL.GL_CCW)

    GL.glPopMatrix()


def setup_rc() -> None:
    white_light = (0.45, 0.45, 0.45, 1.0)
    source_light = (0.25, 0.25, 0.25, 1.0)
    light_pos = (-50.0, 25.0, 250.0, 0.0)

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
    n_range = 120.0
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

    window = glfw.create_window(
        800, 600, "Orthographic Projection", None, None
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
        handle_special_keys(window)
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
