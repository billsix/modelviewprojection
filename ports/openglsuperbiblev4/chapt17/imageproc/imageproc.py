# imageproc.py
# Image-processing demo: render the lit primitive scene to a texture,
# then redraw a fullscreen quad through a 3x3-tap convolution
# fragment shader. Selecting "blur" twice runs two passes.
#
# Keys: 1..8 select shader; P followed by 1..5 sets number of passes;
# left/right rotate light; X/Y/Z + shift to pan; Esc to quit.
#
# OpenGL SuperBible, Chapter 17
# Python port of imageproc.cpp by Benjamin Lipchak

import math
import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


PWD = os.path.dirname(os.path.abspath(__file__))
window_width: int = 1024
window_height: int = 512
texture_width: int = 1024
texture_height: int = 512

PASS_THROUGH, BLUR, SHARPEN, DILATION, EROSION, LAPLACIAN, SOBEL, PREWITT = range(8)
TOTAL_SHADERS = 8
shader_names = [
    "passthrough", "blur", "sharpen", "dilation",
    "erosion", "laplacian", "sobel", "prewitt",
]
f_shader = [0] * TOTAL_SHADERS
prog_obj = [0] * TOTAL_SHADERS
which_shader: int = PASS_THROUGH

camera_pos = [100.0, 75.0, 150.0, 1.0]
camera_zoom: float = 0.3
light_pos = [140.0, 250.0, 140.0, 1.0]
ambient_light = [0.2, 0.2, 0.2, 1.0]
diffuse_light = [0.7, 0.7, 0.7, 1.0]
light_rotation: float = 0.0
tex_coord_offsets: np.ndarray = np.zeros(18, dtype=np.float32)
num_passes: int = 2
max_tex_size: int = 0
pending_pass_select: bool = False  # waiting for digit after 'P' is pressed


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
    draw_solid_sphere(25.0, 50, 50); GL.glPopMatrix()
    GL.glColor3f(1.0, 0.0, 1.0)
    GL.glPushMatrix(); GL.glTranslatef(0.0, 0.0, 60.0)
    draw_torus(16.0, 8.0, 50, 50); GL.glPopMatrix()
    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glPushMatrix(); GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glTranslatef(60.0, 0.0, -24.0)
    draw_solid_cone(25.0, 50.0, 50); GL.glPopMatrix()
    GL.glColor3f(0.0, 1.0, 1.0)
    GL.glPushMatrix(); GL.glTranslatef(0.0, 0.0, -60.0)
    draw_solid_sphere(25.0, 32, 32); GL.glPopMatrix()


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

    p = prog_obj[which_shader]
    GL.glUseProgram(p)
    loc = GL.glGetUniformLocation(p, "sampler0")
    if loc != -1:
        GL.glUniform1i(loc, 0)
    loc = GL.glGetUniformLocation(p, "tc_offset")
    if loc != -1:
        GL.glUniform2fv(loc, 9, tex_coord_offsets)

    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glMatrixMode(GL.GL_PROJECTION); GL.glLoadIdentity()
    GL.glMatrixMode(GL.GL_MODELVIEW); GL.glLoadIdentity()

    for _ in range(num_passes):
        GL.glCopyTexImage2D(
            GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8,
            (window_width - texture_width) // 2,
            (window_height - texture_height) // 2,
            texture_width, texture_height, 0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        wx = float(texture_width) / float(window_width)
        wy = float(texture_height) / float(window_height)
        GL.glBegin(GL.GL_QUADS)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0); GL.glVertex2f(-wx, -wy)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 1.0); GL.glVertex2f(-wx, wy)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 1.0); GL.glVertex2f(wx, wy)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 0.0); GL.glVertex2f(wx, -wy)
        GL.glEnd()

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glUseProgram(0)


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

    max_tex_size = GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)

    for i in range(TOTAL_SHADERS):
        prepare_shader(i)


def change_size(w: int, h: int) -> None:
    global window_width, window_height, texture_width, texture_height
    window_width = texture_width = w
    window_height = texture_height = h
    if texture_width > max_tex_size: texture_width = max_tex_size
    if texture_height > max_tex_size: texture_height = max_tex_size

    x_inc = 1.0 / float(texture_width)
    y_inc = 1.0 / float(texture_height)
    for i in range(3):
        for j in range(3):
            tex_coord_offsets[(((i * 3) + j) * 2) + 0] = (-1.0 * x_inc) + (i * x_inc)
            tex_coord_offsets[(((i * 3) + j) * 2) + 1] = (-1.0 * y_inc) + (j * y_inc)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


KEY_TO_SHADER = {
    glfw.KEY_1: PASS_THROUGH, glfw.KEY_2: BLUR, glfw.KEY_3: SHARPEN,
    glfw.KEY_4: DILATION, glfw.KEY_5: EROSION, glfw.KEY_6: LAPLACIAN,
    glfw.KEY_7: SOBEL, glfw.KEY_8: PREWITT,
}


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    global which_shader, num_passes, light_rotation, pending_pass_select
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True); return
    if pending_pass_select and key in (
        glfw.KEY_1, glfw.KEY_2, glfw.KEY_3, glfw.KEY_4, glfw.KEY_5,
    ):
        num_passes = key - glfw.KEY_0
        print(f"passes: {num_passes}")
        pending_pass_select = False
        return
    pending_pass_select = False
    if key == glfw.KEY_P:
        pending_pass_select = True
        print("press 1..5 to set number of passes")
        return
    if key in KEY_TO_SHADER:
        which_shader = KEY_TO_SHADER[key]
        print(f"Shader: {shader_names[which_shader]}")
        return
    if key == glfw.KEY_LEFT:
        light_rotation -= 5.0
    elif key == glfw.KEY_RIGHT:
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
                                "Image Processing Demo", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    print("Image Processing Demo")
    for i, n in enumerate(shader_names):
        print(f"  {i + 1}: {n}")
    print("  P then 1..5: set number of passes")

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
