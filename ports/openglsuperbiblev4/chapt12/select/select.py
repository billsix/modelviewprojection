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

import math
import os
import sys
from typing import List

# This file is named select.py, which collides with stdlib's `select`
# module.  When run as `python chapt12/select/select.py`, Python puts
# our directory at sys.path[0], so any later `import select` (e.g.
# stdlib subprocess.py does it) re-enters this file recursively and
# explodes inside imgui_bundle's asyncio chain.  Drop our directory
# from sys.path so stdlib's `select` resolves correctly.
_PWD = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != _PWD]

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer



# Pick ids encoded as the red byte (0 reserved for background).
TORUS, SPHERE = 1, 2
PICK_PALETTE = {
    TORUS:  (1.0, 1.0, 0.0),   # yellow
    SPHERE: (1.0, 0.0, 1.0),   # magenta
}

# UI state
selected_object: int = 0
bounding_rect: List[int] = [0, 0, 0, 0]  # top, bottom, left, right
f_aspect: float = 1.0
show_pick_buffer: bool = False


def draw_torus(num_major: int, num_minor: int) -> None:
    major_radius = 0.35
    minor_radius = 0.15
    major_step = 2.0 * math.pi / num_major
    minor_step = 2.0 * math.pi / num_minor
    GL.glEnable(GL.GL_NORMALIZE)
    for i in range(num_major):
        a0, a1 = i * major_step, (i + 1) * major_step
        x0, y0 = math.cos(a0), math.sin(a0)
        x1, y1 = math.cos(a1), math.sin(a1)
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        for j in range(num_minor + 1):
            b = j * minor_step
            cb = math.cos(b)
            r = minor_radius * cb + major_radius
            z = minor_radius * math.sin(b)
            GL.glTexCoord2f(float(i) / num_major, float(j) / num_minor)
            GL.glNormal3f(x0 * cb, y0 * cb, z / minor_radius)
            GL.glVertex3f(x0 * r, y0 * r, z)
            GL.glTexCoord2f(float(i + 1) / num_major,
                            float(j) / num_minor)
            GL.glNormal3f(x1 * cb, y1 * cb, z / minor_radius)
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()
    GL.glDisable(GL.GL_NORMALIZE)


def draw_sphere(radius: float) -> None:
    obj = GLU.gluNewQuadric()
    GLU.gluQuadricNormals(obj, GLU.GLU_SMOOTH)
    GLU.gluSphere(obj, radius, 26, 13)
    GLU.gluDeleteQuadric(obj)


def _set_color(mode: str, pid: int, normal: "tuple[float, float, float]") -> None:
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
    if show_pick_buffer:
        GL.glDisable(GL.GL_LIGHTING)
        _draw_objects("pick_debug")
        GL.glEnable(GL.GL_LIGHTING)
    else:
        _draw_objects("normal")

    # Bounding rectangle overlay around the selected object.
    if selected_object != 0:
        viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        # Flipped Y so the rect lives in window coords (y=0 at top).
        GL.glOrtho(viewport[0], viewport[2], viewport[3], viewport[1],
                   -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glDisable(GL.GL_LIGHTING)
        GL.glColor3f(1.0, 0.0, 0.0)
        GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex2i(bounding_rect[2], bounding_rect[0])  # left, top
        GL.glVertex2i(bounding_rect[2], bounding_rect[1])  # left, bottom
        GL.glVertex2i(bounding_rect[3], bounding_rect[1])  # right, bottom
        GL.glVertex2i(bounding_rect[3], bounding_rect[0])  # right, top
        GL.glEnd()
        GL.glEnable(GL.GL_LIGHTING)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)


def _compute_bounds(arr: np.ndarray, pid: int) -> "List[int] | None":
    """Find the pixels with R==pid and G==B==0 in the pick-encoded
    framebuffer.  Return [top, bottom, left, right] in window coords
    (y=0 at top), or None if no pixels matched."""
    mask = (
        (arr[:, :, 0] == pid)
        & (arr[:, :, 1] == 0)
        & (arr[:, :, 2] == 0)
    )
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    h = arr.shape[0]
    # arr[0] is the bottom row (glReadPixels GL convention).  Flip y so
    # the bbox is in window coords matching the flipped ortho below.
    y_max_arr = int(ys.max())  # near top of screen
    y_min_arr = int(ys.min())  # near bottom of screen
    top = h - 1 - y_max_arr
    bottom = h - 1 - y_min_arr
    return [top, bottom, int(xs.min()), int(xs.max())]


def process_selection(window, x_pos: float, y_pos: float) -> None:
    global selected_object, bounding_rect
    win_w, win_h = glfw.get_window_size(window)
    fb_w, fb_h = glfw.get_framebuffer_size(window)
    scale_x = fb_w / float(win_w) if win_w else 1.0
    scale_y = fb_h / float(win_h) if win_h else 1.0
    fb_x = int(x_pos * scale_x)
    fb_y = fb_h - int(y_pos * scale_y) - 1

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
    fb = GL.glReadPixels(0, 0, fb_w, fb_h, GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
    arr = np.frombuffer(fb, dtype=np.uint8).reshape(fb_h, fb_w, 3)
    obj_id = int(arr[fb_y, fb_x, 0])

    if obj_id == 0:
        return
    # Toggle: clicking the already-selected object deselects it.
    if obj_id == selected_object:
        selected_object = 0
        return
    bounds = _compute_bounds(arr, obj_id)
    if bounds is None:
        return
    # Scale framebuffer-space bbox down to window space (HiDPI).
    bounding_rect = [
        int(bounds[0] / scale_y),
        int(bounds[1] / scale_y),
        int(bounds[2] / scale_x),
        int(bounds[3] / scale_x),
    ]
    selected_object = obj_id


def setup_rc() -> None:
    dim_light = (0.1, 0.1, 0.1, 1.0)
    source_light = (0.65, 0.65, 0.65, 1.0)
    light_pos = (0.0, 0.0, 0.0, 1.0)
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
    global f_aspect
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    f_aspect = float(w) / float(h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(60.0, f_aspect, 1.0, 425.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_panel() -> None:
    """Checkbox to swap the on-screen render between the lit scene and
    the pick-color visualization."""
    global show_pick_buffer
    imgui.begin("Selection")
    _, show_pick_buffer = imgui.checkbox("Show selection buffer",
                                         show_pick_buffer)
    imgui.text("Click an object to select; click again to deselect.")
    imgui.end()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "Select an Object", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    # GlfwRenderer installs its own mouse-button callback.  Polling the
    # button each frame and edge-detecting a press avoids the conflict
    # and lets us check imgui's want_capture_mouse so clicks on the
    # panel don't pick.
    impl = GlfwRenderer(window)

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
        imgui_panel()
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
