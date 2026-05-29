# moons.py
# Hierarchical selection -- click on a body to identify which planet or
# moon it is.  The textbook used glRenderMode(GL_SELECT) + a name stack;
# that pipeline is deprecated in modern OpenGL and Mesa's compatibility
# profile crashes on it (gluSphere inside SELECT mode is a known
# segfault).  This port uses color picking instead: redraw the scene
# into the back buffer with each pickable body painted in a unique flat
# color, glReadPixels at the click position, decode the color to an
# object id.  Same teaching point (hierarchy via parent/child ids),
# survives Mesa.
#
# OpenGL SuperBible, Chapter 12
# Python port of Moons.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer



PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit control button

# Pick ids encoded as the red byte (0..255).  0 reserved for background.
PICK_BG = 0
PICK_EARTH = 1
PICK_EARTH_MOON = 2
PICK_MARS = 3
PICK_MARS_MOON1 = 4
PICK_MARS_MOON2 = 5

# Bright distinct colors used when the user enables the "Show selection
# buffer" checkbox -- the actual encoded pick ids (1..5 in the red byte)
# are too dim to see by eye.  Same scene topology, just visually
# distinguishable.
PICK_PALETTE = {
    PICK_EARTH:      (1.0, 0.0, 0.0),  # red
    PICK_EARTH_MOON: (1.0, 0.6, 0.0),  # orange
    PICK_MARS:       (1.0, 1.0, 0.0),  # yellow
    PICK_MARS_MOON1: (0.0, 1.0, 1.0),  # cyan
    PICK_MARS_MOON2: (1.0, 0.0, 1.0),  # magenta
}

# UI state -- toggled by imgui checkbox in the main loop.
show_pick_buffer: bool = False


def draw_sphere(radius: float) -> None:
    obj = GLU.gluNewQuadric()
    GLU.gluQuadricNormals(obj, GLU.GLU_SMOOTH)
    GLU.gluSphere(obj, radius, 26, 13)
    GLU.gluDeleteQuadric(obj)


def _set_color(mode: str, pid: int, normal: "tuple[float, float, float]") -> None:
    """Bind the right color for this body based on render mode:
    'normal'      = physical color, lit
    'pick_encode' = (pid, 0, 0) raw bytes -- read back by glReadPixels
    'pick_debug'  = bright distinct palette for on-screen debug view"""
    if mode == "pick_encode":
        GL.glColor3ub(pid, 0, 0)
    elif mode == "pick_debug":
        GL.glColor3f(*PICK_PALETTE[pid])
    else:
        GL.glColor3f(*normal)


def _draw_scene(mode: str) -> None:
    """Lay out Earth + its moon, Mars + its two moons."""
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -300.0)

    # Earth
    GL.glPushMatrix()
    _set_color(mode, PICK_EARTH, (0.0, 0.0, 1.0))
    GL.glTranslatef(-100.0, 0.0, 0.0)
    draw_sphere(30.0)

    GL.glTranslatef(45.0, 0.0, 0.0)
    _set_color(mode, PICK_EARTH_MOON, (0.85, 0.85, 0.85))
    draw_sphere(5.0)
    GL.glPopMatrix()

    # Mars
    GL.glPushMatrix()
    _set_color(mode, PICK_MARS, (1.0, 0.0, 0.0))
    GL.glTranslatef(100.0, 0.0, 0.0)
    draw_sphere(20.0)

    GL.glTranslatef(-40.0, 40.0, 0.0)
    _set_color(mode, PICK_MARS_MOON1, (0.85, 0.85, 0.85))
    draw_sphere(5.0)

    GL.glTranslatef(0.0, -80.0, 0.0)
    _set_color(mode, PICK_MARS_MOON2, (0.85, 0.85, 0.85))
    draw_sphere(5.0)
    GL.glPopMatrix()

    GL.glPopMatrix()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    if show_pick_buffer:
        # Visualize what process_selection sees, with bright palette.
        GL.glDisable(GL.GL_LIGHTING)
        _draw_scene("pick_debug")
        GL.glEnable(GL.GL_LIGHTING)
    else:
        _draw_scene("normal")


_PICK_MSG = {
    PICK_EARTH: "You clicked Earth.",
    PICK_EARTH_MOON: "You clicked Earth. - Specifically the moon.",
    PICK_MARS: "You clicked Mars.",
    PICK_MARS_MOON1: "You clicked Mars. - Specifically Moon #1.",
    PICK_MARS_MOON2: "You clicked Mars. - Specifically Moon #2.",
}


def process_selection(window, x_pos: float, y_pos: float) -> None:
    # GLFW cursor coords are in window pixels; framebuffer may be larger
    # on HiDPI displays.  Scale into framebuffer pixels for glReadPixels.
    win_w, win_h = glfw.get_window_size(window)
    fb_w, fb_h = glfw.get_framebuffer_size(window)
    scale_x = fb_w / float(win_w) if win_w else 1.0
    scale_y = fb_h / float(win_h) if win_h else 1.0
    fb_x = int(x_pos * scale_x)
    # GLFW y is from top, GL y is from bottom.
    fb_y = fb_h - int(y_pos * scale_y) - 1

    # Repaint the back buffer with picking colors.  Background is solid
    # black so the R byte == 0 means "missed".  We don't swap, so the
    # user never sees this frame.
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glDisable(GL.GL_LIGHTING)
    _draw_scene("pick_encode")
    GL.glEnable(GL.GL_LIGHTING)
    GL.glClearColor(0.60, 0.60, 0.60, 1.0)

    GL.glReadBuffer(GL.GL_BACK)
    pixel = GL.glReadPixels(fb_x, fb_y, 1, 1, GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
    arr = np.frombuffer(pixel, dtype=np.uint8)
    obj_id = int(arr[0])  # R channel = pick id
    glfw.set_window_title(
        window, _PICK_MSG.get(obj_id, "Nothing was clicked on!")
    )


def setup_rc() -> None:
    dim_light = (0.1, 0.1, 0.1, 1.0)
    source_light = (0.65, 0.65, 0.65, 1.0)
    light_pos = (0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, dim_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glClearColor(0.60, 0.60, 0.60, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, float(w) / float(h), 1.0, 425.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    """All controls live in the top menubar. The single checkbox swaps the
    on-screen render between the normal lit scene and the pick-color
    visualization; mouse-click picking works in either view. No keyboard nav
    besides Esc, which the File -> Quit item covers."""
    global show_pick_buffer
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Picking", True):
        _, show_pick_buffer = imgui.menu_item(
            "Show selection buffer", "", show_pick_buffer, True)
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "Pick a Planet (Hierarchical)",
                                None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    # GlfwRenderer installs its own mouse-button callback for imgui --
    # GLFW only stores one callback per event, so a plain
    # glfw.set_mouse_button_callback here would get overwritten and our
    # picking handler would never fire.  Instead we poll the left
    # button each frame and edge-detect a press, gated on whether
    # imgui wants the mouse (so clicks on the imgui panel don't pick).
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw
    # key callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    prev_click = False

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        click = (
            glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT)
            == glfw.PRESS
        )
        if (click and not prev_click
                and not imgui.get_io().want_capture_mouse):
            x_pos, y_pos = glfw.get_cursor_pos(window)
            process_selection(window, x_pos, y_pos)
        prev_click = click

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
