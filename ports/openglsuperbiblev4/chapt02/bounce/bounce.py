# bounce.py
# Animated bouncing rectangle, with an ImGui status overlay.
# OpenGL SuperBible, Chapter 2
# Python port of bounce.cpp by Richard S. Wright Jr.
#
# The C++ original used GLUT for windowing and imgui_impl_glut +
# imgui_impl_opengl2 for the GUI overlay. This port uses GLFW for
# windowing and imgui_bundle (with the GLFW backend) for the overlay,
# matching the rest of the modelviewprojection codebase.

import os
import sys
import time

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


# Initial square position and size (in the orthographic units set up by
# change_size).
x: float = 0.0
y: float = 0.0
rsize: float = 25.0

# Step size (per-tick) in x and y -- 33 ms / tick to match the C++ timer.
xstep: float = 1.0
ystep: float = 1.0

# Bounds of the orthographic clip volume; updated in change_size.
window_width: float = 100.0
window_height: float = 100.0

# 33 ms timer in the C++ original
TICK_INTERVAL: float = 33.0 / 1000.0
last_tick: float = 0.0
paused: bool = False


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glRectf(x, y, x + rsize, y - rsize)


def tick() -> None:
    """Equivalent to TimerFunction in bounce.cpp -- step the rectangle
    one frame and bounce off the clip-volume edges."""
    global x, y, xstep, ystep

    if x > window_width - rsize or x < -window_width:
        xstep = -xstep
    if y > window_height or y < -window_height + rsize:
        ystep = -ystep

    x += xstep
    y += ystep

    # Clip in case the window shrank while bouncing
    if x > (window_width - rsize + xstep):
        x = window_width - rsize - 1
    elif x < -(window_width + xstep):
        x = -window_width - 1
    if y > (window_height + ystep):
        y = window_height - 1
    elif y < -(window_height - rsize + ystep):
        y = -window_height + rsize - 1


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 1.0, 1.0)


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    if h == 0:
        h = 1

    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()

    aspect_ratio = float(w) / float(h)
    if w <= h:
        window_width = 100.0
        window_height = window_width / aspect_ratio
        GL.glOrtho(-100.0, 100.0, -window_height, window_height, 1.0, -1.0)
    else:
        window_height = 100.0
        window_width = window_height * aspect_ratio
        GL.glOrtho(-window_width, window_width, -100.0, 100.0, 1.0, -1.0)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    global paused
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_SPACE and action == glfw.PRESS:
        paused = not paused


def imgui_panel() -> None:
    """Status overlay -- the C++ version used the ImGui demo window;
    here we just show a small panel matching the spirit of the original
    (a few values, a few controls)."""
    global xstep, ystep, paused
    imgui.begin("Bounce")
    imgui.text(f"x = {x:.1f}, y = {y:.1f}")
    imgui.text(f"xstep = {xstep:.2f}, ystep = {ystep:.2f}")
    imgui.text(f"window {window_width:.0f} x {window_height:.0f}")
    changed_x, xstep = imgui.slider_float("xstep", xstep, -5.0, 5.0)  # noqa: F841
    changed_y, ystep = imgui.slider_float("ystep", ystep, -5.0, 5.0)  # noqa: F841
    if imgui.button("Reverse"):
        xstep = -xstep
        ystep = -ystep
    imgui.same_line()
    if imgui.button("Pause" if not paused else "Resume"):
        paused = not paused
    imgui.text(
        f"Application avg {1000.0 / max(imgui.get_io().framerate, 1.0):.3f} "
        f"ms/frame ({imgui.get_io().framerate:.1f} FPS)"
    )
    imgui.end()


def main() -> None:
    global last_tick

    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    glfw.window_hint(glfw.SAMPLES, 4)  # GLUT_MULTISAMPLE in original

    
    window_width, window_height = _common.resolve_default_window_size()

    window = glfw.create_window(window_width, window_height, "Bounce", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    impl = _common.init_imgui(window)
    win_state = _common.WindowState()

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_tick = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        # Step physics on a 33 ms tick
        now = time.monotonic()
        if not paused and now - last_tick >= TICK_INTERVAL:
            tick()
            last_tick = now

        render_scene()

        imgui.new_frame()

        _common.draw_menubar(window, win_state)
        imgui_panel()
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
