# bumpmap.py
# Tangent-space bump mapping. Tangent, binormal, and normal are
# emitted per-vertex as multi-texcoord1/2/3 attributes (computed
# analytically for box/cylinder/torus, since these shapes have
# closed-form tangent bases). The fragment shader reads a normal
# from the bumpmap texture (encoded as RGB = (n+1)/2) and uses the
# TBN basis to bring the perturbed normal into eye space.
#
# Keys: 1/2/3 select shape (box/cylinder/torus); B/M switch between
# bumpmap and showbump shaders; R/P pick rivets/pyramids bumpmap;
# left/right rotate light; X/Y/Z + shift to pan; Esc to quit.
#
# OpenGL SuperBible, Chapter 17
# Python port of bumpmap.cpp by Benjamin Lipchak

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
window_width: int = 512
window_height: int = 512

BUMPMAP, SHOWBUMP = 0, 1
TOTAL_SHADER_SETS = 2
shader_names = ["bumpmap", "showbump"]
BOX, CYLINDER, TORUS = 0, 1, 2
shape_names = ["box", "cylinder", "torus"]
RIVETS, PYRAMIDS = 0, 1
bumpmap_names = ["rivets", "pyramids"]

f_shader = [0] * TOTAL_SHADER_SETS
v_shader = [0] * TOTAL_SHADER_SETS
prog_obj = [0] * TOTAL_SHADER_SETS
which_shader: int = BUMPMAP
which_shape: int = BOX
which_bumpmap: int = RIVETS

camera_pos = [0.0, 125.0, -200.0, 1.0]
light_rotation: float = 90.0
light_pos0 = np.zeros(3, dtype=np.float32)
max_tex_size: int = 0


def update_light() -> None:
    a = -light_rotation * math.pi / 180.0
    light_pos0[0] = 300.0 * math.cos(a)
    light_pos0[1] = 0.0
    light_pos0[2] = 300.0 * math.sin(a)


def create_rivet_map() -> None:
    tex_size = min(max_tex_size, 128)
    texels = np.zeros(tex_size * tex_size * 4, dtype=np.float32)
    half = (tex_size - 1) * 0.5
    for v in range(tex_size):
        y = (v - half) / half
        for u in range(tex_size):
            x = (u - half) / half
            r = x * x + y * y
            idx = (v * tex_size + u) * 4
            if r <= 0.64:
                nx, ny = x * 1.25, y * 1.25
                nz = math.sqrt(0.64 - r) * 1.25
                s = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
                texels[idx] = nx * s * 0.5 + 0.5
                texels[idx + 1] = ny * s * 0.5 + 0.5
                texels[idx + 2] = nz * s * 0.5 + 0.5
            else:
                texels[idx + 2] = 1.0
            texels[idx + 3] = 1.0
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA16,
                    tex_size, tex_size, 0, GL.GL_RGBA, GL.GL_FLOAT, texels)


def create_pyramid_map() -> None:
    tex_size = min(max_tex_size, 128)
    texels = np.zeros(tex_size * tex_size * 4, dtype=np.float32)
    half = (tex_size - 1) * 0.5
    for v in range(tex_size):
        y = (v - half) / half
        for u in range(tex_size):
            x = (u - half) / half
            idx = (v * tex_size + u) * 4
            if (abs(x) + abs(y)) <= 0.8:
                nx = 0.75 if x >= 0 else -0.75
                ny = 0.75 if y >= 0 else -0.75
                nz = 1.0
                s = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
                texels[idx] = nx * s * 0.5 + 0.5
                texels[idx + 1] = ny * s * 0.5 + 0.5
                texels[idx + 2] = nz * s * 0.5 + 0.5
            else:
                texels[idx + 2] = 1.0
            texels[idx + 3] = 1.0
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA16,
                    tex_size, tex_size, 0, GL.GL_RGBA, GL.GL_FLOAT, texels)


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


def draw_cylinder(radius: float, height: float, slices: int,
                  x_tex_scale: float, y_tex_scale: float) -> None:
    inc = (2.0 * math.pi) / slices
    GL.glBegin(GL.GL_QUAD_STRIP)
    for i in range(slices + 1):
        a = inc * i
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, x_tex_scale * i / slices, 0.0)
        GL.glMultiTexCoord3f(GL.GL_TEXTURE1, math.cos(a + math.pi * 0.5), 0.0,
                             math.sin(a + math.pi * 0.5))
        GL.glMultiTexCoord3f(GL.GL_TEXTURE2, 0.0, 1.0, 0.0)
        GL.glMultiTexCoord3f(GL.GL_TEXTURE3, math.cos(a), 0.0, math.sin(a))
        GL.glVertex3f(radius * math.cos(a), -height * 0.5, radius * math.sin(a))
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,
                             x_tex_scale * i / slices, y_tex_scale)
        GL.glVertex3f(radius * math.cos(a), height * 0.5, radius * math.sin(a))
    GL.glEnd()

    # Top cap
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE1, 1.0, 0.0, 0.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE2, 0.0, 0.0, 1.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE3, 0.0, 1.0, 0.0)
    GL.glVertex3f(0.0, height * 0.5, 0.0)
    for i in range(slices + 1):
        a = inc * i
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,
                             x_tex_scale * math.cos(a) * 0.159155,
                             x_tex_scale * math.sin(a) * 0.159155)
        GL.glVertex3f(radius * math.cos(-a), height * 0.5, radius * math.sin(-a))
    GL.glEnd()

    # Bottom cap
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE1, -1.0, 0.0, 0.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE2, 0.0, 0.0, -1.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE3, 0.0, -1.0, 0.0)
    GL.glVertex3f(0.0, -height * 0.5, 0.0)
    for i in range(slices + 1):
        a = inc * i
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,
                             x_tex_scale * math.cos(a) * 0.159155,
                             x_tex_scale * math.sin(a) * 0.159155)
        GL.glVertex3f(radius * math.cos(a), -height * 0.5, radius * math.sin(a))
    GL.glEnd()


def draw_torus(inner_radius: float, ring_radius: float, rings: int,
               slices: int, x_tex_scale: float, y_tex_scale: float) -> None:
    s_inc = (2.0 * math.pi) / slices
    r_inc = (2.0 * math.pi) / rings
    for i in range(rings + 1):
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            sj = s_inc * j
            cs = math.cos(sj); ss = math.sin(sj)
            for offset in (1, 0):
                ri = r_inc * (i + offset) if offset else r_inc * i
                cr = math.cos(ri); sr = math.sin(ri)
                u_idx = (i + offset) if offset else i
                GL.glMultiTexCoord2f(
                    GL.GL_TEXTURE0,
                    x_tex_scale * u_idx / rings,
                    y_tex_scale * j / slices,
                )
                GL.glMultiTexCoord3f(
                    GL.GL_TEXTURE1,
                    math.cos(ri + math.pi * 0.5), 0.0,
                    math.sin(ri + math.pi * 0.5),
                )
                GL.glMultiTexCoord3f(
                    GL.GL_TEXTURE2, 0.0,
                    math.sin(sj + math.pi * 0.5), 0.0,
                )
                GL.glMultiTexCoord3f(GL.GL_TEXTURE3, cr, ss, sr)
                rr = inner_radius + ring_radius + ring_radius * cs
                GL.glVertex3f(rr * cr, ring_radius * ss, rr * sr)
        GL.glEnd()


def draw_box(size: float, tex_scale: float) -> None:
    s = size * 0.5
    faces = [
        ((1, 0, 0), (0, 1, 0), (0, 0, -1),
         [(-s, -s, -s), (-s, s, -s), (s, s, -s), (s, -s, -s)]),
        ((-1, 0, 0), (0, 1, 0), (0, 0, 1),
         [(s, -s, s), (s, s, s), (-s, s, s), (-s, -s, s)]),
        ((0, 0, 1), (0, 1, 0), (1, 0, 0),
         [(s, -s, -s), (s, s, -s), (s, s, s), (s, -s, s)]),
        ((0, 0, -1), (0, 1, 0), (-1, 0, 0),
         [(-s, -s, s), (-s, s, s), (-s, s, -s), (-s, -s, -s)]),
        ((1, 0, 0), (0, 0, 1), (0, 1, 0),
         [(-s, s, -s), (-s, s, s), (s, s, s), (s, s, -s)]),
        ((1, 0, 0), (0, 0, -1), (0, -1, 0),
         [(-s, -s, s), (-s, -s, -s), (s, -s, -s), (s, -s, s)]),
    ]
    GL.glBegin(GL.GL_QUADS)
    uvs = [(0.0, 0.0), (0.0, tex_scale), (tex_scale, tex_scale), (tex_scale, 0.0)]
    for (tx, ty, tz), (bx, by, bz), (nx, ny, nz), verts in faces:
        for k, vert in enumerate(verts):
            u, v = uvs[k]
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0, u, v)
            GL.glMultiTexCoord3f(GL.GL_TEXTURE1, tx, ty, tz)
            GL.glMultiTexCoord3f(GL.GL_TEXTURE2, bx, by, bz)
            GL.glMultiTexCoord3f(GL.GL_TEXTURE3, nx, ny, nz)
            GL.glVertex3f(*vert)
    GL.glEnd()


def draw_models() -> None:
    p = prog_obj[which_shader]
    loc = GL.glGetUniformLocation(p, "sampler0")
    if loc != -1:
        GL.glUniform1i(loc, 0)
    loc = GL.glGetUniformLocation(p, "lightPos0")
    if loc != -1:
        GL.glUniform3fv(loc, 1, light_pos0)

    GL.glColor3f(0.8, 0.5, 0.3)
    if which_shape == CYLINDER:
        draw_cylinder(25.0, 70.0, 25, 20.0, 10.0)
    elif which_shape == TORUS:
        draw_torus(20.0, 15.0, 50, 25, 40.0, 12.0)
    else:
        draw_box(70.0, 10.0)


def render_scene() -> None:
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, 1.0, 1.0, 1000.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    GL.glViewport(0, 0, window_width, window_height)
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_models()


def setup_rc() -> None:
    global max_tex_size
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_CULL_FACE)

    max_tex_size = GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                       GL.GL_LINEAR_MIPMAP_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
    create_rivet_map()
    GL.glBindTexture(GL.GL_TEXTURE_2D, 1)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                       GL.GL_LINEAR_MIPMAP_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
    create_pyramid_map()
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    update_light()
    for i in range(TOTAL_SHADER_SETS):
        prepare_shader(i)
    GL.glUseProgram(prog_obj[which_shader])


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    global which_shape, which_shader, which_bumpmap, light_rotation
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True); return
    if key == glfw.KEY_1:
        which_shape = BOX; print("shape: box"); return
    if key == glfw.KEY_2:
        which_shape = CYLINDER; print("shape: cylinder"); return
    if key == glfw.KEY_3:
        which_shape = TORUS; print("shape: torus"); return
    if key == glfw.KEY_B:
        which_shader = BUMPMAP; GL.glUseProgram(prog_obj[which_shader])
        print("shader: bumpmap"); return
    if key == glfw.KEY_M:
        which_shader = SHOWBUMP; GL.glUseProgram(prog_obj[which_shader])
        print("shader: showbump"); return
    if key == glfw.KEY_R:
        which_bumpmap = RIVETS; GL.glBindTexture(GL.GL_TEXTURE_2D, which_bumpmap)
        print("bumpmap: rivets"); return
    if key == glfw.KEY_P:
        which_bumpmap = PYRAMIDS; GL.glBindTexture(GL.GL_TEXTURE_2D, which_bumpmap)
        print("bumpmap: pyramids"); return
    if key == glfw.KEY_LEFT:
        light_rotation -= 5.0; update_light()
    elif key == glfw.KEY_RIGHT:
        light_rotation += 5.0; update_light()
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
    
    window_width, window_height = _common.resolve_default_window_size()
    window = glfw.create_window(window_width, window_height,
                                "Bump Mapping Demo", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    impl = _common.init_imgui(window)
    win_state = _common.WindowState()

    print("Bump Mapping Demo")
    print("  1/2/3: shape (box/cylinder/torus)")
    print("  B/M:   shader (bumpmap/showbump)")
    print("  R/P:   bumpmap (rivets/pyramids)")
    print("  Left/Right: rotate light  X/Y/Z + shift: pan camera")

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
