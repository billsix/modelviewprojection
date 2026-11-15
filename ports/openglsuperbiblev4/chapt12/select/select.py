# select.py
# Click an object to select it; a red rectangle appears around its
# screen-space bounding box.  The textbook used glRenderMode(GL_SELECT)
# for the click and glRenderMode(GL_FEEDBACK) for the bbox; both are
# deprecated and Mesa's compatibility profile crashes on them.
#
# This port does both with color picking: render the scene with each
# pickable object in a unique flat color into the back buffer (no
# swap), glReadPixels at the click position to identify the object,
# then scan the framebuffer for all pixels matching that id and take
# min/max x/y to recover the screen-space bounding box.  Pixel-
# rasterized bbox is within ~1 px of the feedback-projected bbox the
# C++ computed.
#
# OpenGL SuperBible, Chapter 12
# Python port of Select.cpp by Richard S. Wright Jr.

import dataclasses
import math
import os
import sys
import typing

# This file is named select.py, which collides with stdlib's `select`
# module.  When run as `python chapt12/select/select.py`, Python puts
# our directory at sys.path[0], so any later `import select` (e.g.
# stdlib subprocess.py does it) re-enters this file recursively and
# explodes inside imgui_bundle's asyncio chain.  Drop our directory
# from sys.path so stdlib's `select` resolves correctly.
_PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != _PWD]

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

# _PWD is this demo's dir; its parent's parent is the ports root where
# _common lives.  (We dropped _PWD from sys.path above; the ports root
# was never on it, so add it explicitly.)
sys.path.insert(0, os.path.dirname(os.path.dirname(_PWD)))
import _common  # noqa: E402

# Pick ids encoded as the red byte (0 reserved for background).
TORUS: int = 1
SPHERE: int = 2
PICK_PALETTE: dict[int, tuple[float, float, float]] = {
    TORUS: (1.0, 1.0, 0.0),  # yellow
    SPHERE: (1.0, 0.0, 1.0),  # magenta
}


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    # glfw window handle; set in main(), used by the Quit control button
    window: typing.Any = None

    # UI state
    selected_object: int = 0
    bounding_rect: list[int] = dataclasses.field(
        default_factory=lambda: [0, 0, 0, 0]
    )  # top, bottom, left, right
    f_aspect: float = 1.0
    show_pick_buffer: bool = False


state: AppState = AppState()


def draw_torus(num_major: int, num_minor: int) -> None:
    major_radius: float = 0.35
    minor_radius: float = 0.15
    major_step: float = 2.0 * math.pi / num_major
    minor_step: float = 2.0 * math.pi / num_minor
    GL.glEnable(GL.GL_NORMALIZE)
    i: int
    for i in range(num_major):
        a0: float = i * major_step
        a1: float = (i + 1) * major_step
        x0: float = math.cos(a0)
        y0: float = math.sin(a0)
        x1: float = math.cos(a1)
        y1: float = math.sin(a1)
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        j: int
        for j in range(num_minor + 1):
            b: float = j * minor_step
            cb: float = math.cos(b)
            r: float = minor_radius * cb + major_radius
            z: float = minor_radius * math.sin(b)
            GL.glTexCoord2f(float(i) / num_major, float(j) / num_minor)
            GL.glNormal3f(x0 * cb, y0 * cb, z / minor_radius)
            GL.glVertex3f(x0 * r, y0 * r, z)
            GL.glTexCoord2f(float(i + 1) / num_major, float(j) / num_minor)
            GL.glNormal3f(x1 * cb, y1 * cb, z / minor_radius)
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()
    GL.glDisable(GL.GL_NORMALIZE)


def draw_sphere(radius: float) -> None:
    obj: typing.Any = GLU.gluNewQuadric()  # GLU quadric object
    GLU.gluQuadricNormals(obj, GLU.GLU_SMOOTH)
    GLU.gluSphere(obj, radius, 26, 13)
    GLU.gluDeleteQuadric(obj)


def _set_color(
    mode: str, pid: int, normal: "tuple[float, float, float]"
) -> None:
    """mode in {'normal', 'pick_encode', 'pick_debug'}."""
    if mode == "pick_encode":
        GL.glColor3ub(pid, 0, 0)
    elif mode == "pick_debug":
        GL.glColor3f(*PICK_PALETTE[pid])
    else:
        GL.glColor3f(*normal)


def _draw_objects(mode: str) -> None:
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glTranslatef(-0.75, 0.0, -2.5)

    _set_color(mode, TORUS, (1.0, 1.0, 0.0))
    draw_torus(40, 20)

    GL.glTranslatef(1.5, 0.0, 0.0)
    _set_color(mode, SPHERE, (0.5, 0.0, 0.0))
    draw_sphere(0.5)

    GL.glPopMatrix()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    if state.show_pick_buffer:
        GL.glDisable(GL.GL_LIGHTING)
        _draw_objects("pick_debug")
        GL.glEnable(GL.GL_LIGHTING)
    else:
        _draw_objects("normal")

    # Bounding rectangle overlay around the selected object.
    if state.selected_object != 0:
        viewport: np.ndarray = GL.glGetIntegerv(GL.GL_VIEWPORT)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        # Flipped Y so the rect lives in window coords (y=0 at top).
        GL.glOrtho(viewport[0], viewport[2], viewport[3], viewport[1], -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glDisable(GL.GL_LIGHTING)
        GL.glColor3f(1.0, 0.0, 0.0)
        GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex2i(
            state.bounding_rect[2], state.bounding_rect[0]
        )  # left, top
        GL.glVertex2i(
            state.bounding_rect[2], state.bounding_rect[1]
        )  # left, bottom
        GL.glVertex2i(
            state.bounding_rect[3], state.bounding_rect[1]
        )  # right, bottom
        GL.glVertex2i(
            state.bounding_rect[3], state.bounding_rect[0]
        )  # right, top
        GL.glEnd()
        GL.glEnable(GL.GL_LIGHTING)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)


def _compute_bounds(arr: np.ndarray, pid: int) -> "list[int] | None":
    """Find the pixels with R==pid and G==B==0 in the pick-encoded
    framebuffer.  Return [top, bottom, left, right] in window coords
    (y=0 at top), or None if no pixels matched."""
    mask: np.ndarray = (
        (arr[:, :, 0] == pid) & (arr[:, :, 1] == 0) & (arr[:, :, 2] == 0)
    )
    nonzero: tuple[np.ndarray, ...] = np.nonzero(mask)
    if len(nonzero[1]) == 0:
        return None
    h: int = arr.shape[0]
    # arr[0] is the bottom row (glReadPixels GL convention).  Flip y so
    # the bbox is in window coords matching the flipped ortho below.
    y_max_arr: int = int(nonzero[0].max())  # near top of screen
    y_min_arr: int = int(nonzero[0].min())  # near bottom of screen
    top: int = h - 1 - y_max_arr
    bottom: int = h - 1 - y_min_arr
    return [top, bottom, int(nonzero[1].min()), int(nonzero[1].max())]


def process_selection(window: typing.Any, x_pos: float, y_pos: float) -> None:
    win_size: tuple[int, int] = glfw.get_window_size(window)
    fb_size: tuple[int, int] = glfw.get_framebuffer_size(window)
    scale_x: float = fb_size[0] / float(win_size[0]) if win_size[0] else 1.0
    scale_y: float = fb_size[1] / float(win_size[1]) if win_size[1] else 1.0
    fb_x: int = int(x_pos * scale_x)
    fb_y: int = fb_size[1] - int(y_pos * scale_y) - 1

    # Render pick-encoded colors into the back buffer (no swap).
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glDisable(GL.GL_LIGHTING)
    _draw_objects("pick_encode")
    GL.glEnable(GL.GL_LIGHTING)
    GL.glClearColor(0.60, 0.60, 0.60, 1.0)

    # Read back the whole framebuffer so we can both identify the click
    # and (if it hit) recover the object's screen-space bbox.
    GL.glReadBuffer(GL.GL_BACK)
    fb: typing.Any = GL.glReadPixels(  # raw RGB pixel buffer (bytes)
        0, 0, fb_size[0], fb_size[1], GL.GL_RGB, GL.GL_UNSIGNED_BYTE
    )
    arr: np.ndarray = np.frombuffer(fb, dtype=np.uint8).reshape(
        fb_size[1], fb_size[0], 3
    )
    obj_id: int = int(arr[fb_y, fb_x, 0])

    if obj_id == 0:
        return
    # Toggle: clicking the already-selected object deselects it.
    if obj_id == state.selected_object:
        state.selected_object = 0
        return
    bounds: list[int] | None = _compute_bounds(arr, obj_id)
    if bounds is None:
        return
    # Scale framebuffer-space bbox down to window space (HiDPI).
    state.bounding_rect = [
        int(bounds[0] / scale_y),
        int(bounds[1] / scale_y),
        int(bounds[2] / scale_x),
        int(bounds[3] / scale_x),
    ]
    state.selected_object = obj_id


def setup_rc() -> None:
    dim_light: tuple[float, float, float, float] = (0.1, 0.1, 0.1, 1.0)
    source_light: tuple[float, float, float, float] = (0.65, 0.65, 0.65, 1.0)
    light_pos: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, dim_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glClearColor(0.60, 0.60, 0.60, 1.0)
    GL.glLineWidth(2.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    state.f_aspect = float(w) / float(h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(60.0, state.f_aspect, 1.0, 425.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    """All controls live in the top menubar. The single checkbox swaps the
    on-screen render between the lit scene and the pick-color visualization;
    mouse-click selects an object (click again to deselect) in either view.
    No keyboard nav besides Esc, which the File -> Quit item covers."""
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
    if imgui.begin_menu("Selection", True):
        pick_item: tuple[bool, bool] = imgui.menu_item(
            "Show selection buffer", "", state.show_pick_buffer, True
        )
        state.show_pick_buffer = pick_item[1]
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window: typing.Any = glfw.create_window(  # glfw window handle
        800, 600, "Select an Object", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    state.window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    # GlfwRenderer installs its own mouse-button callback.  Polling the
    # button each frame and edge-detecting a press avoids the conflict
    # and lets us check imgui's want_capture_mouse so clicks on the
    # panel don't pick.
    impl: GlfwRenderer = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw
    # key callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])

    prev_click: bool = False

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        click: bool = (
            glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
        )
        if click and not prev_click and not imgui.get_io().want_capture_mouse:
            cursor: tuple[float, float] = glfw.get_cursor_pos(window)
            process_selection(window, cursor[0], cursor[1])
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
