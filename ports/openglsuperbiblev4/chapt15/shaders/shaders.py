# shaders.py
# First GLSL shader demo in the book. A "hello world" vertex shader
# that converts NDC into a secondary color, plus a fragment shader
# that mixes primary and secondary 50/50 and multiplies by a flicker
# factor uniform.
#
# C++ used a right-click GLUT menu and imgui_impl_glut UI. This port
# uses key bindings: V toggles vertex shader, F toggles fragment
# shader, B toggles blink/flicker.
#
# OpenGL SuperBible, Chapter 15
# Python port of shaders.cpp by Benjamin Lipchak

import math
import os
import random
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


PWD = os.path.dirname(os.path.abspath(__file__))
window_width: int = 1024
window_height: int = 768

use_vertex_shader: bool = True
use_fragment_shader: bool = True
do_blink: bool = False

flicker_factor: float = 1.0
flicker_location: int = -1
prog_obj: int = 0
v_shader: int = 0
f_shader: int = 0

camera_pos = [100.0, 150.0, 200.0, 1.0]
camera_zoom: float = 0.6


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


def draw_models() -> None:
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

    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glTranslatef(60.0, 0.0, -24.0)
    draw_solid_cone(25.0, 50.0, 50)
    GL.glPopMatrix()

    GL.glColor3f(1.0, 0.0, 1.0)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, 60.0)
    draw_torus(16.0, 8.0, 50, 50)
    GL.glPopMatrix()


def link_program(first_time: bool) -> None:
    global flicker_location
    GL.glLinkProgram(prog_obj)
    if not GL.glGetProgramiv(prog_obj, GL.GL_LINK_STATUS):
        info = GL.glGetProgramInfoLog(prog_obj)
        sys.stderr.write(f"Program link error: {info}\n")
        sys.exit(1)
    if first_time:
        GL.glUseProgram(prog_obj)
    flicker_location = GL.glGetUniformLocation(prog_obj, "flickerFactor")
    if flicker_location != -1:
        GL.glUniform1f(flicker_location, 1.0)


def render_scene() -> None:
    global flicker_factor

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

    if do_blink and flicker_location != -1:
        flicker_factor += (random.random() - 0.5) * 0.1
        flicker_factor = max(0.0, min(1.0, flicker_factor))
        GL.glUniform1f(flicker_location, flicker_factor)

    draw_models()


def setup_rc() -> None:
    global v_shader, f_shader, prog_obj

    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glSecondaryColor3f(1.0, 1.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)

    with open(os.path.join(PWD, "shaders", "shaders.vs")) as f:
        vs_src = f.read()
    with open(os.path.join(PWD, "shaders", "shaders.fs")) as f:
        fs_src = f.read()

    v_shader = shaders_mod.compileShader(vs_src, GL.GL_VERTEX_SHADER)
    f_shader = shaders_mod.compileShader(fs_src, GL.GL_FRAGMENT_SHADER)
    prog_obj = GL.glCreateProgram()
    GL.glAttachShader(prog_obj, v_shader)
    GL.glAttachShader(prog_obj, f_shader)
    link_program(True)


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    global use_vertex_shader, use_fragment_shader, do_blink
    if action != glfw.PRESS:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_V:
        use_vertex_shader = not use_vertex_shader
        if use_vertex_shader:
            GL.glAttachShader(prog_obj, v_shader)
        else:
            GL.glDetachShader(prog_obj, v_shader)
        link_program(False)
    elif key == glfw.KEY_F:
        use_fragment_shader = not use_fragment_shader
        if use_fragment_shader:
            GL.glAttachShader(prog_obj, f_shader)
        else:
            GL.glDetachShader(prog_obj, f_shader)
        link_program(False)
    elif key == glfw.KEY_B:
        do_blink = not do_blink
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
                                "Hello World GLSL Shaders", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

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
