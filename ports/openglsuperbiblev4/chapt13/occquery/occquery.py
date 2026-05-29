# occquery.py
# Occlusion queries: a cube of 27 spheres is wrapped in bounding cubes;
# at draw time only the spheres whose bounding box passed depth testing
# in the previous frame are rendered. The render options (occlusion
# detection, bounding volumes, help overlay) live on an imgui panel;
# arrows and x/y/z (and SHIFT) fly the camera.
#
# Note: the C++ original used glutSolidTetrahedron/Octahedron/etc. for
# alternate bounding volumes; this port keeps just the box variant for
# simplicity.
#
# OpenGL SuperBible, Chapter 13
# Python port of occquery.cpp by Benjamin Lipchak

import math
import os
import sys
import time

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer



PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit control button
window_width: int = 1024
window_height: int = 768

show_menu: bool = True
occlusion_detection: bool = True
show_bounding_volume: bool = False
query_ids: np.ndarray = np.zeros(27, dtype=np.uint32)

ambient_light = (0.4, 0.4, 0.4, 1.0)
diffuse_light = (0.9, 0.9, 0.9, 1.0)
light_pos = (100.0, 300.0, 100.0, 1.0)

camera_pos = [200.0, 300.0, 400.0, 1.0]
camera_zoom: float = 0.6
texture_id: int = 0


def draw_solid_cube(size: float) -> None:
    s = size / 2.0
    GL.glBegin(GL.GL_QUADS)
    for nx, ny, nz, vs in [
        (0, 0, 1, [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]),
        (0, 0, -1, [(s, -s, -s), (-s, -s, -s), (-s, s, -s), (s, s, -s)]),
        (1, 0, 0, [(s, -s, s), (s, -s, -s), (s, s, -s), (s, s, s)]),
        (-1, 0, 0, [(-s, -s, -s), (-s, -s, s), (-s, s, s), (-s, s, -s)]),
        (0, 1, 0, [(-s, s, s), (s, s, s), (s, s, -s), (-s, s, -s)]),
        (0, -1, 0, [(-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s)]),
    ]:
        GL.glNormal3f(nx, ny, nz)
        for v in vs:
            GL.glVertex3f(*v)
    GL.glEnd()


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        s0, c0 = math.sin(lat0), math.cos(lat0)
        s1, c1 = math.sin(lat1), math.cos(lat1)
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            GL.glNormal3f(cl * c0, sl * c0, s0)
            GL.glVertex3f(radius * cl * c0, radius * sl * c0, radius * s0)
            GL.glNormal3f(cl * c1, sl * c1, s1)
            GL.glVertex3f(radius * cl * c1, radius * sl * c1, radius * s1)
        GL.glEnd()


def draw_occluder() -> None:
    GL.glColor3f(0.5, 0.25, 0.0)
    for axis in range(3):
        GL.glPushMatrix()
        if axis == 0:
            GL.glScalef(30.0, 30.0, 1.0)
            for d in (50.0, -50.0):
                GL.glPushMatrix()
                GL.glTranslatef(0.0, 0.0, d)
                draw_solid_cube(10.0)
                GL.glPopMatrix()
        elif axis == 1:
            GL.glScalef(1.0, 30.0, 30.0)
            for d in (50.0, -50.0):
                GL.glPushMatrix()
                GL.glTranslatef(d, 0.0, 0.0)
                draw_solid_cube(10.0)
                GL.glPopMatrix()
        else:
            GL.glScalef(30.0, 1.0, 30.0)
            for d in (50.0, -50.0):
                GL.glPushMatrix()
                GL.glTranslatef(0.0, d, 0.0)
                draw_solid_cube(10.0)
                GL.glPopMatrix()
        GL.glPopMatrix()


def draw_sphere_at(idx: int) -> None:
    occluded = False
    if occlusion_detection:
        passing = GL.glGetQueryObjectiv(query_ids[idx], GL.GL_QUERY_RESULT)
        if passing == 0:
            occluded = True
    if not occluded:
        draw_solid_sphere(50.0, 100, 100)


def draw_models() -> None:
    draw_occluder()

    if occlusion_detection or show_bounding_volume:
        GL.glShadeModel(GL.GL_FLAT)
        if not show_bounding_volume:
            GL.glDisable(GL.GL_LIGHTING)
            GL.glDisable(GL.GL_COLOR_MATERIAL)
            GL.glDisable(GL.GL_NORMALIZE)
            GL.glDepthMask(GL.GL_FALSE)
            GL.glColorMask(False, False, False, False)
        for r in range(3):
            for g in range(3):
                for b in range(3):
                    if show_bounding_volume:
                        GL.glColor3f(r * 0.5, g * 0.5, b * 0.5)
                    GL.glPushMatrix()
                    GL.glTranslatef(100.0 * r - 100.0,
                                    100.0 * g - 100.0,
                                    100.0 * b - 100.0)
                    GL.glBeginQuery(GL.GL_SAMPLES_PASSED,
                                    int(query_ids[r * 9 + g * 3 + b]))
                    draw_solid_cube(100.0)
                    GL.glEndQuery(GL.GL_SAMPLES_PASSED)
                    GL.glPopMatrix()
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glEnable(GL.GL_NORMALIZE)
        GL.glColorMask(True, True, True, True)
        GL.glDepthMask(GL.GL_TRUE)

    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_TEXTURE_GEN_S)
    GL.glEnable(GL.GL_TEXTURE_GEN_T)

    for r in range(3):
        for g in range(3):
            for b in range(3):
                GL.glColor3f(r * 0.5, g * 0.5, b * 0.5)
                GL.glPushMatrix()
                GL.glTranslatef(100.0 * r - 100.0,
                                100.0 * g - 100.0,
                                100.0 * b - 100.0)
                draw_sphere_at(r * 9 + g * 3 + b)
                GL.glPopMatrix()

    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)


def render_scene() -> None:
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if window_width > window_height:
        ar = float(window_width) / float(window_height)
        GL.glFrustum(-ar * camera_zoom, ar * camera_zoom,
                     -camera_zoom, camera_zoom, 1.0, 1000.0)
    else:
        ar = float(window_height) / float(window_width)
        GL.glFrustum(-camera_zoom, camera_zoom,
                     -ar * camera_zoom, ar * camera_zoom, 1.0, 1000.0)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    GL.glViewport(0, 0, window_width, window_height)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_models()


def _nudge_cam(axis: int, d: float) -> None:
    camera_pos[axis] += d


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column (discovery); hold the key for
    # continuous motion.
    global occlusion_detection, show_bounding_volume, show_menu
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Render options", True):
        clicked, v = imgui.menu_item("Occlusion detection", "",
                                     occlusion_detection, True)
        if clicked:
            occlusion_detection = v
        clicked, v = imgui.menu_item("Show bounding volumes", "",
                                     show_bounding_volume, True)
        if clicked:
            show_bounding_volume = v
        clicked, v = imgui.menu_item("Show help overlay", "", show_menu, True)
        if clicked:
            show_menu = v
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Camera +X", "Left", lambda: _nudge_cam(0, 5.0))
        _common.menu_action("Camera -X", "Right", lambda: _nudge_cam(0, -5.0))
        _common.menu_action("Camera +Y", "Up", lambda: _nudge_cam(1, 5.0))
        _common.menu_action("Camera -Y", "Down", lambda: _nudge_cam(1, -5.0))
        _common.menu_action("Camera +Z", "Z", lambda: _nudge_cam(2, 5.0))
        _common.menu_action("Camera -Z", "Shift+Z", lambda: _nudge_cam(2, -5.0))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def setup_rc() -> None:
    global texture_id, query_ids

    query_ids = np.array(GL.glGenQueries(27), dtype=np.uint32)

    GL.glClearColor(0.3, 0.3, 0.3, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LESS)

    # Screen-door stipple pattern
    mask = np.zeros(32, dtype=np.uint32)
    for i in range(0, 32, 2):
        mask[i] = 0xAAAAAAAA
        mask[i + 1] = 0x55555555
    GL.glPolygonStipple(mask.view(np.uint8))

    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glEnable(GL.GL_NORMALIZE)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)

    GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_OBJECT_LINEAR)
    GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_OBJECT_LINEAR)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)

    img = np.flipud(iio.imread(os.path.join(PWD, "logo.tga")))
    h, w = img.shape[:2]
    fmt = (GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4
           else GL.GL_RGB)
    img = np.ascontiguousarray(img, dtype=np.uint8)
    texture_id = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)
    # Bind FIRST, then set the params on this texture.  The C++ wrote
    # to texture 0 (no glGenTextures, no glBindTexture) so its param
    # order didn't matter; we have a real texture name now and the
    # params need to land on it.  Without these, min-filter defaults
    # to GL_NEAREST_MIPMAP_LINEAR -- since we don't upload mipmaps,
    # the texture is incomplete and Mesa samples black.
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, fmt, w, h, 0, fmt,
                    GL.GL_UNSIGNED_BYTE, img)

    GL.glTexGenfv(GL.GL_S, GL.GL_OBJECT_PLANE,
                  np.array([1.0 / 50.0, 0.0, 0.0, -0.5], dtype=np.float32))
    GL.glTexGenfv(GL.GL_T, GL.GL_OBJECT_PLANE,
                  np.array([0.0, 1.0 / 50.0, 0.0, -0.5], dtype=np.float32))


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    # Render-option toggles (O/S/M) moved to the imgui panel; keys here
    # are navigation only.
    global camera_pos

    # Movement keys fire on PRESS or REPEAT so holding the key keeps
    # moving, matching GLUT glutSpecialFunc's auto-repeat behavior.
    is_movement = key in (glfw.KEY_LEFT, glfw.KEY_RIGHT,
                          glfw.KEY_UP, glfw.KEY_DOWN,
                          glfw.KEY_X, glfw.KEY_Y, glfw.KEY_Z)
    if action == glfw.PRESS:
        pass
    elif action == glfw.REPEAT and is_movement:
        pass
    else:
        return

    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    # Arrow keys -- matches C++ SpecialKeys.  LEFT/RIGHT moves X (note
    # the C++ inverts: LEFT increases, RIGHT decreases); UP/DOWN moves Y.
    elif key == glfw.KEY_LEFT:
        camera_pos[0] += 5.0
    elif key == glfw.KEY_RIGHT:
        camera_pos[0] -= 5.0
    elif key == glfw.KEY_UP:
        camera_pos[1] += 5.0
    elif key == glfw.KEY_DOWN:
        camera_pos[1] -= 5.0
    # x/y/z letter keys -- shift inverts direction.  Matches the
    # ProcessMenu callbacks in the C++ original.
    elif key == glfw.KEY_X:
        camera_pos[0] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Y:
        camera_pos[1] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Z:
        camera_pos[2] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
    window = glfw.create_window(window_width, window_height,
                                "Occlusion Query Demo", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    # FPS reporter.  C++ updates every 100 frames, but at Python
    # immediate-mode rates (a handful of fps with 540k triangles), 100
    # frames takes 20+ seconds and feels frozen.  Report on a 1-second
    # wall-clock cadence instead so the user sees the number quickly.
    frames = 0
    frame_timer = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        render_scene()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

        frames += 1
        now = time.monotonic()
        if now - frame_timer >= 1.0:
            fps = frames / (now - frame_timer)
            label = "with" if occlusion_detection else "without"
            glfw.set_window_title(
                window,
                f"Draw scene {label} occlusion detection {fps:.1f} fps",
            )
            frames = 0
            frame_timer = now

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
