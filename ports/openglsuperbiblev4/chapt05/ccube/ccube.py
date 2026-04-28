# ccube.py
# RGB color cube -- each vertex is a different color, GL_SMOOTH
# interpolates between them across each face.
# OpenGL SuperBible, Chapter 5
# Python port of ccube.cpp by Richard S. Wright Jr.

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
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)

    GL.glBegin(GL.GL_QUADS)
    # Front
    GL.glColor3ub(255, 255, 255); GL.glVertex3f(50.0, 50.0, 50.0)
    GL.glColor3ub(255, 255, 0);   GL.glVertex3f(50.0, -50.0, 50.0)
    GL.glColor3ub(255, 0, 0);     GL.glVertex3f(-50.0, -50.0, 50.0)
    GL.glColor3ub(255, 0, 255);   GL.glVertex3f(-50.0, 50.0, 50.0)
    # Back
    GL.glColor3f(0.0, 1.0, 1.0);  GL.glVertex3f(50.0, 50.0, -50.0)
    GL.glColor3f(0.0, 1.0, 0.0);  GL.glVertex3f(50.0, -50.0, -50.0)
    GL.glColor3f(0.0, 0.0, 0.0);  GL.glVertex3f(-50.0, -50.0, -50.0)
    GL.glColor3f(0.0, 0.0, 1.0);  GL.glVertex3f(-50.0, 50.0, -50.0)
    # Top
    GL.glColor3f(0.0, 1.0, 1.0);  GL.glVertex3f(50.0, 50.0, -50.0)
    GL.glColor3f(1.0, 1.0, 1.0);  GL.glVertex3f(50.0, 50.0, 50.0)
    GL.glColor3f(1.0, 0.0, 1.0);  GL.glVertex3f(-50.0, 50.0, 50.0)
    GL.glColor3f(0.0, 0.0, 1.0);  GL.glVertex3f(-50.0, 50.0, -50.0)
    # Bottom
    GL.glColor3f(0.0, 1.0, 0.0);  GL.glVertex3f(50.0, -50.0, -50.0)
    GL.glColor3f(1.0, 1.0, 0.0);  GL.glVertex3f(50.0, -50.0, 50.0)
    GL.glColor3f(1.0, 0.0, 0.0);  GL.glVertex3f(-50.0, -50.0, 50.0)
    GL.glColor3f(0.0, 0.0, 0.0);  GL.glVertex3f(-50.0, -50.0, -50.0)
    # Left
    GL.glColor3f(1.0, 1.0, 1.0);  GL.glVertex3f(50.0, 50.0, 50.0)
    GL.glColor3f(0.0, 1.0, 1.0);  GL.glVertex3f(50.0, 50.0, -50.0)
    GL.glColor3f(0.0, 1.0, 0.0);  GL.glVertex3f(50.0, -50.0, -50.0)
    GL.glColor3f(1.0, 1.0, 0.0);  GL.glVertex3f(50.0, -50.0, 50.0)
    # Right
    GL.glColor3f(1.0, 0.0, 1.0);  GL.glVertex3f(-50.0, 50.0, 50.0)
    GL.glColor3f(0.0, 0.0, 1.0);  GL.glVertex3f(-50.0, 50.0, -50.0)
    GL.glColor3f(0.0, 0.0, 0.0);  GL.glVertex3f(-50.0, -50.0, -50.0)
    GL.glColor3f(1.0, 0.0, 0.0);  GL.glVertex3f(-50.0, -50.0, 50.0)
    GL.glEnd()

    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_DITHER)
    GL.glShadeModel(GL.GL_SMOOTH)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    f_aspect = float(w) / float(h)
    GLU.gluPerspective(35.0, f_aspect, 1.0, 1000.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -400.0)


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

    window = glfw.create_window(800, 600, "RGB Cube", None, None)
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
