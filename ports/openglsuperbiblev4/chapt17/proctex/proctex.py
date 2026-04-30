# proctex.py
# Procedural texture demo: a single sphere drawn three different
# ways by the fragment shader. checkerboard divides surface UVs into
# squares; beachball uses lat/long stripes; toyball does the
# half-spheres + star pattern from the SIGGRAPH RenderMan classic.
#
# Keys: 1..3 select shader; arrows rotate light / change tess; X/Y/Z
# move camera (shift = -); Esc to quit.
#
# OpenGL SuperBible, Chapter 17
# Python port of proctex.cpp by Benjamin Lipchak

import math
import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU



PWD = os.path.dirname(os.path.abspath(__file__))
window_width: int = 1024
window_height: int = 768

CHECKERBOARD, BEACHBALL, TOYBALL = 0, 1, 2
TOTAL_SHADER_SETS = 3
shader_names = ["checkerboard", "beachball", "toyball"]
v_shader = [0] * TOTAL_SHADER_SETS
f_shader = [0] * TOTAL_SHADER_SETS
prog_obj = [0] * TOTAL_SHADER_SETS
which_shader: int = CHECKERBOARD

camera_pos = [50.0, 50.0, 150.0, 1.0]
camera_zoom: float = 0.4
light_pos = np.array([140.0, 250.0, 140.0, 1.0], dtype=np.float32)
light_rotation: float = 0.0
tess: int = 75


def transform_vec3(v: np.ndarray, m: np.ndarray) -> np.ndarray:
    out = np.zeros(3, dtype=np.float32)
    for r in range(3):
        out[r] = m[r] * v[0] + m[r + 4] * v[1] + m[r + 8] * v[2] + m[r + 12] * v[3]
    return out


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
    light_pos_eye = transform_vec3(light_pos, mv)
    GL.glPopMatrix()
    p = prog_obj[which_shader]
    loc = GL.glGetUniformLocation(p, "lightPos")
    if loc != -1:
        GL.glUniform3fv(loc, 1, light_pos_eye)
    draw_solid_sphere(50.0, tess, tess)


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
    print(f"Shader: {shader_names[n]}")
    GL.glUseProgram(prog_obj[which_shader])


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    for i in range(TOTAL_SHADER_SETS):
        prepare_shader(i)
    select_shader(CHECKERBOARD)


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    global light_rotation, tess
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True); return
    if key == glfw.KEY_1:
        select_shader(CHECKERBOARD); return
    if key == glfw.KEY_2:
        select_shader(BEACHBALL); return
    if key == glfw.KEY_3:
        select_shader(TOYBALL); return
    if key == glfw.KEY_LEFT:
        light_rotation -= 5.0
    elif key == glfw.KEY_RIGHT:
        light_rotation += 5.0
    elif key == glfw.KEY_UP:
        tess += 5
    elif key == glfw.KEY_DOWN:
        tess = max(5, tess - 5)
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
                                "Procedural Texture Mapping Demo", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    print("Procedural Texture Mapping Demo")
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
