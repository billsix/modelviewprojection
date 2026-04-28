# vertexshaders.py
# Vertex shader gallery: 10 different vertex shaders that demonstrate
# the range of fixed-function effects you can replace with GLSL.
# The shaders themselves live in shaders/*.vs and are loaded at startup.
#
# C++ used a right-click GLUT menu to switch shaders. This port uses
# number keys 1..9 and 0 for the 10 entries, listed below in the
# console at startup. Arrow keys rotate the lights (or change fog
# density when a fog shader is active). The C++ glutSolidTeapot is
# replaced with a second sphere — there is no equivalent in plain
# PyOpenGL and the teapot is decorative; the demo is about shaders.
#
# OpenGL SuperBible, Chapter 16
# Python port of vertexshaders.cpp by Benjamin Lipchak

import math
import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU
from imgui_bundle import imgui

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
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


def draw_solid_cone(base: float, height: float, slices: int) -> None:
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, 1.0)
    GL.glVertex3f(0.0, 0.0, height)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        GL.glVertex3f(math.cos(a) * base, math.sin(a) * base, 0.0)
    GL.glEnd()


def draw_torus(major: float, minor: float, n_major: int, n_minor: int) -> None:
    major_step = 2.0 * math.pi / n_major
    minor_step = 2.0 * math.pi / n_minor
    for i in range(n_major):
        a0, a1 = i * major_step, (i + 1) * major_step
        x0, y0 = math.cos(a0), math.sin(a0)
        x1, y1 = math.cos(a1), math.sin(a1)
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        for j in range(n_minor + 1):
            b = j * minor_step
            cb, sb = math.cos(b), math.sin(b)
            r = minor * cb + major
            z = minor * sb
            GL.glNormal3f(x0 * cb, y0 * cb, sb)
            GL.glVertex3f(x0 * r, y0 * r, z)
            GL.glNormal3f(x1 * cb, y1 * cb, sb)
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()


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
    draw_solid_sphere(25.0, 50, 50)
    GL.glPopMatrix()

    GL.glColor3f(1.0, 0.0, 1.0)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, 60.0)
    draw_torus(16.0, 8.0, 50, 50)
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
    draw_solid_cone(25.0, 50.0, 50)
    GL.glPopMatrix()

    # C++ used glutSolidTeapot here; we substitute another sphere so
    # the scene still has a sixth object exercising the shader.
    GL.glColor3f(0.0, 1.0, 1.0)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -60.0)
    draw_solid_sphere(25.0, 32, 32)
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
    print(f"Shader: {shader_names[n]}")
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


# Number-key shader bindings (1..9 => 0..8, 0 => 9)
KEY_TO_SHADER = {
    glfw.KEY_1: SIMPLE, glfw.KEY_2: DIFFUSE, glfw.KEY_3: SPECULAR,
    glfw.KEY_4: SEPSPEC, glfw.KEY_5: TEXSPEC, glfw.KEY_6: THREELIGHTS,
    glfw.KEY_7: FOGCOORD, glfw.KEY_8: FOG, glfw.KEY_9: PTSIZE,
    glfw.KEY_0: STRETCH,
}


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    global density, light_rotation
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
        return
    if key in KEY_TO_SHADER:
        select_shader(KEY_TO_SHADER[key])
        return
    if key == glfw.KEY_LEFT:
        if which_shader in (FOGCOORD, FOG):
            density = max(0.0, density - 0.0005)
        else:
            light_rotation -= 5.0
    elif key == glfw.KEY_RIGHT:
        if which_shader in (FOGCOORD, FOG):
            density += 0.0005
        else:
            light_rotation += 5.0
    elif key == glfw.KEY_UP:
        camera_pos[1] += 5.0
    elif key == glfw.KEY_DOWN:
        camera_pos[1] -= 5.0
    elif key == glfw.KEY_X:
        delta = -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
        if which_shader == STRETCH:
            squash_stretch[0] += delta * 0.002
        else:
            camera_pos[0] += delta
    elif key == glfw.KEY_Y:
        delta = -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
        if which_shader == STRETCH:
            squash_stretch[1] += delta * 0.002
        else:
            camera_pos[1] += delta
    elif key == glfw.KEY_Z:
        delta = -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
        if which_shader == STRETCH:
            squash_stretch[2] += delta * 0.002
        else:
            camera_pos[2] += delta


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    
    window_width, window_height = _common.resolve_default_window_size()
    window = glfw.create_window(window_width, window_height,
                                "Vertex Shaders Demo", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    impl = _common.init_imgui(window)
    win_state = _common.WindowState()

    print("Vertex Shaders Demo")
    print("Press 1..9, 0 to select a shader:")
    for i, name in enumerate(shader_names):
        key = (i + 1) % 10
        print(f"  {key}: {name}")

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
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
