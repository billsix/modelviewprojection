# snowman.py
# A snowman built from GLU quadric primitives (spheres, cylinder, disk).
# OpenGL SuperBible, Chapter 10
# Python port of Snowman.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item


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


def _rot_x(d: float) -> None:
    global x_rot
    x_rot += d


def _rot_y(d: float) -> None:
    global y_rot
    y_rot += d


def imgui_menubar() -> None:
    # All controls in the top menubar. Rotate items run once per click and
    # show their key in the shortcut column; hold the key for continuous spin.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Rotate up", "Up", lambda: _rot_x(-BTN_ROT_STEP))
        _common.menu_action("Rotate down", "Down", lambda: _rot_x(BTN_ROT_STEP))
        _common.menu_action("Rotate left", "Left", lambda: _rot_y(-BTN_ROT_STEP))
        _common.menu_action("Rotate right", "Right",
                            lambda: _rot_y(BTN_ROT_STEP))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "Modeling with Quadrics", None, None)
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
