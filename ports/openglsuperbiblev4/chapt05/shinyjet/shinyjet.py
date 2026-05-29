# shinyjet.py
# Same lit jet as chapt05/litjet, but with specular reflection enabled.
# The added GL_SPECULAR / GL_SHININESS material settings give the jet
# a glossy white highlight.
# OpenGL SuperBible, Chapter 5
# Python port of Shinyjet.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from modelviewprojection.mathutils import Vector3D, find_normal

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item


x_rot: float = 0.0
y_rot: float = 0.0


def _emit_face(p1: Vector3D, p2: Vector3D, p3: Vector3D) -> None:
    n = find_normal(p1, p2, p3)
    GL.glNormal3f(n.x, n.y, n.z)
    GL.glVertex3f(p1.x, p1.y, p1.z)
    GL.glVertex3f(p2.x, p2.y, p2.z)
    GL.glVertex3f(p3.x, p3.y, p3.z)


def draw_jet() -> None:
    GL.glBegin(GL.GL_TRIANGLES)

    GL.glColor3ub(128, 128, 128)
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
    specular = (1.0, 1.0, 1.0, 1.0)
    specref = (1.0, 1.0, 1.0, 1.0)

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)

    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, specular)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, specref)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

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


# Per-click step for the menubar rotate items (the keyboard, held, rotates
# continuously via handle_special_keys; a menu click does one fixed step).
BTN_ROT_STEP: float = 5.0


def _rotate(dx: float, dy: float) -> None:
    global x_rot, y_rot
    x_rot += dx
    y_rot += dy


def imgui_menubar() -> None:
    # All controls in the top menubar. Rotate items run once per click and show
    # their key in the shortcut column; hold the key for continuous rotation.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Rotate up", "Up", lambda: _rotate(-BTN_ROT_STEP, 0))
        _common.menu_action("Rotate down", "Down",
                            lambda: _rotate(BTN_ROT_STEP, 0))
        _common.menu_action("Rotate left", "Left",
                            lambda: _rotate(0, -BTN_ROT_STEP))
        _common.menu_action("Rotate right", "Right",
                            lambda: _rotate(0, BTN_ROT_STEP))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "Shiny Jet", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_frame = time.monotonic()

    while not glfw.window_should_close(window):
        now = time.monotonic()
        dt = now - last_frame
        last_frame = now

        glfw.poll_events()
        impl.process_inputs()
        handle_special_keys(window, dt)
        render_scene()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
