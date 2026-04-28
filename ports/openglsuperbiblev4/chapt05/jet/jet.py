# jet.py
# A hand-modeled jet airplane, drawn flat-shaded with no lighting yet --
# the starting point for chapt05's progression: jet -> ambient -> litjet
# -> shinyjet -> spot.
# OpenGL SuperBible, Chapter 5
# Python port of Jet.cpp by Richard S. Wright Jr.

import os
import sys

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


x_rot: float = 0.0
y_rot: float = 0.0


def draw_jet() -> None:
    """The hand-modeled jet -- 16 triangles, per-triangle colors,
    no normals (lighting is off in this demo)."""
    GL.glBegin(GL.GL_TRIANGLES)

    # --- Nose cone ---
    GL.glColor3ub(255, 255, 255)
    GL.glVertex3f(0.0, 0.0, 60.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(15.0, 0.0, 30.0)

    GL.glColor3ub(0, 0, 0)
    GL.glVertex3f(15.0, 0.0, 30.0)
    GL.glVertex3f(0.0, 15.0, 30.0)
    GL.glVertex3f(0.0, 0.0, 60.0)

    GL.glColor3ub(255, 0, 0)
    GL.glVertex3f(0.0, 0.0, 60.0)
    GL.glVertex3f(0.0, 15.0, 30.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)

    # --- Body ---
    GL.glColor3ub(0, 255, 0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(0.0, 15.0, 30.0)
    GL.glVertex3f(0.0, 0.0, -56.0)

    GL.glColor3ub(255, 255, 0)
    GL.glVertex3f(0.0, 0.0, -56.0)
    GL.glVertex3f(0.0, 15.0, 30.0)
    GL.glVertex3f(15.0, 0.0, 30.0)

    GL.glColor3ub(0, 255, 255)
    GL.glVertex3f(15.0, 0.0, 30.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(0.0, 0.0, -56.0)

    # --- Wing ---
    GL.glColor3ub(128, 128, 128)
    GL.glVertex3f(0.0, 2.0, 27.0)
    GL.glVertex3f(-60.0, 2.0, -8.0)
    GL.glVertex3f(60.0, 2.0, -8.0)

    GL.glColor3ub(64, 64, 64)
    GL.glVertex3f(60.0, 2.0, -8.0)
    GL.glVertex3f(0.0, 7.0, -8.0)
    GL.glVertex3f(0.0, 2.0, 27.0)

    GL.glColor3ub(192, 192, 192)
    GL.glVertex3f(60.0, 2.0, -8.0)
    GL.glVertex3f(-60.0, 2.0, -8.0)
    GL.glVertex3f(0.0, 7.0, -8.0)

    GL.glColor3ub(64, 64, 64)
    GL.glVertex3f(0.0, 2.0, 27.0)
    GL.glVertex3f(0.0, 7.0, -8.0)
    GL.glVertex3f(-60.0, 2.0, -8.0)

    # --- Tail ---
    GL.glColor3ub(255, 128, 255)
    GL.glVertex3f(-30.0, -0.50, -57.0)
    GL.glVertex3f(30.0, -0.50, -57.0)
    GL.glVertex3f(0.0, -0.50, -40.0)

    GL.glColor3ub(255, 128, 0)
    GL.glVertex3f(0.0, -0.5, -40.0)
    GL.glVertex3f(30.0, -0.5, -57.0)
    GL.glVertex3f(0.0, 4.0, -57.0)

    GL.glColor3ub(255, 128, 0)
    GL.glVertex3f(0.0, 4.0, -57.0)
    GL.glVertex3f(-30.0, -0.5, -57.0)
    GL.glVertex3f(0.0, -0.5, -40.0)

    GL.glColor3ub(255, 255, 255)
    GL.glVertex3f(30.0, -0.5, -57.0)
    GL.glVertex3f(-30.0, -0.5, -57.0)
    GL.glVertex3f(0.0, 4.0, -57.0)

    # Vertical fin
    GL.glColor3ub(255, 0, 0)
    GL.glVertex3f(0.0, 0.5, -40.0)
    GL.glVertex3f(3.0, 0.5, -57.0)
    GL.glVertex3f(0.0, 25.0, -65.0)

    GL.glColor3ub(255, 0, 0)
    GL.glVertex3f(0.0, 25.0, -65.0)
    GL.glVertex3f(-3.0, 0.5, -57.0)
    GL.glVertex3f(0.0, 0.5, -40.0)

    GL.glColor3ub(128, 128, 128)
    GL.glVertex3f(3.0, 0.5, -57.0)
    GL.glVertex3f(-3.0, 0.5, -57.0)
    GL.glVertex3f(0.0, 25.0, -65.0)

    GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_jet()
    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glFrontFace(GL.GL_CCW)
    GL.glClearColor(0.0, 0.0, 0.5, 1.0)


def change_size(w: int, h: int) -> None:
    n_range = 80.0
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if w <= h:
        GL.glOrtho(-n_range, n_range, -n_range * h / w, n_range * h / w,
                   -n_range, n_range)
    else:
        GL.glOrtho(-n_range * w / h, n_range * w / h, -n_range, n_range,
                   -n_range, n_range)
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

    
    window_width, window_height = _common.resolve_default_window_size()

    window = glfw.create_window(window_width, window_height, "Jet", None, None)
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

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        handle_special_keys(window)
        render_scene()
        
        imgui.new_frame()
        _common.draw_menubar(window, win_state)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()

    glfw.terminate()


if __name__ == "__main__":
    main()
