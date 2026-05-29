"""Shared helpers for the SuperBible ports.

All ports under ``/mvp/ports/openglsuperbiblev4/chaptNN/<demo>/<demo>.py``
import this module to pick up:

  - ``resolve_default_window_size()``  — pick a sensible initial size
    (1920x1080 capped to the primary monitor, or 90% of monitor on
    smaller displays).

  - ``init_imgui(window)``             — set up imgui_bundle + GlfwRenderer.
    Returns the renderer; caller calls ``impl.process_inputs()``,
    ``impl.render(imgui.get_draw_data())``, ``impl.shutdown()``.

  - ``WindowState``                    — dataclass tracking the borderless-
    fullscreen toggle state and the saved windowed geometry to restore to.

  - ``draw_menubar(window, state)``    — the standard menubar with
    File→Quit and View→Fullscreen. Mutates state on toggle and sets
    the GLFW close flag on Quit.

  - ``Camera``, ``SceneObject``         — unified walk-around / focus
    camera for 3D demos. ``Camera.position`` + ``rot_y`` + ``rot_x`` is
    the walk-around state (Bill's preferred terminology, NOT yaw/pitch).
    Set ``Camera.focus_index`` ≥ 0 to switch to orbital mode around
    ``scene_objects[focus_index]``.

  - ``bind_camera_inputs(window, camera)`` — register the GLFW scroll
    callback that feeds the camera. Chains with any prior callback.
    Call once at startup.

  - ``update_camera(window, camera, scene_objects)`` — read keyboard,
    mouse drag, and scroll each frame; mutate the camera. Call between
    ``impl.process_inputs()`` and your ``render_scene()``.

  - ``apply_camera(camera, scene_objects)`` — emit ``glRotatef``/
    ``glTranslatef`` on the current ``GL_MODELVIEW`` matrix. Call after
    ``glLoadIdentity()`` but before drawing scene geometry.

  - ``draw_camera_controls(camera, scene_objects)`` — imgui panel with
    mode display, focus selector, current state, key reminders.

Each demo imports this by prepending the ports root to ``sys.path``.
For a demo at ``chaptNN/<demo>/<demo>.py`` (two levels under the ports
root) the canonical pattern is::

    PWD = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
    import _common

(Same convention as ``chapt11/_thunderbird_data.py``, but one level
higher in the tree.)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence, Tuple

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer


WINDOW_DEFAULT: Tuple[int, int] = (1920, 1080)


def resolve_default_window_size() -> Tuple[int, int]:
    """Pick an initial window size: 1920x1080 if the primary monitor
    fits it, otherwise 90% of the monitor's video mode."""
    monitor = glfw.get_primary_monitor()
    if monitor is None:
        return WINDOW_DEFAULT
    mode = glfw.get_video_mode(monitor)
    mw, mh = mode.size.width, mode.size.height
    if mw >= WINDOW_DEFAULT[0] and mh >= WINDOW_DEFAULT[1]:
        return WINDOW_DEFAULT
    return (int(mw * 0.9), int(mh * 0.9))


def init_imgui(window) -> GlfwRenderer:
    """Create the ImGui context and bind it to a GLFW window.
    Caller is responsible for calling ``shutdown()`` on the returned
    renderer at exit."""
    imgui.create_context()
    return GlfwRenderer(window)


@dataclass
class WindowState:
    """Window-level UI state.

    ``fullscreen`` and ``saved_*`` track the fullscreen toggle: when
    ``fullscreen`` flips False→True we save the current windowed
    geometry so the inverse toggle restores it.

    ``show_camera_controls`` is the visibility flag for the Camera
    panel (off by default; toggle from View → Show Controls). 2D demos
    that don't register a camera ignore this field.
    """
    fullscreen: bool = False
    saved_x: int = 0
    saved_y: int = 0
    saved_w: int = 0
    saved_h: int = 0
    show_camera_controls: bool = False


def toggle_fullscreen(window, state: WindowState) -> None:
    """Flip between windowed and exclusive fullscreen on the primary
    monitor. Uses ``glfw.set_window_monitor`` — same path as
    ``chapt19/fscreen``'s ``glfw.create_window(..., monitor, ...)``,
    just applied to an already-running window. Pass monitor=None on
    the way back to return to the saved windowed geometry.
    """
    if state.fullscreen:
        glfw.set_window_monitor(window, None,
                                state.saved_x, state.saved_y,
                                state.saved_w, state.saved_h, 0)
        state.fullscreen = False
    else:
        state.saved_x, state.saved_y = glfw.get_window_pos(window)
        state.saved_w, state.saved_h = glfw.get_window_size(window)
        monitor = glfw.get_primary_monitor()
        if monitor is None:
            return
        mode = glfw.get_video_mode(monitor)
        glfw.set_window_monitor(window, monitor, 0, 0,
                                mode.size.width, mode.size.height,
                                mode.refresh_rate)
        state.fullscreen = True


def draw_menubar(window, state: WindowState, *,
                 has_camera_controls: bool = False) -> None:
    """Draw the standard menubar. Sets GLFW close flag on Quit, calls
    ``toggle_fullscreen`` on the View toggle. Must be called inside
    the imgui frame (between ``imgui.new_frame()`` and ``imgui.render()``).

    When ``has_camera_controls=True``, View also shows a "Show Controls"
    toggle bound to ``state.show_camera_controls``. The demo's main loop
    is responsible for actually calling ``draw_camera_controls`` (which
    returns early when the flag is False).

    Pushes a tighter ``frame_padding`` style around the main menubar so
    the bar height stays close to the font height."""
    imgui.push_style_var(
        imgui.StyleVar_.frame_padding.value, (6.0, 2.0))
    opened = imgui.begin_main_menu_bar()
    if not opened:
        imgui.pop_style_var(1)
        return
    if imgui.begin_menu("File", True):
        clicked_quit, _ = imgui.menu_item("Quit", "Esc", False, True)
        if clicked_quit:
            glfw.set_window_should_close(window, True)
        imgui.end_menu()
    if imgui.begin_menu("View", True):
        clicked_fs, _ = imgui.menu_item(
            "Fullscreen", "", state.fullscreen, True)
        if clicked_fs:
            toggle_fullscreen(window, state)
        if has_camera_controls:
            _, state.show_camera_controls = imgui.menu_item(
                "Show Controls", "", state.show_camera_controls, True)
        imgui.end_menu()
    imgui.end_main_menu_bar()
    imgui.pop_style_var(1)


def menu_action(label: str, key: str, action: Callable[[], None], *,
                selected: bool = False) -> None:
    """A menubar item that mirrors a keyboard control. ``key`` is shown in the
    item's right-hand shortcut column (so the menu both performs the action and
    tells the user the keyboard equivalent); ``selected`` shows a check mark
    (for the current mode / shader). Clicking runs ``action()`` once -- menus
    can't "hold to repeat", so continuous motion stays on the keyboard and the
    menu item is a discoverable single-step. Call inside a ``begin_menu`` block."""
    clicked, _ = imgui.menu_item(label, key, selected, True)
    if clicked:
        action()


# ---------------------------------------------------------------------------
# Camera (walk-around with optional focus-orbit on a scene object)
# ---------------------------------------------------------------------------
#
# State follows Bill's convention from /mvp/mvpVisualization/: world-space
# position + angle rotated around Y + angle rotated around X (NOT yaw / pitch
# / roll; we don't have roll). When ``focus_index`` is -1 the camera is in
# walk-around mode and ``position`` is the world-space camera location. When
# ``focus_index`` ≥ 0 the camera orbits ``scene_objects[focus_index]`` at
# distance ``focus_radius``; ``position`` is unused while focused.
#
# The scene-object position is a callable so animated objects (a torus that
# orbits the origin, a planet on a path) keep being tracked while focused.


@dataclass
class SceneObject:
    """A focusable object the camera can orbit. ``position`` is a
    callable returning the current world-space position so animated
    objects keep being tracked while focused."""
    name: str
    position: Callable[[], Tuple[float, float, float]]


@dataclass
class Camera:
    """Walk-around camera with optional focus-orbit on a scene object.

    Walk-around state (used when ``focus_index < 0``):
        * ``position``  — world-space camera location.
        * ``rot_y``    — angle around world Y (radians, "look left/right").
        * ``rot_x``    — angle around camera-local X (radians, "look up/down").
                         Clamped to ±π/2 so you can't flip over.

    Focus-orbit state (used when ``focus_index ≥ 0``):
        * ``focus_index`` is an index into the ``scene_objects`` list.
        * ``focus_radius`` is the distance from the focus object's center.
        * ``rot_y`` / ``rot_x`` are reused for the orbit angles.

    Speed knobs are per-camera (override at construction for demos with
    very small or very large worlds). All distances/speeds are in the
    demo's world units; pick something sensible for your scene scale.
    """

    position: List[float] = field(
        default_factory=lambda: [0.0, 0.0, 10.0])
    rot_y: float = 0.0
    rot_x: float = 0.0
    focus_index: int = -1
    focus_radius: float = 25.0

    move_speed: float = 1.0
    look_step: float = math.radians(2.0)
    mouse_look_speed: float = 0.005
    scroll_speed: float = 1.0

    _prev_mouse: Optional[Tuple[float, float]] = None
    _scroll_accum: float = 0.0


def bind_camera_inputs(window, camera: Camera) -> None:
    """Register a GLFW scroll callback that feeds the camera. Chains
    with any previously-registered scroll callback (so demos that have
    their own scroll handler keep it). Call once at startup, after
    ``glfw.create_window`` and the demo's other callbacks."""
    prev_cb = glfw.set_scroll_callback(window, None)

    def _scroll_cb(_win, x_offset: float, y_offset: float) -> None:
        camera._scroll_accum += y_offset
        if prev_cb is not None:
            prev_cb(_win, x_offset, y_offset)

    glfw.set_scroll_callback(window, _scroll_cb)


def update_camera(window, camera: Camera,
                  scene_objects: Sequence[SceneObject]) -> None:
    """Read input and update camera state. Call between
    ``impl.process_inputs()`` and the demo's render code each frame.

    Walk-around mode bindings:
        W / S         move forward / back along camera-relative -Z (horizontal)
        A / D         strafe left / right along camera-relative +X
        Q / E         move down / up along world Y
        Arrows        look (rot_y left/right, rot_x up/down)
        Left-drag     mouse-look
        Scroll        forward/back along camera -Z

    Focus-orbit mode bindings:
        Arrows        orbit
        Left-drag     orbit
        Scroll        zoom (radius)

    Respects ``imgui.io.want_capture_*`` so clicking inside an imgui
    panel doesn't move the camera."""
    io = imgui.get_io()
    want_kbd = io.want_capture_keyboard
    want_mouse = io.want_capture_mouse

    cy, sy = math.cos(camera.rot_y), math.sin(camera.rot_y)
    fwd_x, fwd_z = -sy, -cy
    right_x, right_z = cy, -sy

    if camera._scroll_accum != 0.0 and not want_mouse:
        if camera.focus_index < 0:
            d = camera._scroll_accum * camera.scroll_speed
            camera.position[0] += fwd_x * d
            camera.position[2] += fwd_z * d
        else:
            camera.focus_radius -= camera._scroll_accum * camera.scroll_speed
            if camera.focus_radius < 0.1:
                camera.focus_radius = 0.1
    camera._scroll_accum = 0.0

    if not want_kbd:
        if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
            camera.rot_y += camera.look_step
        if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
            camera.rot_y -= camera.look_step
        if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
            camera.rot_x -= camera.look_step
        if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
            camera.rot_x += camera.look_step

        if camera.focus_index < 0:
            ms = camera.move_speed
            if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
                camera.position[0] += fwd_x * ms
                camera.position[2] += fwd_z * ms
            if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
                camera.position[0] -= fwd_x * ms
                camera.position[2] -= fwd_z * ms
            if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
                camera.position[0] += right_x * ms
                camera.position[2] += right_z * ms
            if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
                camera.position[0] -= right_x * ms
                camera.position[2] -= right_z * ms
            if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
                camera.position[1] += ms
            if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
                camera.position[1] -= ms

    if not want_mouse:
        cur = glfw.get_cursor_pos(window)
        pressed = (glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT)
                   == glfw.PRESS)
        if pressed:
            if camera._prev_mouse is not None:
                dx = cur[0] - camera._prev_mouse[0]
                dy = cur[1] - camera._prev_mouse[1]
                camera.rot_y -= dx * camera.mouse_look_speed
                camera.rot_x -= dy * camera.mouse_look_speed
            camera._prev_mouse = cur
        else:
            camera._prev_mouse = None
    else:
        camera._prev_mouse = None

    half_pi = math.pi / 2.0
    if camera.rot_x > half_pi:
        camera.rot_x = half_pi
    elif camera.rot_x < -half_pi:
        camera.rot_x = -half_pi


def apply_camera(camera: Camera,
                 scene_objects: Sequence[SceneObject]) -> None:
    """Emit the camera transform on the current ``GL_MODELVIEW``
    matrix. Call right after ``glLoadIdentity()`` and before the demo
    draws scene geometry. Must be in ``glMatrixMode(GL_MODELVIEW)``."""
    if 0 <= camera.focus_index < len(scene_objects):
        ox, oy, oz = scene_objects[camera.focus_index].position()
        GL.glTranslatef(0.0, 0.0, -camera.focus_radius)
        GL.glRotatef(math.degrees(camera.rot_x), 1.0, 0.0, 0.0)
        GL.glRotatef(math.degrees(-camera.rot_y), 0.0, 1.0, 0.0)
        GL.glTranslatef(-ox, -oy, -oz)
    else:
        GL.glRotatef(math.degrees(-camera.rot_x), 1.0, 0.0, 0.0)
        GL.glRotatef(math.degrees(-camera.rot_y), 0.0, 1.0, 0.0)
        GL.glTranslatef(-camera.position[0],
                        -camera.position[1],
                        -camera.position[2])


def draw_camera_controls(camera: Camera,
                         scene_objects: Sequence[SceneObject],
                         state: WindowState) -> None:
    """ImGui panel: shows current mode + state, lets the user pick a
    focus object or return to walk-around. Hidden by default; toggled
    on via View → Show Controls in the menubar (or the window's X
    button). Call inside the imgui frame after ``draw_menubar``; safe
    to call unconditionally — returns early when the panel is hidden."""
    if not state.show_camera_controls:
        return
    expanded, state.show_camera_controls = imgui.begin(
        "Camera", state.show_camera_controls)
    if not expanded:
        imgui.end()
        return

    if camera.focus_index < 0:
        imgui.text("Mode: Walk-around")
        imgui.text(
            f"Position: ({camera.position[0]:.2f}, "
            f"{camera.position[1]:.2f}, {camera.position[2]:.2f})")
    else:
        obj = scene_objects[camera.focus_index]
        ox, oy, oz = obj.position()
        imgui.text(f"Mode: Focus on '{obj.name}'")
        imgui.text(f"Object at ({ox:.2f}, {oy:.2f}, {oz:.2f})")
        _, camera.focus_radius = imgui.slider_float(
            "Radius", camera.focus_radius, 0.1, 1000.0)

    imgui.text(
        f"rot_y={math.degrees(camera.rot_y):6.1f}°  "
        f"rot_x={math.degrees(camera.rot_x):6.1f}°")
    imgui.separator()
    imgui.text("Focus on:")
    if imgui.radio_button("(walk around)", camera.focus_index < 0):
        camera.focus_index = -1
    for i, obj in enumerate(scene_objects):
        if imgui.radio_button(obj.name, camera.focus_index == i):
            camera.focus_index = i
    imgui.separator()
    imgui.text_wrapped(
        "Walk-around: WASD strafes, QE up/down. Arrows or left-mouse "
        "drag to look. Scroll to move forward/back. Pick an object "
        "above to orbit around it instead.")
    imgui.end()
