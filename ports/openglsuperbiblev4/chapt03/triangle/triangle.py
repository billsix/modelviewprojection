# triangle.py
# Demonstrates triangle fans, backface culling, and depth testing.
# The C++ original used a GLUT right-click menu; replaced here with an
# ImGui control panel.
# OpenGL SuperBible, Chapter 3
# Python port of Triangle.cpp by Richard S. Wright Jr.

import dataclasses
import math
import os
import sys
import time
import typing

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

# C++ original used a truncated 3.1415; that, combined with `angle <
# 2*GL_PI` in the fan loop, dropped the closing vertex and left an open
# seam in the cone. Use math.pi and an inclusive vertex count so all
# triangles get drawn.
NUM_SEGMENTS: int = 16


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    # set in main(); used by the Quit control button
    window: typing.Any = None  # glfw window handle

    x_rot: float = 0.0
    y_rot: float = 0.0

    i_cull: bool = False
    i_outline: bool = False
    i_depth: bool = False


state: AppState = AppState()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    if state.i_cull:
        GL.glEnable(GL.GL_CULL_FACE)
    else:
        GL.glDisable(GL.GL_CULL_FACE)

    if state.i_depth:
        GL.glEnable(GL.GL_DEPTH_TEST)
    else:
        GL.glDisable(GL.GL_DEPTH_TEST)

    # C++ original used GL_BACK so back faces would render as lines, but
    # in modern fixed-function pipelines back faces are either culled or
    # depth-discarded by the front, so GL_BACK is a visible no-op.
    # GL_FRONT_AND_BACK makes the toggle actually do something visible.
    if state.i_outline:
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
    else:
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

    GL.glPushMatrix()
    GL.glRotatef(state.x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(state.y_rot, 0.0, 1.0, 0.0)

    # Top of cone as a triangle fan. Loop NUM_SEGMENTS+1 times so the
    # last vertex closes the fan back to the first base vertex.
    pivot: int = 1
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glVertex3f(0.0, 0.0, 75.0)  # apex
    i: int
    for i in range(NUM_SEGMENTS + 1):
        angle: float = 2.0 * math.pi * i / NUM_SEGMENTS
        x: float = 50.0 * math.sin(angle)
        y: float = 50.0 * math.cos(angle)
        if pivot % 2 == 0:
            GL.glColor3f(0.0, 1.0, 0.0)
        else:
            GL.glColor3f(1.0, 0.0, 0.0)
        pivot += 1
        GL.glVertex2f(x, y)
    GL.glEnd()

    # Bottom cap
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glVertex2f(0.0, 0.0)
    for i in range(NUM_SEGMENTS + 1):
        angle = 2.0 * math.pi * i / NUM_SEGMENTS
        x = 50.0 * math.sin(angle)
        y = 50.0 * math.cos(angle)
        if pivot % 2 == 0:
            GL.glColor3f(0.0, 1.0, 0.0)
        else:
            GL.glColor3f(1.0, 0.0, 0.0)
        pivot += 1
        GL.glVertex2f(x, y)
    GL.glEnd()

    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glShadeModel(GL.GL_FLAT)
    # Triangle fans wind clockwise here, so flip the front-face convention
    GL.glFrontFace(GL.GL_CW)


def change_size(w: int, h: int) -> None:
    n_range: float = 100.0
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


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


ROT_DEG_PER_SEC: float = 90.0
# Step applied per held-button frame, mirroring the keyboard rotation
# rate at a nominal 60fps so the buttons feel like holding an arrow key.
ROT_STEP: float = ROT_DEG_PER_SEC / 60.0


def _nudge_rot(axis: str, d: float) -> None:
    if axis == "x":
        state.x_rot += d
    else:
        state.y_rot += d


def handle_special_keys(window: typing.Any, dt: float) -> None:
    step: float = ROT_DEG_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        state.x_rot -= step
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        state.x_rot += step
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        state.y_rot -= step
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        state.y_rot += step


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit",
            "Esc",
            lambda: glfw.set_window_should_close(state.window, True),
        )
        imgui.end_menu()
    _common.draw_view_menu(state.window)
    if imgui.begin_menu("Options", True):
        # menu_item returns (clicked, selected); keep the toggled selection
        depth_item: tuple[bool, bool] = imgui.menu_item(
            "Depth test", "", state.i_depth, True
        )
        state.i_depth = depth_item[1]
        cull_item: tuple[bool, bool] = imgui.menu_item(
            "Cull backface", "", state.i_cull, True
        )
        state.i_cull = cull_item[1]
        outline_item: tuple[bool, bool] = imgui.menu_item(
            "Outline back", "", state.i_outline, True
        )
        state.i_outline = outline_item[1]
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action(
            "Rotate up", "Up", lambda: _nudge_rot("x", -ROT_STEP)
        )
        _common.menu_action(
            "Rotate down", "Down", lambda: _nudge_rot("x", ROT_STEP)
        )
        _common.menu_action(
            "Rotate left", "Left", lambda: _nudge_rot("y", -ROT_STEP)
        )
        _common.menu_action(
            "Rotate right", "Right", lambda: _nudge_rot("y", ROT_STEP)
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window: typing.Any = glfw.create_window(  # glfw window handle
        800, 600, "Triangle Culling Example", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)

    state.window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl: GlfwRenderer = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw
    # key callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])

    glfw.swap_interval(1)
    last_frame: float = time.monotonic()

    while not glfw.window_should_close(window):
        now: float = time.monotonic()
        dt: float = now - last_frame
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
