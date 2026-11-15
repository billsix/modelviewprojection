# bumpmap.py
# Tangent-space bump mapping. Tangent, binormal, and normal are
# emitted per-vertex as multi-texcoord1/2/3 attributes (computed
# analytically for box/cylinder/torus, since these shapes have
# closed-form tangent bases). The fragment shader reads a normal
# from the bumpmap texture (encoded as RGB = (n+1)/2) and uses the
# TBN basis to bring the perturbed normal into eye space.
#
# Shape (box/cylinder/torus), shader (bumpmap/showbump), and bumpmap
# texture (rivets/pyramids) are selected on an imgui panel; left/right
# rotate the light; X/Y/Z + shift to pan; Esc to quit.
#
# OpenGL SuperBible, Chapter 17
# Python port of bumpmap.cpp by Benjamin Lipchak

import dataclasses
import math
import os
import sys
import typing
from typing import Any

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

BUMPMAP: int = 0
SHOWBUMP: int = 1
TOTAL_SHADER_SETS: int = 2
shader_names: list[str] = ["bumpmap", "showbump"]
BOX: int = 0
CYLINDER: int = 1
TORUS: int = 2
shape_names: list[str] = ["box", "cylinder", "torus"]
RIVETS: int = 0
PYRAMIDS: int = 1
bumpmap_names: list[str] = ["rivets", "pyramids"]


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    window: typing.Any = None  # glfw window handle; set in main()
    window_width: int = 512
    window_height: int = 512

    f_shader: list[int] = dataclasses.field(
        default_factory=lambda: [0] * TOTAL_SHADER_SETS
    )
    v_shader: list[int] = dataclasses.field(
        default_factory=lambda: [0] * TOTAL_SHADER_SETS
    )
    prog_obj: list[int] = dataclasses.field(
        default_factory=lambda: [0] * TOTAL_SHADER_SETS
    )
    which_shader: int = BUMPMAP
    which_shape: int = BOX
    which_bumpmap: int = RIVETS

    camera_pos: list[float] = dataclasses.field(
        default_factory=lambda: [0.0, 125.0, -200.0, 1.0]
    )
    light_rotation: float = 90.0
    light_pos0: np.ndarray = dataclasses.field(
        default_factory=lambda: np.zeros(3, dtype=np.float32)
    )
    max_tex_size: int = 0


state: AppState = AppState()


def update_light() -> None:
    a: float = -state.light_rotation * math.pi / 180.0
    state.light_pos0[0] = 300.0 * math.cos(a)
    state.light_pos0[1] = 0.0
    state.light_pos0[2] = 300.0 * math.sin(a)


def create_rivet_map() -> None:
    tex_size: int = min(state.max_tex_size, 128)
    texels: np.ndarray = np.zeros(tex_size * tex_size * 4, dtype=np.float32)
    half: float = (tex_size - 1) * 0.5
    v: int
    for v in range(tex_size):
        y: float = (v - half) / half
        u: int
        for u in range(tex_size):
            x: float = (u - half) / half
            r: float = x * x + y * y
            idx: int = (v * tex_size + u) * 4
            if r <= 0.64:
                nx: float = x * 1.25
                ny: float = y * 1.25
                nz: float = math.sqrt(0.64 - r) * 1.25
                s: float = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
                texels[idx] = nx * s * 0.5 + 0.5
                texels[idx + 1] = ny * s * 0.5 + 0.5
                texels[idx + 2] = nz * s * 0.5 + 0.5
            else:
                texels[idx + 2] = 1.0
            texels[idx + 3] = 1.0
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D,
        0,
        GL.GL_RGBA16,
        tex_size,
        tex_size,
        0,
        GL.GL_RGBA,
        GL.GL_FLOAT,
        texels,
    )


def create_pyramid_map() -> None:
    tex_size: int = min(state.max_tex_size, 128)
    texels: np.ndarray = np.zeros(tex_size * tex_size * 4, dtype=np.float32)
    half: float = (tex_size - 1) * 0.5
    v: int
    for v in range(tex_size):
        y: float = (v - half) / half
        u: int
        for u in range(tex_size):
            x: float = (u - half) / half
            idx: int = (v * tex_size + u) * 4
            if (abs(x) + abs(y)) <= 0.8:
                nx: float = 0.75 if x >= 0 else -0.75
                ny: float = 0.75 if y >= 0 else -0.75
                nz: float = 1.0
                s: float = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
                texels[idx] = nx * s * 0.5 + 0.5
                texels[idx + 1] = ny * s * 0.5 + 0.5
                texels[idx + 2] = nz * s * 0.5 + 0.5
            else:
                texels[idx + 2] = 1.0
            texels[idx + 3] = 1.0
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D,
        0,
        GL.GL_RGBA16,
        tex_size,
        tex_size,
        0,
        GL.GL_RGBA,
        GL.GL_FLOAT,
        texels,
    )


def prepare_shader(n: int) -> None:
    name: str = shader_names[n]
    f: typing.TextIO
    with open(os.path.join(PWD, "shaders", f"{name}.vs")) as f:
        vs_src: str = f.read()
    with open(os.path.join(PWD, "shaders", f"{name}.fs")) as f:
        fs_src: str = f.read()
    state.v_shader[n] = shaders_mod.compileShader(vs_src, GL.GL_VERTEX_SHADER)
    state.f_shader[n] = shaders_mod.compileShader(fs_src, GL.GL_FRAGMENT_SHADER)
    state.prog_obj[n] = GL.glCreateProgram()
    GL.glAttachShader(state.prog_obj[n], state.v_shader[n])
    GL.glAttachShader(state.prog_obj[n], state.f_shader[n])
    GL.glLinkProgram(state.prog_obj[n])
    if not GL.glGetProgramiv(state.prog_obj[n], GL.GL_LINK_STATUS):
        info: bytes = GL.glGetProgramInfoLog(state.prog_obj[n])
        sys.stderr.write(f"Program {n} link error: {info}\n")
        sys.exit(1)


def draw_cylinder(
    radius: float,
    height: float,
    slices: int,
    x_tex_scale: float,
    y_tex_scale: float,
) -> None:
    inc: float = (2.0 * math.pi) / slices
    GL.glBegin(GL.GL_QUAD_STRIP)
    i: int
    for i in range(slices + 1):
        a: float = inc * i
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, x_tex_scale * i / slices, 0.0)
        GL.glMultiTexCoord3f(
            GL.GL_TEXTURE1,
            math.cos(a + math.pi * 0.5),
            0.0,
            math.sin(a + math.pi * 0.5),
        )
        GL.glMultiTexCoord3f(GL.GL_TEXTURE2, 0.0, 1.0, 0.0)
        GL.glMultiTexCoord3f(GL.GL_TEXTURE3, math.cos(a), 0.0, math.sin(a))
        GL.glVertex3f(radius * math.cos(a), -height * 0.5, radius * math.sin(a))
        GL.glMultiTexCoord2f(
            GL.GL_TEXTURE0, x_tex_scale * i / slices, y_tex_scale
        )
        GL.glVertex3f(radius * math.cos(a), height * 0.5, radius * math.sin(a))
    GL.glEnd()

    # Top cap
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE1, 1.0, 0.0, 0.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE2, 0.0, 0.0, 1.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE3, 0.0, 1.0, 0.0)
    GL.glVertex3f(0.0, height * 0.5, 0.0)
    i: int
    for i in range(slices + 1):
        a = inc * i
        GL.glMultiTexCoord2f(
            GL.GL_TEXTURE0,
            x_tex_scale * math.cos(a) * 0.159155,
            x_tex_scale * math.sin(a) * 0.159155,
        )
        GL.glVertex3f(
            radius * math.cos(-a), height * 0.5, radius * math.sin(-a)
        )
    GL.glEnd()

    # Bottom cap
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE1, -1.0, 0.0, 0.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE2, 0.0, 0.0, -1.0)
    GL.glMultiTexCoord3f(GL.GL_TEXTURE3, 0.0, -1.0, 0.0)
    GL.glVertex3f(0.0, -height * 0.5, 0.0)
    i: int
    for i in range(slices + 1):
        a = inc * i
        GL.glMultiTexCoord2f(
            GL.GL_TEXTURE0,
            x_tex_scale * math.cos(a) * 0.159155,
            x_tex_scale * math.sin(a) * 0.159155,
        )
        GL.glVertex3f(radius * math.cos(a), -height * 0.5, radius * math.sin(a))
    GL.glEnd()


def draw_torus(
    inner_radius: float,
    ring_radius: float,
    rings: int,
    slices: int,
    x_tex_scale: float,
    y_tex_scale: float,
) -> None:
    s_inc: float = (2.0 * math.pi) / slices
    r_inc: float = (2.0 * math.pi) / rings
    i: int
    for i in range(rings + 1):
        GL.glBegin(GL.GL_QUAD_STRIP)
        j: int
        for j in range(slices + 1):
            sj: float = s_inc * j
            cs: float = math.cos(sj)
            ss: float = math.sin(sj)
            offset: int
            for offset in (1, 0):
                ri: float = r_inc * (i + offset) if offset else r_inc * i
                cr: float = math.cos(ri)
                sr: float = math.sin(ri)
                u_idx: int = (i + offset) if offset else i
                GL.glMultiTexCoord2f(
                    GL.GL_TEXTURE0,
                    x_tex_scale * u_idx / rings,
                    y_tex_scale * j / slices,
                )
                GL.glMultiTexCoord3f(
                    GL.GL_TEXTURE1,
                    math.cos(ri + math.pi * 0.5),
                    0.0,
                    math.sin(ri + math.pi * 0.5),
                )
                GL.glMultiTexCoord3f(
                    GL.GL_TEXTURE2,
                    0.0,
                    math.sin(sj + math.pi * 0.5),
                    0.0,
                )
                GL.glMultiTexCoord3f(GL.GL_TEXTURE3, cr, ss, sr)
                rr: float = inner_radius + ring_radius + ring_radius * cs
                GL.glVertex3f(rr * cr, ring_radius * ss, rr * sr)
        GL.glEnd()


def draw_box(size: float, tex_scale: float) -> None:
    s: float = size * 0.5
    faces: list[tuple[Any, ...]] = [
        (
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, -1),
            [(-s, -s, -s), (-s, s, -s), (s, s, -s), (s, -s, -s)],
        ),
        (
            (-1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            [(s, -s, s), (s, s, s), (-s, s, s), (-s, -s, s)],
        ),
        (
            (0, 0, 1),
            (0, 1, 0),
            (1, 0, 0),
            [(s, -s, -s), (s, s, -s), (s, s, s), (s, -s, s)],
        ),
        (
            (0, 0, -1),
            (0, 1, 0),
            (-1, 0, 0),
            [(-s, -s, s), (-s, s, s), (-s, s, -s), (-s, -s, -s)],
        ),
        (
            (1, 0, 0),
            (0, 0, 1),
            (0, 1, 0),
            [(-s, s, -s), (-s, s, s), (s, s, s), (s, s, -s)],
        ),
        (
            (1, 0, 0),
            (0, 0, -1),
            (0, -1, 0),
            [(-s, -s, s), (-s, -s, -s), (s, -s, -s), (s, -s, s)],
        ),
    ]
    GL.glBegin(GL.GL_QUADS)
    uvs: list[tuple[float, float]] = [
        (0.0, 0.0),
        (0.0, tex_scale),
        (tex_scale, tex_scale),
        (tex_scale, 0.0),
    ]
    tx: int
    ty: int
    tz: int
    bx: int
    by: int
    bz: int
    nx: int
    ny: int
    nz: int
    verts: list[tuple[float, float, float]]
    for (tx, ty, tz), (bx, by, bz), (nx, ny, nz), verts in faces:
        k: int
        vert: tuple[float, float, float]
        for k, vert in enumerate(verts):
            uv: tuple[float, float] = uvs[k]
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0, uv[0], uv[1])
            GL.glMultiTexCoord3f(GL.GL_TEXTURE1, tx, ty, tz)
            GL.glMultiTexCoord3f(GL.GL_TEXTURE2, bx, by, bz)
            GL.glMultiTexCoord3f(GL.GL_TEXTURE3, nx, ny, nz)
            GL.glVertex3f(*vert)
    GL.glEnd()


def draw_models() -> None:
    p: int = state.prog_obj[state.which_shader]
    loc: int = GL.glGetUniformLocation(p, "sampler0")
    if loc != -1:
        GL.glUniform1i(loc, 0)
    loc = GL.glGetUniformLocation(p, "lightPos0")
    if loc != -1:
        GL.glUniform3fv(loc, 1, state.light_pos0)

    GL.glColor3f(0.8, 0.5, 0.3)
    if state.which_shape == CYLINDER:
        draw_cylinder(25.0, 70.0, 25, 20.0, 10.0)
    elif state.which_shape == TORUS:
        draw_torus(20.0, 15.0, 50, 25, 40.0, 12.0)
    else:
        draw_box(70.0, 10.0)


def select_shader(n: int) -> None:
    state.which_shader = n
    GL.glUseProgram(state.prog_obj[state.which_shader])


def select_bumpmap(n: int) -> None:
    state.which_bumpmap = n
    GL.glBindTexture(GL.GL_TEXTURE_2D, state.which_bumpmap)


def _nudge_light(d: float) -> None:
    state.light_rotation += d
    update_light()


def _nudge_cam(axis: int, d: float) -> None:
    state.camera_pos[axis] += d


def _select_shape(i: int) -> None:
    state.which_shape = i


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column (discovery); hold the key for
    # continuous motion.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit",
            "Esc",
            lambda: glfw.set_window_should_close(state.window, True),
        )
        imgui.end_menu()
    _common.draw_view_menu(state.window)
    if imgui.begin_menu("Render options", True):
        if imgui.begin_menu("Shape", True):
            i: int
            name: str
            for i, name in enumerate(shape_names):
                _common.menu_action(
                    name,
                    "",
                    lambda i=i: _select_shape(i),
                    selected=(state.which_shape == i),
                )
            imgui.end_menu()
        if imgui.begin_menu("Shader", True):
            i: int
            name: str
            for i, name in enumerate(shader_names):
                _common.menu_action(
                    name,
                    "",
                    lambda i=i: select_shader(i),
                    selected=(state.which_shader == i),
                )
            imgui.end_menu()
        if imgui.begin_menu("Bump texture", True):
            i: int
            name: str
            for i, name in enumerate(bumpmap_names):
                _common.menu_action(
                    name,
                    "",
                    lambda i=i: select_bumpmap(i),
                    selected=(state.which_bumpmap == i),
                )
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


def render_scene() -> None:
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, 1.0, 1.0, 1000.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(
        state.camera_pos[0],
        state.camera_pos[1],
        state.camera_pos[2],
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
    )
    GL.glViewport(0, 0, state.window_width, state.window_height)
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_models()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_CULL_FACE)

    state.max_tex_size = GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR
    )
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
    create_rivet_map()
    GL.glBindTexture(GL.GL_TEXTURE_2D, 1)
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR
    )
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
    create_pyramid_map()
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    update_light()
    i: int
    for i in range(TOTAL_SHADER_SETS):
        prepare_shader(i)
    GL.glUseProgram(state.prog_obj[state.which_shader])


def change_size(w: int, h: int) -> None:
    state.window_width = w
    state.window_height = h


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, mods: int
) -> None:
    # Shape, shader, and bumpmap texture selection moved to the imgui panel;
    # keys here are navigation only.
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
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window: typing.Any = glfw.create_window(  # glfw window handle
        state.window_width, state.window_height, "Bump Mapping Demo", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    state.window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl: GlfwRenderer = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])
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
