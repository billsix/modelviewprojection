# spot.py
# Demonstrates a spotlight illuminating a sphere. The C++ original used
# a GLUT right-click menu to switch between flat/smooth shading and
# three tessellation levels; replaced here with an ImGui panel.
# OpenGL SuperBible, Chapter 5
# Python port of Spot.cpp by Richard S. Wright Jr.

import math
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
import _common  # noqa: E402
import _primitives  # noqa: E402

_window = None  # set in main(); used by the Controls buttons

x_rot: float = 0.0
y_rot: float = 0.0

light_pos = (0.0, 0.0, 75.0, 1.0)
specular = (1.0, 1.0, 1.0, 1.0)
specref = (1.0, 1.0, 1.0, 1.0)
ambient_light = (0.5, 0.5, 0.5, 1.0)
spot_dir = (0.0, 0.0, -1.0)

MODE_FLAT = 1
MODE_SMOOTH = 2
MODE_VERYLOW = 3
MODE_MEDIUM = 4
MODE_VERYHIGH = 5

i_shade: int = MODE_FLAT
i_tess: int = MODE_VERYLOW


def _build_slant_cone(
    base: float, height: float, slices: int, stacks: int
) -> "_primitives.Mesh":
    """Spot's cone: base at z=0, apex at z=+height, with a *slant* normal per
    vertex (radial + a +Z slope component, normalized) -- distinct from the
    flat-normal fan cone in _primitives.build_cone. GL_QUAD_STRIP per stack,
    emitting apex-side (r1,z1) then base-side (r0,z0) so the outward faces wind
    CCW under glFrontFace(GL_CCW) (else they'd be culled). Per-vertex normals,
    so replay with the default draw_mesh."""
    slope = base / height if height != 0 else 0.0
    mag = math.sqrt(1.0 + slope * slope)
    nz = slope / mag
    bands: list = []
    for i in range(stacks):
        z0 = float(i) / stacks * height
        z1 = float(i + 1) / stacks * height
        r0 = base * (1.0 - float(i) / stacks)
        r1 = base * (1.0 - float(i + 1) / stacks)
        band: list = []
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            nx, ny = cl / mag, sl / mag
            band.append((nx, ny, nz, 0.0, 0.0, r1 * cl, r1 * sl, z1))
            band.append((nx, ny, nz, 0.0, 0.0, r0 * cl, r0 * sl, z0))
        bands.append(band)
    return (GL.GL_QUAD_STRIP, bands)


def _build_cone_cap(base: float, slices: int) -> "_primitives.Mesh":
    """Cone base cap at z=0 facing -Z, wound (cos, -sin) so it's CCW from -Z;
    one flat normal for the whole fan -- replay with draw_mesh(flat=True)."""
    band: list = [(0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0)]
    for j in range(slices + 1):
        lng = 2.0 * math.pi * float(j) / slices
        band.append(
            (
                0.0,
                0.0,
                -1.0,
                0.0,
                0.0,
                base * math.cos(lng),
                -base * math.sin(lng),
                0.0,
            )
        )
    return (GL.GL_TRIANGLE_FAN, [band])


# Geometry is fixed (the cone) or one of three fixed tessellations (the blue
# sphere, switched live via the imgui Tessellation panel) -- tessellate every
# variant once at import, replay each frame. All spheres use swap_winding so
# they emit (lat1, lat0) per band: the camera-facing side then winds CCW under
# glFrontFace(GL_CCW) and isn't culled (the unlit far hemisphere otherwise).
CONE_SLANT = _build_slant_cone(4.0, 6.0, 15, 15)
CONE_CAP = _build_cone_cap(4.0, 15)
BULB_SPHERE = _primitives.build_sphere(3.0, 15, 15, swap_winding=True)
BLUE_SPHERE_LOW = _primitives.build_sphere(30.0, 7, 7, swap_winding=True)
BLUE_SPHERE_MEDIUM = _primitives.build_sphere(30.0, 15, 15, swap_winding=True)
BLUE_SPHERE_HIGH = _primitives.build_sphere(30.0, 50, 50, swap_winding=True)


def render_scene() -> None:
    if i_shade == MODE_FLAT:
        GL.glShadeModel(GL.GL_FLAT)
    else:
        GL.glShadeModel(GL.GL_SMOOTH)

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPushMatrix()
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)

    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPOT_DIRECTION, spot_dir)

    # Red cone enclosing the light source
    GL.glColor3ub(255, 0, 0)
    GL.glTranslatef(light_pos[0], light_pos[1], light_pos[2])
    _primitives.draw_mesh(CONE_SLANT)
    _primitives.draw_mesh(CONE_CAP, flat=True)

    # Yellow sphere -- lighting off so it appears self-lit
    GL.glPushAttrib(GL.GL_LIGHTING_BIT)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glColor3ub(255, 255, 0)
    _primitives.draw_mesh(BULB_SPHERE)
    GL.glPopAttrib()

    GL.glPopMatrix()

    # The blue sphere being illuminated
    GL.glColor3ub(0, 0, 255)
    if i_tess == MODE_VERYLOW:
        _primitives.draw_mesh(BLUE_SPHERE_LOW)
    elif i_tess == MODE_MEDIUM:
        _primitives.draw_mesh(BLUE_SPHERE_MEDIUM)
    else:
        _primitives.draw_mesh(BLUE_SPHERE_HIGH)


def _nudge_x(d: float) -> None:
    global x_rot
    x_rot += d


def _nudge_y(d: float) -> None:
    global y_rot
    y_rot += d


def _set_shade(mode: int) -> None:
    global i_shade
    i_shade = mode


def _set_tess(mode: int) -> None:
    global i_tess
    i_tess = mode


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column (discovery); hold the key for
    # continuous rotation.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Shade Model", True):
        _common.menu_action(
            "Flat",
            "",
            lambda: _set_shade(MODE_FLAT),
            selected=(i_shade == MODE_FLAT),
        )
        _common.menu_action(
            "Smooth",
            "",
            lambda: _set_shade(MODE_SMOOTH),
            selected=(i_shade == MODE_SMOOTH),
        )
        imgui.end_menu()
    if imgui.begin_menu("Tessellation", True):
        _common.menu_action(
            "Very Low",
            "",
            lambda: _set_tess(MODE_VERYLOW),
            selected=(i_tess == MODE_VERYLOW),
        )
        _common.menu_action(
            "Medium",
            "",
            lambda: _set_tess(MODE_MEDIUM),
            selected=(i_tess == MODE_MEDIUM),
        )
        _common.menu_action(
            "Very High",
            "",
            lambda: _set_tess(MODE_VERYHIGH),
            selected=(i_tess == MODE_VERYHIGH),
        )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Rotate Up", "Up", lambda: _nudge_x(-2.0))
        _common.menu_action("Rotate Down", "Down", lambda: _nudge_x(2.0))
        _common.menu_action("Rotate Left", "Left", lambda: _nudge_y(-2.0))
        _common.menu_action("Rotate Right", "Right", lambda: _nudge_y(2.0))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_LIGHTING)

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, specular)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glLightf(GL.GL_LIGHT0, GL.GL_SPOT_CUTOFF, 50.0)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, specref)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    GL.glClearColor(0.0, 0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    f_aspect = float(w) / float(h)
    GLU.gluPerspective(35.0, f_aspect, 1.0, 500.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -250.0)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


# Rotation rate while an arrow key is held. Multiplied by frame delta
# so the rotation speed is independent of the render framerate.
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

    window = glfw.create_window(800, 600, "Spot Light", None, None)
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
    # callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

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
