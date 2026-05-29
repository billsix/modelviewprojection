# lighting.py
# Vertex+fragment shader pairs that implement progressively more
# elaborate lighting models in GLSL: simple, diffuse, specular,
# 3lights. Each shader set lives as shaders/<name>.{vs,fs}.
#
# Key bindings: 1..4 select shader; left/right rotate lights; up/down
# +y/-y; X/Y/Z + shift to pan; Esc to quit. Teapot replaced with a
# sphere — no PyOpenGL equivalent.
#
# OpenGL SuperBible, Chapter 17
# Python port of lighting.cpp by Benjamin Lipchak

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

SIMPLE, DIFFUSE, SPECULAR, THREELIGHTS = 0, 1, 2, 3
TOTAL_SHADER_SETS = 4
shader_names = ["simple", "diffuse", "specular", "3lights"]

f_shader = [0] * TOTAL_SHADER_SETS
v_shader = [0] * TOTAL_SHADER_SETS
prog_obj = [0] * TOTAL_SHADER_SETS
which_shader: int = SIMPLE

camera_pos = [100.0, 75.0, 150.0, 1.0]
camera_zoom: float = 0.4
light_pos0 = np.array([140.0, 250.0, 140.0, 1.0], dtype=np.float32)
light_pos1 = np.array([-140.0, 250.0, 140.0, 1.0], dtype=np.float32)
light_pos2 = np.array([0.0, 250.0, -200.0, 1.0], dtype=np.float32)
light_rotation: float = 0.0


def transform_vec3(v: np.ndarray, m: np.ndarray) -> np.ndarray:
    out = np.zeros(3, dtype=np.float32)
    for r in range(3):
        out[r] = m[r] * v[0] + m[r + 4] * v[1] + m[r + 8] * v[2] + m[r + 12] * v[3]
    return out


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


def prepare_shader(n: int) -> None:
    name = shader_names[n]
    with open(os.path.join(PWD, "shaders", f"{name}.vs")) as f:
        vs_src = f.read()
    with open(os.path.join(PWD, "shaders", f"{name}.fs")) as f:
        fs_src = f.read()
    v_shader[n] = shaders_mod.compileShader(vs_src, GL.GL_VERTEX_SHADER)
    f_shader[n] = shaders_mod.compileShader(fs_src, GL.GL_FRAGMENT_SHADER)
    prog_obj[n] = GL.glCreateProgram()
    GL.glAttachShader(prog_obj[n], v_shader[n])
    GL.glAttachShader(prog_obj[n], f_shader[n])
    GL.glLinkProgram(prog_obj[n])
    if not GL.glGetProgramiv(prog_obj[n], GL.GL_LINK_STATUS):
        info = GL.glGetProgramInfoLog(prog_obj[n])
        sys.stderr.write(f"Program {n} link error: {info}\n")
        sys.exit(1)


def draw_models() -> None:
    GL.glPushMatrix()
    GL.glRotatef(light_rotation, 0.0, 1.0, 0.0)
    mv = np.array(GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX),
                  dtype=np.float32).flatten()
    le0 = transform_vec3(light_pos0, mv)
    le1 = le2 = np.zeros(3, dtype=np.float32)
    if which_shader == THREELIGHTS:
        le1 = transform_vec3(light_pos1, mv)
        le2 = transform_vec3(light_pos2, mv)
    GL.glPopMatrix()

    p = prog_obj[which_shader]
    loc = GL.glGetUniformLocation(p, "sampler0")
    if loc != -1:
        GL.glUniform1i(loc, 0)
    loc = GL.glGetUniformLocation(p, "lightPos[0]")
    if loc != -1:
        GL.glUniform3fv(loc, 1, le0)
    loc = GL.glGetUniformLocation(p, "lightPos[1]")
    if loc != -1:
        GL.glUniform3fv(loc, 1, le1)
    loc = GL.glGetUniformLocation(p, "lightPos[2]")
    if loc != -1:
        GL.glUniform3fv(loc, 1, le2)

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
    GL.glPushMatrix(); GL.glTranslatef(-60.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE_BIG); GL.glPopMatrix()
    GL.glColor3f(1.0, 0.0, 1.0)
    GL.glPushMatrix(); GL.glTranslatef(0.0, 0.0, 60.0)
    _primitives.draw_mesh(TORUS); GL.glPopMatrix()
    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glPushMatrix(); GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glTranslatef(60.0, 0.0, -24.0)
    _primitives.draw_mesh(CONE, flat=True); GL.glPopMatrix()
    GL.glColor3f(0.0, 1.0, 1.0)
    GL.glPushMatrix(); GL.glTranslatef(0.0, 0.0, -60.0)
    _primitives.draw_mesh(SPHERE_SMALL); GL.glPopMatrix()


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
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_models()


def select_shader(n: int) -> None:
    global which_shader
    which_shader = n
    GL.glUseProgram(prog_obj[which_shader])


def _nudge_light(d: float) -> None:
    global light_rotation
    light_rotation += d


def _nudge_cam(axis: int, d: float) -> None:
    camera_pos[axis] += d


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column (discovery); hold the key for
    # continuous motion.
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
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    for i in range(TOTAL_SHADER_SETS):
        prepare_shader(i)
    select_shader(SIMPLE)


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    # Shader selection is in the imgui panel; these keys are mirrored by the
    # panel's "Controls" buttons (which name each key).
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True); return
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
                                "Lighting Demo", None, None)
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
