# atom2.py
# Same atom as chapt04/atom, but with perspective projection instead of
# orthographic. Demonstrates how nested transformations look when the
# scene has depth foreshortening.
# OpenGL SuperBible, Chapter 4
# Python port of Atom2.cpp by Richard S. Wright Jr.

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
import _primitives  # noqa: E402
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item

x_rot: float = 0.0
y_rot: float = 0.0
# Orbital angle, advanced from elapsed time each frame so motion stays
# smooth at the render framerate (was a 100 ms timer in the C++).
f_elect1: float = 0.0
ELECTRON_DEG_PER_SEC: float = 100.0
start_time: float = 0.0


# Sphere tessellation is identical every frame: build the bands once at import
# and replay them in render_scene (same GL_QUAD_STRIP-per-band shape the old
# draw_solid_sphere emitted).
NUCLEUS_SPHERE = _primitives.build_sphere(10.0, 15, 15)
ELECTRON_SPHERE = _primitives.build_sphere(6.0, 15, 15)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # Red nucleus
    GL.glColor3ub(255, 0, 0)
    _primitives.draw_mesh(NUCLEUS_SPHERE)

    # Yellow electrons
    GL.glColor3ub(255, 255, 0)

    GL.glPushMatrix()
    GL.glRotatef(f_elect1, 0.0, 1.0, 0.0)
    GL.glTranslatef(90.0, 0.0, 0.0)
    _primitives.draw_mesh(ELECTRON_SPHERE)
    GL.glPopMatrix()

    GL.glPushMatrix()
    GL.glRotatef(45.0, 0.0, 0.0, 1.0)
    GL.glRotatef(f_elect1, 0.0, 1.0, 0.0)
    GL.glTranslatef(-70.0, 0.0, 0.0)
    _primitives.draw_mesh(ELECTRON_SPHERE)
    GL.glPopMatrix()

    GL.glPushMatrix()
    GL.glRotatef(360.0 - 45.0, 0.0, 0.0, 1.0)
    GL.glRotatef(f_elect1, 0.0, 1.0, 0.0)
    GL.glTranslatef(0.0, 0.0, 60.0)
    _primitives.draw_mesh(ELECTRON_SPHERE)
    GL.glPopMatrix()


def update_animation() -> None:
    global f_elect1
    f_elect1 = ((time.monotonic() - start_time) * ELECTRON_DEG_PER_SEC) % 360.0


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    f_aspect = float(w) / float(h)
    GLU.gluPerspective(45.0, f_aspect, 1.0, 500.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -250.0)


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


def _rotate_x(d: float) -> None:
    global x_rot
    x_rot += d


def _rotate_y(d: float) -> None:
    global y_rot
    y_rot += d


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
        _common.menu_action("Rotate up", "Up", lambda: _rotate_x(-BTN_ROT_STEP))
        _common.menu_action("Rotate down", "Down",
                            lambda: _rotate_x(BTN_ROT_STEP))
        _common.menu_action("Rotate left", "Left",
                            lambda: _rotate_y(-BTN_ROT_STEP))
        _common.menu_action("Rotate right", "Right",
                            lambda: _rotate_y(BTN_ROT_STEP))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global start_time, _window

    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(
        800, 600, "OpenGL Atom - Part Duex", None, None
    )
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

    start_time = time.monotonic()
    last_frame = start_time

    while not glfw.window_should_close(window):
        now = time.monotonic()
        dt = now - last_frame
        last_frame = now

        glfw.poll_events()
        impl.process_inputs()
        handle_special_keys(window, dt)
        update_animation()
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
