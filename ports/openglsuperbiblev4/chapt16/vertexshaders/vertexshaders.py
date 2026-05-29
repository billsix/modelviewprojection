# vertexshaders.py
# Vertex shader gallery: 10 different vertex shaders that demonstrate
# the range of fixed-function effects you can replace with GLSL.
# The shaders themselves live in shaders/*.vs and are loaded at startup.
#
# C++ used a right-click GLUT menu to switch shaders. This port uses
# an imgui combo to pick one of the 10 shaders, with sliders that
# appear for the fog shaders (fog density) and the stretch shader
# (squash/stretch vector). The arrow and X/Y/Z keys are pure
# navigation now: LEFT/RIGHT rotate the lights, UP/DOWN and X/Y/Z move
# the camera. The C++ glutSolidTeapot is replaced with a second sphere
# — there is no equivalent in plain PyOpenGL and the teapot is
# decorative; the demo is about shaders.
#
# OpenGL SuperBible, Chapter 16
# Python port of vertexshaders.cpp by Benjamin Lipchak

import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer



PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _primitives  # noqa: E402
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit control button
window_width: int = 1024
window_height: int = 768

SIMPLE, DIFFUSE, SPECULAR, SEPSPEC, TEXSPEC = 0, 1, 2, 3, 4
THREELIGHTS, FOGCOORD, FOG, PTSIZE, STRETCH = 5, 6, 7, 8, 9
TOTAL_SHADERS = 10
shader_names = [
    "simple", "diffuse", "specular", "sepspec", "texspec",
    "3lights", "fogcoord", "fog", "ptsize", "stretch",
]

v_shader = [0] * TOTAL_SHADERS
prog_obj = [0] * TOTAL_SHADERS

which_shader: int = SIMPLE

camera_pos = [100.0, 75.0, 150.0, 1.0]
camera_zoom: float = 0.4

light_pos0 = np.array([140.0, 250.0, 140.0, 1.0], dtype=np.float32)
light_pos1 = np.array([-140.0, 250.0, 140.0, 1.0], dtype=np.float32)
light_pos2 = np.array([0.0, 250.0, -200.0, 1.0], dtype=np.float32)

squash_stretch = [1.0, 1.5, 0.75, 1.0]
fog_color = [0.5, 0.8, 0.5, 1.0]
light_rotation: float = 0.0
density: float = 0.005

max_tex_size: int = 0


def transform_vec3(v: np.ndarray, m: np.ndarray) -> np.ndarray:
    """Like m3dTransformVector3: 4x4 column-major mat times 4-vec, drop w."""
    out = np.zeros(3, dtype=np.float32)
    for r in range(3):
        out[r] = m[r] * v[0] + m[r + 4] * v[1] + m[r + 8] * v[2] + m[r + 12] * v[3]
    return out


def create_pow_map(r: float, g: float, b: float) -> None:
    tex_size = min(max_tex_size, 512)
    texels = np.zeros(tex_size * 4, dtype=np.float32)
    for x in range(tex_size):
        # Range trick: incoming N.H scaled by 8 and biased by -7 so we
        # only sample the upper 1/8 of the curve where it varies.
        t = (float(x) / float(tex_size - 1)) * 0.125 + 0.875
        v = pow(t, 128.0)
        texels[x * 4 + 0] = r * v
        texels[x * 4 + 1] = g * v
        texels[x * 4 + 2] = b * v
        texels[x * 4 + 3] = 1.0
    texels[0] = texels[1] = texels[2] = 0.0
    GL.glTexImage1D(GL.GL_TEXTURE_1D, 0, GL.GL_RGBA16,
                    tex_size, 0, GL.GL_RGBA, GL.GL_FLOAT, texels)


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


SPHERE_BIG = _primitives.build_sphere(25.0, 50, 50)
SPHERE_SMALL = _primitives.build_sphere(25.0, 32, 32)
CONE = _primitives.build_cone(25.0, 50.0, 50)
TORUS = _primitives.build_torus(16.0, 8.0, 50, 50)


def prepare_shader(shader_num: int) -> None:
    fname = os.path.join(PWD, "shaders", f"{shader_names[shader_num]}.vs")
    with open(fname) as f:
        vs_src = f.read()
    v_shader[shader_num] = shaders_mod.compileShader(vs_src, GL.GL_VERTEX_SHADER)
    prog_obj[shader_num] = GL.glCreateProgram()
    GL.glAttachShader(prog_obj[shader_num], v_shader[shader_num])
    GL.glLinkProgram(prog_obj[shader_num])
    if not GL.glGetProgramiv(prog_obj[shader_num], GL.GL_LINK_STATUS):
        info = GL.glGetProgramInfoLog(prog_obj[shader_num])
        sys.stderr.write(f"Program {shader_num} link error: {info}\n")
        sys.exit(1)


def draw_models() -> None:
    # Transform light positions to eye space
    GL.glPushMatrix()
    GL.glRotatef(light_rotation, 0.0, 1.0, 0.0)
    mv = np.array(GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX), dtype=np.float32).flatten()
    light_pos_eye0 = transform_vec3(light_pos0, mv)
    light_pos_eye1 = light_pos_eye2 = np.zeros(3, dtype=np.float32)
    if which_shader == THREELIGHTS:
        light_pos_eye1 = transform_vec3(light_pos1, mv)
        light_pos_eye2 = transform_vec3(light_pos2, mv)
    GL.glPopMatrix()

    p = prog_obj[which_shader]
    loc = GL.glGetUniformLocation(p, "lightPos[0]")
    if loc != -1:
        GL.glUniform3fv(loc, 1, light_pos_eye0)
    loc = GL.glGetUniformLocation(p, "lightPos[1]")
    if loc != -1:
        GL.glUniform3fv(loc, 1, light_pos_eye1)
    loc = GL.glGetUniformLocation(p, "lightPos[2]")
    if loc != -1:
        GL.glUniform3fv(loc, 1, light_pos_eye2)
    loc = GL.glGetUniformLocation(p, "squashStretch")
    if loc != -1:
        GL.glUniform3fv(loc, 1, np.array(squash_stretch[:3], dtype=np.float32))
    loc = GL.glGetUniformLocation(p, "density")
    if loc != -1:
        GL.glUniform1f(loc, density)

    GL.glColor3f(0.0, 0.0, 0.90)
    GL.glNormal3f(0.0, 1.0, 0.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex3f(-100.0, -25.0, -100.0)
    GL.glVertex3f(-100.0, -25.0, 100.0)
    GL.glVertex3f(100.0, -25.0, 100.0)
    GL.glVertex3f(100.0, -25.0, -100.0)
    GL.glEnd()

    GL.glColor3f(1.0, 0.0, 0.0); draw_solid_cube(48.0)

    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glTranslatef(-60.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE_BIG)
    GL.glPopMatrix()

    GL.glColor3f(1.0, 0.0, 1.0)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, 60.0)
    _primitives.draw_mesh(TORUS)
    GL.glPopMatrix()

    if which_shader == STRETCH:
        rotated = [squash_stretch[0], squash_stretch[2], squash_stretch[1]]
        loc = GL.glGetUniformLocation(p, "squashStretch")
        if loc != -1:
            GL.glUniform3fv(loc, 1, np.array(rotated, dtype=np.float32))

    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glTranslatef(60.0, 0.0, -24.0)
    _primitives.draw_mesh(CONE, flat=True)
    GL.glPopMatrix()

    # C++ used glutSolidTeapot here; we substitute another sphere so
    # the scene still has a sixth object exercising the shader.
    GL.glColor3f(0.0, 1.0, 1.0)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -60.0)
    _primitives.draw_mesh(SPHERE_SMALL)
    GL.glPopMatrix()


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

    if which_shader in (FOGCOORD, FOG):
        GL.glClearColor(*fog_color)
        GL.glFogf(GL.GL_FOG_DENSITY, density)
    else:
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_models()


def select_shader(n: int) -> None:
    global which_shader
    which_shader = n
    GL.glUseProgram(prog_obj[which_shader])

    if which_shader == SEPSPEC:
        GL.glEnable(GL.GL_COLOR_SUM)
    else:
        GL.glDisable(GL.GL_COLOR_SUM)

    if which_shader == FOGCOORD:
        GL.glEnable(GL.GL_FOG)
    else:
        GL.glDisable(GL.GL_FOG)

    if which_shader == PTSIZE:
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_POINT)
        GL.glEnable(GL.GL_VERTEX_PROGRAM_POINT_SIZE)
        GL.glEnable(GL.GL_POINT_SMOOTH)
        GL.glEnable(GL.GL_BLEND)
    else:
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
        GL.glDisable(GL.GL_VERTEX_PROGRAM_POINT_SIZE)
        GL.glDisable(GL.GL_POINT_SMOOTH)
        GL.glDisable(GL.GL_BLEND)

    for unit in (GL.GL_TEXTURE3, GL.GL_TEXTURE2, GL.GL_TEXTURE1, GL.GL_TEXTURE0):
        GL.glActiveTexture(unit)
        GL.glDisable(GL.GL_TEXTURE_1D)

    if which_shader in (TEXSPEC, STRETCH):
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_1D)
    elif which_shader == THREELIGHTS:
        GL.glActiveTexture(GL.GL_TEXTURE3); GL.glEnable(GL.GL_TEXTURE_1D)
        GL.glActiveTexture(GL.GL_TEXTURE2); GL.glEnable(GL.GL_TEXTURE_1D)
        GL.glActiveTexture(GL.GL_TEXTURE1); GL.glEnable(GL.GL_TEXTURE_1D)
        GL.glActiveTexture(GL.GL_TEXTURE0)


def _nudge_light(d: float) -> None:
    global light_rotation
    light_rotation += d


def _nudge_cam(axis: int, d: float) -> None:
    camera_pos[axis] += d


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column; hold the key for continuous
    # motion. Shader-specific parameters (fog density, squash/stretch) are
    # shown only for the shaders that use them.
    global density
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Shader", True):
        for i, name in enumerate(shader_names):
            _common.menu_action(name, "", lambda i=i: select_shader(i),
                                selected=(which_shader == i))
        if which_shader in (FOGCOORD, FOG):
            imgui.separator()
            if imgui.begin_menu("Fog density", True):
                _, density = imgui.slider_float("##fog", density, 0.0, 0.05)
                imgui.end_menu()
        elif which_shader == STRETCH:
            imgui.separator()
            if imgui.begin_menu("Squash / stretch", True):
                _, squash_stretch[0] = imgui.slider_float(
                    "X", squash_stretch[0], 0.0, 3.0)
                _, squash_stretch[1] = imgui.slider_float(
                    "Y", squash_stretch[1], 0.0, 3.0)
                _, squash_stretch[2] = imgui.slider_float(
                    "Z", squash_stretch[2], 0.0, 3.0)
                imgui.end_menu()
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Light -", "Left", lambda: _nudge_light(-5.0))
        _common.menu_action("Light +", "Right", lambda: _nudge_light(5.0))
        imgui.separator()
        _common.menu_action("Camera +X", "X", lambda: _nudge_cam(0, 5.0))
        _common.menu_action("Camera -X", "Shift+X", lambda: _nudge_cam(0, -5.0))
        _common.menu_action("Camera +Y", "Up", lambda: _nudge_cam(1, 5.0))
        _common.menu_action("Camera -Y", "Down", lambda: _nudge_cam(1, -5.0))
        _common.menu_action("Camera +Z", "Z", lambda: _nudge_cam(2, 5.0))
        _common.menu_action("Camera -Z", "Shift+Z", lambda: _nudge_cam(2, -5.0))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def setup_rc() -> None:
    global max_tex_size

    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glFogfv(GL.GL_FOG_COLOR, fog_color)
    GL.glFogi(GL.GL_FOG_MODE, GL.GL_EXP2)
    GL.glFogi(GL.GL_FOG_COORD_SRC, GL.GL_FOG_COORD)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

    max_tex_size = GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE)

    # 1D pow-maps for specular: red, green, blue, white on units 1,2,3,0.
    for unit, color in [
        (GL.GL_TEXTURE3, (0.25, 0.25, 1.0)),
        (GL.GL_TEXTURE2, (0.25, 1.0, 0.25)),
        (GL.GL_TEXTURE1, (1.0, 0.25, 0.25)),
        (GL.GL_TEXTURE0, (1.0, 1.0, 1.0)),
    ]:
        GL.glActiveTexture(unit)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_ADD)
        GL.glBindTexture(GL.GL_TEXTURE_1D, unit - GL.GL_TEXTURE0)
        GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        create_pow_map(*color)

    for i in range(TOTAL_SHADERS):
        prepare_shader(i)
    select_shader(SIMPLE)


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    # Shader selection moved to the imgui combo; the fog-density and
    # squash/stretch parameters moved to imgui sliders. The arrow and
    # X/Y/Z keys are now pure navigation: LEFT/RIGHT rotate the lights,
    # UP/DOWN raise/lower the camera, X/Y/Z move the camera (shift = -).
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
        return
    if key == glfw.KEY_LEFT:
        _nudge_light(-5.0)
    elif key == glfw.KEY_RIGHT:
        _nudge_light(5.0)
    elif key == glfw.KEY_UP:
        _nudge_cam(1, 5.0)
    elif key == glfw.KEY_DOWN:
        _nudge_cam(1, -5.0)
    elif key == glfw.KEY_X:
        _nudge_cam(0, -5.0 if (mods & glfw.MOD_SHIFT) else 5.0)
    elif key == glfw.KEY_Y:
        _nudge_cam(1, -5.0 if (mods & glfw.MOD_SHIFT) else 5.0)
    elif key == glfw.KEY_Z:
        _nudge_cam(2, -5.0 if (mods & glfw.MOD_SHIFT) else 5.0)


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(window_width, window_height,
                                "Vertex Shaders Demo", None, None)
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
