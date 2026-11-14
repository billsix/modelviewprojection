# bounce.py
# Animated bouncing rectangle, with an ImGui status overlay.
# OpenGL SuperBible, Chapter 2
# Python port of bounce.cpp by Richard S. Wright Jr.
#
# The C++ original used GLUT for windowing and imgui_impl_glut +
# imgui_impl_opengl2 for the GUI overlay. This port uses GLFW for
# windowing and imgui_bundle (with the GLFW backend) for the overlay,
# matching the rest of the modelviewprojection codebase.

import dataclasses
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

# 33 ms timer in the C++ original
TICK_INTERVAL: float = 33.0 / 1000.0

# Square size (in the orthographic units set up by change_size).
rsize: float = 25.0


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    # set in main(); used by the menubar actions
    window: typing.Any = None  # glfw window handle

    # Initial square position (in the orthographic units set up by
    # change_size).
    x: float = 0.0
    y: float = 0.0

    # Step size (per-tick) in x and y -- 33 ms / tick to match the C++ timer.
    xstep: float = 1.0
    ystep: float = 1.0

    # Bounds of the orthographic clip volume; updated in change_size.
    window_width: float = 100.0
    window_height: float = 100.0

    last_tick: float = 0.0
    paused: bool = False


state: AppState = AppState()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glRectf(state.x, state.y, state.x + rsize, state.y - rsize)


def tick() -> None:
    """Equivalent to TimerFunction in bounce.cpp -- step the rectangle
    one frame and bounce off the clip-volume edges."""
    if state.x > state.window_width - rsize or state.x < -state.window_width:
        state.xstep = -state.xstep
    if state.y > state.window_height or state.y < -state.window_height + rsize:
        state.ystep = -state.ystep

    state.x += state.xstep
    state.y += state.ystep

    # Clip in case the window shrank while bouncing
    if state.x > (state.window_width - rsize + state.xstep):
        state.x = state.window_width - rsize - 1
    elif state.x < -(state.window_width + state.xstep):
        state.x = -state.window_width - 1
    if state.y > (state.window_height + state.ystep):
        state.y = state.window_height - 1
    elif state.y < -(state.window_height - rsize + state.ystep):
        state.y = -state.window_height + rsize - 1


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 1.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1

    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()

    aspect_ratio: float = float(w) / float(h)
    if w <= h:
        state.window_width = 100.0
        state.window_height = state.window_width / aspect_ratio
        GL.glOrtho(
            -100.0, 100.0, -state.window_height, state.window_height, 1.0, -1.0
        )
    else:
        state.window_height = 100.0
        state.window_width = state.window_height * aspect_ratio
        GL.glOrtho(
            -state.window_width, state.window_width, -100.0, 100.0, 1.0, -1.0
        )

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_SPACE and action == glfw.PRESS:
        state.paused = not state.paused


def imgui_menubar() -> None:
    """Top menubar. The Bounce menu carries the step sliders plus the
    Reverse and Pause/Resume actions (SPACE still toggles pause)."""
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
    if imgui.begin_menu("Bounce", True):
        # Sliders live inside the menu (begin_menu/end_menu); they have no
        # menubar-native equivalent so they render as ordinary widgets here.
        xstep_slider: tuple[bool, float] = imgui.slider_float(
            "xstep", state.xstep, -5.0, 5.0
        )
        state.xstep = xstep_slider[1]
        ystep_slider: tuple[bool, float] = imgui.slider_float(
            "ystep", state.ystep, -5.0, 5.0
        )
        state.ystep = ystep_slider[1]
        imgui.separator()

        def _reverse() -> None:
            state.xstep = -state.xstep
            state.ystep = -state.ystep

        def _toggle_pause() -> None:
            state.paused = not state.paused

        _common.menu_action("Reverse", "", _reverse)
        _common.menu_action(
            "Resume" if state.paused else "Pause", "SPACE", _toggle_pause
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    glfw.window_hint(glfw.SAMPLES, 4)  # GLUT_MULTISAMPLE in original

    window: typing.Any = glfw.create_window(  # glfw window handle
        800, 600, "Bounce", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    state.window = window

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl: GlfwRenderer = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so SPACE/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])

    state.last_tick = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        # Step physics on a 33 ms tick
        now: float = time.monotonic()
        if not state.paused and now - state.last_tick >= TICK_INTERVAL:
            tick()
            state.last_tick = now

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
