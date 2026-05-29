# fragmentshaders.py
# Fragment-shader gallery: 7 different fragment shaders applied to
# the same lit scene of primitives. Lighting in the vertex shader is
# delegated to fixed function (the program objects only attach an
# .fs); the fragment shader gets the interpolated gl_Color and
# transforms it (heat-sig 1D-LUT, sepia matrix, fog mix, etc.).
#
# C++ used a right-click GLUT menu; this port uses keys 1..7 to pick
# a shader, arrows to rotate lights / adjust fog, X/Y/Z + shift to
# pan camera, Esc to quit. The C++ glutSolidTeapot is replaced with
# a sphere — there's no equivalent in plain PyOpenGL.
#
# OpenGL SuperBible, Chapter 17
# Python port of fragmentshaders.cpp by Benjamin Lipchak

import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU



PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _primitives  # noqa: E402
window_width: int = 1024
window_height: int = 768

SIMPLE, GRAYSCALE, SEPIA, HEATSIG, FOG, GRAYINVERT, COLORINVERT = range(7)
TOTAL_SHADERS = 7
shader_names = [
    "simple", "grayscale", "sepia", "heatsig",
    "fog", "grayinvert", "colorinvert",
]
f_shader = [0] * TOTAL_SHADERS
prog_obj = [0] * TOTAL_SHADERS
which_shader: int = SIMPLE

camera_pos = [100.0, 75.0, 150.0, 1.0]
camera_zoom: float = 0.4
light_pos = [140.0, 250.0, 140.0, 1.0]
ambient_light = [0.2, 0.2, 0.2, 1.0]
diffuse_light = [0.7, 0.7, 0.7, 1.0]
specular_material = [1.0, 1.0, 1.0, 1.0]
fog_color = [0.5, 0.8, 0.5, 1.0]
light_rotation: float = 0.0
density: float = 1.0
max_tex_size: int = 0


def create_heatsig_map() -> None:
    tex_size = min(max_tex_size, 512)
    texels = np.zeros(tex_size * 4, dtype=np.float32)
    for x in range(tex_size):
        p = float(x) / float(tex_size - 1)
        if p < 0.25:
            p *= 4.0
            texels[x * 4 + 2] = p
        elif p < 0.5:
            p = (p - 0.25) * 4.0
            texels[x * 4 + 1] = p
            texels[x * 4 + 2] = 1.0 - p
        elif p < 0.75:
            p = (p - 0.5) * 4.0
            texels[x * 4 + 0] = p
            texels[x * 4 + 1] = 1.0
        else:
            p = (p - 0.75) * 4.0
            texels[x * 4 + 0] = 1.0
            texels[x * 4 + 1] = 1.0 - p
        texels[x * 4 + 3] = 1.0
    GL.glTexImage1D(GL.GL_TEXTURE_1D, 0, GL.GL_RGBA8,
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


def prepare_shader(n: int) -> None:
    fname = os.path.join(PWD, "shaders", f"{shader_names[n]}.fs")
    with open(fname) as f:
        fs_src = f.read()
    f_shader[n] = shaders_mod.compileShader(fs_src, GL.GL_FRAGMENT_SHADER)
    prog_obj[n] = GL.glCreateProgram()
    GL.glAttachShader(prog_obj[n], f_shader[n])
    GL.glLinkProgram(prog_obj[n])
    if not GL.glGetProgramiv(prog_obj[n], GL.GL_LINK_STATUS):
        info = GL.glGetProgramInfoLog(prog_obj[n])
        sys.stderr.write(f"Program {n} link error: {info}\n")
        sys.exit(1)


def draw_models() -> None:
    GL.glPushMatrix()
    GL.glRotatef(light_rotation, 0.0, 1.0, 0.0)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glPopMatrix()

    p = prog_obj[which_shader]
    loc = GL.glGetUniformLocation(p, "sampler0")
    if loc != -1:
        GL.glUniform1i(loc, 0)
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

    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glTranslatef(60.0, 0.0, -24.0)
    _primitives.draw_mesh(CONE, flat=True)
    GL.glPopMatrix()

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

    if which_shader == FOG:
        GL.glClearColor(*fog_color)
    elif which_shader in (GRAYINVERT, COLORINVERT):
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    else:
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_models()


def select_shader(n: int) -> None:
    global which_shader
    which_shader = n
    print(f"Shader: {shader_names[n]}")
    GL.glUseProgram(prog_obj[which_shader])


def setup_rc() -> None:
    global max_tex_size
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glEnable(GL.GL_NORMALIZE)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
    GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_SPECULAR, specular_material)
    GL.glMaterialf(GL.GL_FRONT_AND_BACK, GL.GL_SHININESS, 128.0)

    max_tex_size = GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glBindTexture(GL.GL_TEXTURE_1D, 0)
    GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
    create_heatsig_map()

    for i in range(TOTAL_SHADERS):
        prepare_shader(i)
    select_shader(SIMPLE)


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


KEY_TO_SHADER = {
    glfw.KEY_1: SIMPLE, glfw.KEY_2: GRAYSCALE, glfw.KEY_3: SEPIA,
    glfw.KEY_4: HEATSIG, glfw.KEY_5: FOG, glfw.KEY_6: GRAYINVERT,
    glfw.KEY_7: COLORINVERT,
}


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    global density, light_rotation
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True); return
    if key in KEY_TO_SHADER:
        select_shader(KEY_TO_SHADER[key]); return
    if key == glfw.KEY_LEFT:
        if which_shader == FOG:
            density = max(0.0, density - 0.1)
        else:
            light_rotation -= 5.0
    elif key == glfw.KEY_RIGHT:
        if which_shader == FOG:
            density += 0.1
        else:
            light_rotation += 5.0
    elif key == glfw.KEY_UP:
        camera_pos[1] += 5.0
    elif key == glfw.KEY_DOWN:
        camera_pos[1] -= 5.0
    elif key == glfw.KEY_X:
        camera_pos[0] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Y:
        camera_pos[1] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Z:
        camera_pos[2] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(window_width, window_height,
                                "Fragment Shaders Demo", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    print("Fragment Shaders Demo")
    print("Press 1..7 to select a shader:")
    for i, n in enumerate(shader_names):
        print(f"  {i + 1}: {n}")

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
