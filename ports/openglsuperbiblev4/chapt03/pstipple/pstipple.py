# pstipple.py
# Demonstrates polygon stippling
# OpenGL SuperBible, Chapter 3
# Python port of PStipple.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import numpy as np
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item

x_rot: float = 0.0
y_rot: float = 0.0


# Per-click step for the menubar rotate items (the keyboard, held, rotates
# continuously via handle_special_keys; a menu click does one fixed step).
BTN_ROT_STEP: float = 5.0


def _rot(axis: str, d: float) -> None:
    # Lambdas can't rebind a module global, so mutate here.
    global x_rot, y_rot
    if axis == "x":
        x_rot += d
    else:
        y_rot += d


def imgui_menubar() -> None:
    # All controls in the top menubar. Rotate items run once per click and show
    # their key in the shortcut column; hold the key for continuous rotation.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Rotate up", "Up", lambda: _rot("x", -BTN_ROT_STEP))
        _common.menu_action(
            "Rotate down", "Down", lambda: _rot("x", BTN_ROT_STEP)
        )
        _common.menu_action(
            "Rotate left", "Left", lambda: _rot("y", -BTN_ROT_STEP)
        )
        _common.menu_action(
            "Rotate right", "Right", lambda: _rot("y", BTN_ROT_STEP)
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


# Bitmap of camp fire (32x32 pixels = 128 bytes)
fire = np.array(
    [
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0xC0,
        0x00,
        0x00,
        0x01,
        0xF0,
        0x00,
        0x00,
        0x07,
        0xF0,
        0x0F,
        0x00,
        0x1F,
        0xE0,
        0x1F,
        0x80,
        0x1F,
        0xC0,
        0x0F,
        0xC0,
        0x3F,
        0x80,
        0x07,
        0xE0,
        0x7E,
        0x00,
        0x03,
        0xF0,
        0xFF,
        0x80,
        0x03,
        0xF5,
        0xFF,
        0xE0,
        0x07,
        0xFD,
        0xFF,
        0xF8,
        0x1F,
        0xFC,
        0xFF,
        0xE8,
        0xFF,
        0xE3,
        0xBF,
        0x70,
        0xDE,
        0x80,
        0xB7,
        0x00,
        0x71,
        0x10,
        0x4A,
        0x80,
        0x03,
        0x10,
        0x4E,
        0x40,
        0x02,
        0x88,
        0x8C,
        0x20,
        0x05,
        0x05,
        0x04,
        0x40,
        0x02,
        0x82,
        0x14,
        0x40,
        0x02,
        0x40,
        0x10,
        0x80,
        0x02,
        0x64,
        0x1A,
        0x80,
        0x00,
        0x92,
        0x29,
        0x00,
        0x00,
        0xB0,
        0x48,
        0x00,
        0x00,
        0xC8,
        0x90,
        0x00,
        0x00,
        0x85,
        0x10,
        0x00,
        0x00,
        0x03,
        0x00,
        0x00,
        0x00,
        0x00,
        0x10,
        0x00,
    ],
    dtype=np.uint8,
)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glEnable(GL.GL_POLYGON_STIPPLE)

    GL.glPushMatrix()
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)

    # Stop sign shape, drawn as a single polygon
    GL.glBegin(GL.GL_POLYGON)
    GL.glVertex2f(-20.0, 50.0)
    GL.glVertex2f(20.0, 50.0)
    GL.glVertex2f(50.0, 20.0)
    GL.glVertex2f(50.0, -20.0)
    GL.glVertex2f(20.0, -50.0)
    GL.glVertex2f(-20.0, -50.0)
    GL.glVertex2f(-50.0, -20.0)
    GL.glVertex2f(-50.0, 20.0)
    GL.glEnd()

    GL.glPopMatrix()

    # Disable so the imgui menubar isn't stippled (re-enabled below before
    # the next polygon draw).
    GL.glDisable(GL.GL_POLYGON_STIPPLE)


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glEnable(GL.GL_POLYGON_STIPPLE)
    GL.glPolygonStipple(fire)


def change_size(w: int, h: int) -> None:
    n_range = 100.0
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if w <= h:
        GL.glOrtho(
            -n_range,
            n_range,
            -n_range * h / w,
            n_range * h / w,
            -n_range,
            n_range,
        )
    else:
        GL.glOrtho(
            -n_range * w / h,
            n_range * w / h,
            -n_range,
            n_range,
            -n_range,
            n_range,
        )
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
    global _window

    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "Polygon Stippling", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    glfw.swap_interval(1)
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
