# fboshadowmap.py
# Shadow mapping with framebuffer objects. Same fixed-function shadow
# pipeline as chapt14/shadowmap, but the depth pass renders into an
# off-screen depth renderbuffer instead of the back buffer, so the
# shadow texture can be larger than the window.
#
# Keys: X/Y/Z + shift to move; arrows for x/z; Esc to quit. Shadows,
# show-shadow-map, FBO, camera/light control, and the polygon-offset
# factor live on an imgui panel. Octahedron replaced with a manual
# 8-triangle mesh.
#
# OpenGL SuperBible, Chapter 18
# Python port of fboshadowmap.cpp by Benjamin Lipchak

import math
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
import _primitives  # noqa: E402
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit control button
window_width: int = 512
window_height: int = 512
shadow_width: int = 512
shadow_height: int = 512

control_camera: bool = True
no_shadows: bool = False
show_shadow_map: bool = False
use_fbo: bool = False
factor: float = 4.0
ambient_shadow_available: bool = False

ambient_light = [0.2, 0.2, 0.2, 1.0]
diffuse_light = [0.7, 0.7, 0.7, 1.0]
light_pos = [100.0, 300.0, 100.0, 1.0]
camera_pos = [100.0, 150.0, 200.0, 1.0]
camera_zoom: float = 0.3

shadow_texture_id: int = 0
framebuffer_id: int = 0
renderbuffer_id: int = 0
max_tex_size: int = 0
texture_matrix = np.identity(4, dtype=np.float32)


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


SPHERE = _primitives.build_sphere(25.0, 50, 50)
CONE = _primitives.build_cone(25.0, 50.0, 50)
TORUS = _primitives.build_torus(16.0, 8.0, 50, 50)


def draw_solid_octahedron() -> None:
    verts = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    faces = [(0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
             (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5)]
    GL.glBegin(GL.GL_TRIANGLES)
    for i, j, k in faces:
        a, b, c = verts[i], verts[j], verts[k]
        nx = (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1])
        ny = (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2])
        nz = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        GL.glNormal3f(nx, ny, nz)
        GL.glVertex3f(*a); GL.glVertex3f(*b); GL.glVertex3f(*c)
    GL.glEnd()


def draw_models(draw_base: bool) -> None:
    if draw_base:
        GL.glColor3f(0.0, 0.0, 0.90); GL.glNormal3f(0.0, 1.0, 0.0)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex3f(-100.0, -25.0, -100.0)
        GL.glVertex3f(-100.0, -25.0, 100.0)
        GL.glVertex3f(100.0, -25.0, 100.0)
        GL.glVertex3f(100.0, -25.0, -100.0)
        GL.glEnd()

    GL.glColor3f(1.0, 0.0, 0.0); draw_solid_cube(48.0)
    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glPushMatrix(); GL.glTranslatef(-60.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE); GL.glPopMatrix()
    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glPushMatrix(); GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glTranslatef(60.0, 0.0, -24.0)
    _primitives.draw_mesh(CONE, flat=True); GL.glPopMatrix()
    GL.glColor3f(1.0, 0.0, 1.0)
    GL.glPushMatrix(); GL.glTranslatef(0.0, 0.0, 60.0)
    _primitives.draw_mesh(TORUS); GL.glPopMatrix()
    GL.glColor3f(0.0, 1.0, 1.0)
    GL.glPushMatrix(); GL.glTranslatef(0.0, 0.0, -60.0)
    GL.glScalef(25.0, 25.0, 25.0)
    draw_solid_octahedron(); GL.glPopMatrix()


def regenerate_shadow_map() -> None:
    global texture_matrix
    light_to_scene = math.sqrt(sum(p * p for p in light_pos[:3]))
    scene_radius = 95.0
    near_plane = light_to_scene - scene_radius
    fov = math.degrees(2.0 * math.atan(scene_radius / light_to_scene))

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(fov, 1.0, near_plane, near_plane + 2.0 * scene_radius)
    light_proj = np.array(GL.glGetFloatv(GL.GL_PROJECTION_MATRIX),
                          dtype=np.float32).reshape((4, 4))
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(light_pos[0], light_pos[1], light_pos[2],
                  0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    light_mv = np.array(GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX),
                        dtype=np.float32).reshape((4, 4))
    GL.glViewport(0, 0, shadow_width, shadow_height)

    if use_fbo:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id)
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
    GL.glShadeModel(GL.GL_FLAT)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glDisable(GL.GL_COLOR_MATERIAL)
    GL.glDisable(GL.GL_NORMALIZE)
    GL.glColorMask(False, False, False, False)
    GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
    draw_models(False)
    GL.glCopyTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT,
                        0, 0, shadow_width, shadow_height, 0)
    if use_fbo:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glEnable(GL.GL_NORMALIZE)
    GL.glColorMask(True, True, True, True)
    GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)

    bias = np.array([
        [0.5, 0.0, 0.0, 0.5],
        [0.0, 0.5, 0.0, 0.5],
        [0.0, 0.0, 0.5, 0.5],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=np.float32)
    # GL matrices are column-major, so light_proj_T @ light_mv_T = (light_mv @ light_proj).T
    proj_t = light_proj.T
    mv_t = light_mv.T
    combined = bias @ proj_t @ mv_t
    texture_matrix = combined.T  # rows = s,t,r,q plane equations


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
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    if show_shadow_map:
        GL.glMatrixMode(GL.GL_PROJECTION); GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_MODELVIEW); GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_TEXTURE); GL.glPushMatrix(); GL.glLoadIdentity()
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glDisable(GL.GL_LIGHTING)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_REPLACE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_COMPARE_MODE, GL.GL_NONE)
        # Stretch the depth texture to fill the entire window. The
        # SuperBible original sized the quad to the texture's native
        # pixel dimensions (so a 512×512 shadow map appeared in the
        # bottom-left of a 1920×1080 window). For an educational
        # debug view we want it to fill the screen.
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex2f(-1.0, -1.0)
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex2f( 1.0, -1.0)
        GL.glTexCoord2f(1.0, 1.0); GL.glVertex2f( 1.0,  1.0)
        GL.glTexCoord2f(0.0, 1.0); GL.glVertex2f(-1.0,  1.0)
        GL.glEnd()
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
    elif no_shadows:
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
        draw_models(True)
    else:
        if not ambient_shadow_available:
            low_amb = [0.1, 0.1, 0.1, 1.0]
            low_dif = [0.35, 0.35, 0.35, 1.0]
            GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, low_amb)
            GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, low_dif)
            draw_models(True)
            GL.glAlphaFunc(GL.GL_GREATER, 0.9)
            GL.glEnable(GL.GL_ALPHA_TEST)

        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_COMPARE_MODE,
                           GL.GL_COMPARE_R_TO_TEXTURE)
        for gen in (GL.GL_TEXTURE_GEN_S, GL.GL_TEXTURE_GEN_T,
                    GL.GL_TEXTURE_GEN_R, GL.GL_TEXTURE_GEN_Q):
            GL.glEnable(gen)
        GL.glTexGenfv(GL.GL_S, GL.GL_EYE_PLANE, texture_matrix[0])
        GL.glTexGenfv(GL.GL_T, GL.GL_EYE_PLANE, texture_matrix[1])
        GL.glTexGenfv(GL.GL_R, GL.GL_EYE_PLANE, texture_matrix[2])
        GL.glTexGenfv(GL.GL_Q, GL.GL_EYE_PLANE, texture_matrix[3])
        draw_models(True)
        GL.glDisable(GL.GL_ALPHA_TEST)
        GL.glDisable(GL.GL_TEXTURE_2D)
        for gen in (GL.GL_TEXTURE_GEN_S, GL.GL_TEXTURE_GEN_T,
                    GL.GL_TEXTURE_GEN_R, GL.GL_TEXTURE_GEN_Q):
            GL.glDisable(gen)


def setup_rc() -> None:
    global shadow_texture_id, framebuffer_id, renderbuffer_id, max_tex_size

    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glPolygonOffset(factor, 0.0)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glEnable(GL.GL_NORMALIZE)
    GL.glEnable(GL.GL_LIGHT0)

    max_tex_size = GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE)
    max_rb = GL.glGetIntegerv(GL.GL_MAX_RENDERBUFFER_SIZE)
    max_tex_size = min(max_tex_size, max_rb, 2048)

    shadow_texture_id = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_texture_id)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_DEPTH_TEXTURE_MODE, GL.GL_INTENSITY)
    for axis in (GL.GL_S, GL.GL_T, GL.GL_R, GL.GL_Q):
        GL.glTexGeni(axis, GL.GL_TEXTURE_GEN_MODE, GL.GL_EYE_LINEAR)

    framebuffer_id = GL.glGenFramebuffers(1)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id)
    renderbuffer_id = GL.glGenRenderbuffers(1)
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, renderbuffer_id)
    GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT32,
                             max_tex_size, max_tex_size)
    GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT,
                                 GL.GL_RENDERBUFFER, renderbuffer_id)
    GL.glDrawBuffer(GL.GL_NONE)
    GL.glReadBuffer(GL.GL_NONE)
    if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
        sys.stderr.write("FBO incomplete\n")
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    regenerate_shadow_map()


def change_size(w: int, h: int) -> None:
    global window_width, window_height, shadow_width, shadow_height
    orig_w, orig_h = shadow_width, shadow_height
    window_width, window_height = w, h
    if use_fbo:
        shadow_width = shadow_height = max_tex_size
    else:
        shadow_width = w
        shadow_height = h
    if shadow_width > max_tex_size: shadow_width = max_tex_size
    if shadow_height > max_tex_size: shadow_height = max_tex_size
    if (orig_w, orig_h) != (shadow_width, shadow_height):
        regenerate_shadow_map()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def _nudge(axis: int, delta: float) -> None:
    # Move whichever target the panel/keyboard selects (camera or light);
    # moving the light requires regenerating the shadow map (mirrors on_key).
    target = camera_pos if control_camera else light_pos
    target[axis] += delta
    if not control_camera:
        regenerate_shadow_map()


def _set_shadows(on: bool) -> None:
    # "Shadows" on means no_shadows off. The old S key cleared show_shadow_map.
    global no_shadows, show_shadow_map
    no_shadows = not on
    show_shadow_map = False


def _set_show_shadow_map(v: bool) -> None:
    # The old M key cleared no_shadows.
    global show_shadow_map, no_shadows
    show_shadow_map = v
    no_shadows = False


def _set_use_fbo(v: bool) -> None:
    global use_fbo
    use_fbo = v
    change_size(window_width, window_height)


def _set_control_camera(v: bool) -> None:
    global control_camera
    control_camera = v


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column; hold the key for continuous
    # motion. They move whichever target the Control mode selects.
    global factor
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Options", True):
        clicked, v = imgui.menu_item("Shadows", "", not no_shadows, True)
        if clicked:
            _set_shadows(v)
        clicked, v = imgui.menu_item("Show shadow map", "", show_shadow_map, True)
        if clicked:
            _set_show_shadow_map(v)
        clicked, v = imgui.menu_item("Use FBO", "", use_fbo, True)
        if clicked:
            _set_use_fbo(v)
        imgui.separator()
        _common.menu_action("Move camera", "", lambda: _set_control_camera(True),
                            selected=control_camera)
        _common.menu_action("Move light", "", lambda: _set_control_camera(False),
                            selected=not control_camera)
        imgui.separator()
        if imgui.begin_menu("Polygon offset", True):
            changed, factor = imgui.slider_float("Factor", factor, 0.0, 10.0)
            if changed:
                GL.glPolygonOffset(factor, 0.0)
                regenerate_shadow_map()
            imgui.end_menu()
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        # These move whichever target ("Move camera" / "Move light") is set.
        _common.menu_action("+X", "X", lambda: _nudge(0, 5.0))
        _common.menu_action("-X", "Shift+X", lambda: _nudge(0, -5.0))
        _common.menu_action("+Y", "Y", lambda: _nudge(1, 5.0))
        _common.menu_action("-Y", "Shift+Y", lambda: _nudge(1, -5.0))
        _common.menu_action("+Z", "Z", lambda: _nudge(2, 5.0))
        _common.menu_action("-Z", "Shift+Z", lambda: _nudge(2, -5.0))
        imgui.separator()
        _common.menu_action("Left", "Left", lambda: _nudge(0, -5.0))
        _common.menu_action("Right", "Right", lambda: _nudge(0, 5.0))
        _common.menu_action("Forward", "Up", lambda: _nudge(2, -5.0))
        _common.menu_action("Back", "Down", lambda: _nudge(2, 5.0))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    # Render-option toggles moved to the imgui panel; keys move the
    # camera or light (whichever the panel selects).
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True); return
    target = camera_pos if control_camera else light_pos
    delta = -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    if key == glfw.KEY_X:
        target[0] += delta
    elif key == glfw.KEY_Y:
        target[1] += delta
    elif key == glfw.KEY_Z:
        target[2] += delta
    elif key == glfw.KEY_LEFT:
        target[0] -= 5.0
    elif key == glfw.KEY_RIGHT:
        target[0] += 5.0
    elif key == glfw.KEY_UP:
        target[2] -= 5.0
    elif key == glfw.KEY_DOWN:
        target[2] += 5.0
    else:
        return
    if not control_camera:
        regenerate_shadow_map()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(window_width, window_height,
                                "FBO Shadow Mapping Demo", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    _window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    print("FBO Shadow Mapping Demo")
    print("  X/Y/Z + shift, arrows: move    Esc: quit")

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
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
