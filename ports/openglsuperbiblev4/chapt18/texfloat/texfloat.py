# texfloat.py
# Floating-point textures (GL_RGB16F): load an HDR EXR image into a
# half-float 2D texture, then run one of four tone-mapping fragment
# shaders to bring it into 0..1. The "iris" and "whitebalance"
# shaders are interactive: they use the brightest texel within a
# 51x51 cursor window to set their exposure or white-balance values.
#
# Keys: arrow keys move the pixel-probe cursor (mouse motion also
# updates it); Esc to quit. The tone-map shader and the test image
# live on an imgui panel.
#
# OpenGL SuperBible, Chapter 18
# Python port of texfloat.cpp by Benjamin Lipchak

import dataclasses
import os
import sys
import typing

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

CLAMPED: int = 0
TRIVIAL: int = 1
IRIS: int = 2
WHITEBALANCE: int = 3
TOTAL_SHADERS: int = 4
shader_names: list[str] = ["clamped", "trivial", "iris", "whitebalance"]

exr_files: list[str] = [
    "Blobbies.exr",
    "Desk.exr",
    "GoldenGate.exr",
    "MtTamWest.exr",
    "Ocean.exr",
    "Spirals.exr",
    "StillLife.exr",
    "Tree.exr",
]
image_names: list[str] = [os.path.splitext(f)[0] for f in exr_files]


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    window: typing.Any = None  # glfw window handle; set in main(), used by Quit
    window_width: int = 1024
    window_height: int = 768

    f_shader: list[int] = dataclasses.field(
        default_factory=lambda: [0] * TOTAL_SHADERS
    )
    prog_obj: list[int] = dataclasses.field(
        default_factory=lambda: [0] * TOTAL_SHADERS
    )
    current_shader: int = TRIVIAL

    current_image: int = 0

    f_texels: np.ndarray | None = None
    npot_w: int = 0
    npot_h: int = 0
    pot_w: int = 0
    pot_h: int = 0
    x_aspect: float = 1.0
    y_aspect: float = 1.0

    f_cursor_x: float = 0.0
    f_cursor_y: float = 0.0
    i_cursor_x: int = 0
    i_cursor_y: int = 0
    max_r: float = 0.0
    max_g: float = 0.0
    max_b: float = 0.0


state: AppState = AppState()


def _trace(msg: str) -> None:
    # DEBUG instrumentation: texfloat segfaults (C-level SIGSEGV) at startup on
    # some Mesa drivers, somewhere in setup_rc -> setup_textures. flush=True so
    # the LAST line printed before the crash survives and names the failing
    # call. Remove once the culprit GL call is identified and fixed.
    print(f"[texfloat] {msg}", flush=True)


def prepare_shader(n: int) -> None:
    fname: str = os.path.join(PWD, "shaders", f"{shader_names[n]}.fs")
    f: typing.TextIO
    with open(fname) as f:
        fs_src: str = f.read()
    state.f_shader[n] = shaders_mod.compileShader(fs_src, GL.GL_FRAGMENT_SHADER)
    state.prog_obj[n] = GL.glCreateProgram()
    GL.glAttachShader(state.prog_obj[n], state.f_shader[n])
    GL.glLinkProgram(state.prog_obj[n])
    if not GL.glGetProgramiv(state.prog_obj[n], GL.GL_LINK_STATUS):
        info: bytes = GL.glGetProgramInfoLog(state.prog_obj[n])
        sys.stderr.write(f"Program {n} link error: {info}\n")
        sys.exit(1)
    GL.glUseProgram(state.prog_obj[n])
    loc: int = GL.glGetUniformLocation(state.prog_obj[n], "sampler0")
    if loc != -1:
        GL.glUniform1i(loc, 0)
    GL.glUseProgram(0)


def alter_aspect() -> None:
    if state.window_height == 0:
        state.x_aspect = 0.00001
        state.y_aspect = 1.0
        return
    ta: float = float(state.npot_w) / float(state.npot_h)
    wa: float = float(state.window_width) / float(state.window_height)
    if ta > wa:
        state.x_aspect = 1.0
        state.y_aspect = wa / ta
    else:
        state.x_aspect = ta / wa
        state.y_aspect = 1.0


def setup_textures(which: int) -> None:
    state.current_image = which
    _trace(f"setup_textures({which}): imread {exr_files[which]}")
    img: np.ndarray = iio.imread(
        os.path.join(PWD, "openexr-images", exr_files[which])
    )
    img = np.flipud(img).astype(np.float32)
    if img.ndim == 3 and img.shape[2] >= 3:
        img = img[:, :, :3]
    img_shape: tuple[int, ...] = img.shape[:2]
    state.npot_h = img_shape[0]
    state.npot_w = img_shape[1]
    state.pot_w = state.npot_w
    state.pot_h = state.npot_h
    state.f_texels = np.ascontiguousarray(img, dtype=np.float32)
    _trace(
        f"  image {state.npot_w}x{state.npot_h} shape={state.f_texels.shape} "
        f"MAX_TEXTURE_SIZE={GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE)}"
    )
    alter_aspect()
    _trace("  glTexParameteri(GL_GENERATE_MIPMAP, 1)")
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, 1)
    _trace(
        f"  glTexImage2D(RGB16F, {state.pot_w}, {state.pot_h}, "
        f"GL_RGB, GL_FLOAT)"
    )
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D,
        0,
        GL.GL_RGB16F,
        state.pot_w,
        state.pot_h,
        0,
        GL.GL_RGB,
        GL.GL_FLOAT,
        state.f_texels,
    )
    _trace("  glTexImage2D returned OK")
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE
    )
    print(f"Loaded {exr_files[which]} ({state.npot_w}x{state.npot_h})")


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glUseProgram(state.prog_obj[state.current_shader])

    if (
        state.current_shader in (IRIS, WHITEBALANCE)
        and state.f_texels is not None
    ):
        center_u: int = int(
            ((state.f_cursor_x / state.x_aspect) + 1.0) * 0.5 * state.npot_w
        )
        center_v: int = int(
            ((state.f_cursor_y / state.y_aspect) + 1.0) * 0.5 * state.npot_h
        )
        u0: int = max(0, center_u - 25)
        u1: int = min(state.npot_w, center_u + 26)
        v0: int = max(0, center_v - 25)
        v1: int = min(state.npot_h, center_v + 26)
        if u1 > u0 and v1 > v0:
            patch: np.ndarray = state.f_texels[v0:v1, u0:u1]
            new_max: np.ndarray = patch.reshape(-1, 3).max(axis=0)
            state.max_r += (new_max[0] - state.max_r) * 0.01
            state.max_g += (new_max[1] - state.max_g) * 0.01
            state.max_b += (new_max[2] - state.max_b) * 0.01
        loc: int = GL.glGetUniformLocation(
            state.prog_obj[state.current_shader], "max"
        )
        if loc != -1:
            GL.glUniform3f(loc, state.max_r, state.max_g, state.max_b)

    GL.glBegin(GL.GL_QUADS)
    GL.glTexCoord2f(0.0, 0.0)
    GL.glVertex2f(-state.x_aspect, -state.y_aspect)
    GL.glTexCoord2f(0.0, state.npot_h / state.pot_h)
    GL.glVertex2f(-state.x_aspect, state.y_aspect)
    GL.glTexCoord2f(state.npot_w / state.pot_w, state.npot_h / state.pot_h)
    GL.glVertex2f(state.x_aspect, state.y_aspect)
    GL.glTexCoord2f(state.npot_w / state.pot_w, 0.0)
    GL.glVertex2f(state.x_aspect, -state.y_aspect)
    GL.glEnd()

    GL.glUseProgram(0)

    if state.current_shader in (IRIS, WHITEBALANCE):
        hw: float = 51.0 * state.x_aspect / state.npot_w
        hh: float = 51.0 * state.y_aspect / state.npot_h
        GL.glColor4f(1.0, 0.0, 0.0, 1.0)
        GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex2f(state.f_cursor_x - hw, state.f_cursor_y - hh)
        GL.glVertex2f(state.f_cursor_x - hw, state.f_cursor_y + hh)
        GL.glVertex2f(state.f_cursor_x + hw, state.f_cursor_y + hh)
        GL.glVertex2f(state.f_cursor_x + hw, state.f_cursor_y - hh)
        GL.glEnd()


def setup_rc() -> None:
    _trace("setup_rc: start")
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    setup_textures(0)
    i: int
    for i in range(TOTAL_SHADERS):
        _trace(f"setup_rc: prepare_shader({i}) [{shader_names[i]}]")
        prepare_shader(i)
    _trace("setup_rc: done -- all textures + shaders set up")


def cursor_update(x: float, y: float) -> None:
    state.f_cursor_x = max(
        -state.x_aspect, min(state.x_aspect, 2.0 * (x - 0.5))
    )
    state.f_cursor_y = max(
        -state.y_aspect, min(state.y_aspect, 2.0 * (y - 0.5))
    )
    state.f_cursor_y *= -1.0


def change_size(w: int, h: int) -> None:
    state.window_width = w
    state.window_height = h
    GL.glViewport(0, 0, w, h)
    alter_aspect()


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def on_mouse_pos(_window: typing.Any, x: float, y: float) -> None:
    state.i_cursor_x = int(x)
    state.i_cursor_y = int(y)
    if state.window_width > 1 and state.window_height > 1:
        cursor_update(
            x / (state.window_width - 1), y / (state.window_height - 1)
        )


def _nudge_cursor(axis: int, delta: int) -> None:
    # Move the pixel-probe cursor one pixel (mirrors the arrow keys); this
    # is NOT a camera -- it positions the 51x51 readback window.
    if axis == 0:
        state.i_cursor_x = max(
            0, min(state.window_width - 1, state.i_cursor_x + delta)
        )
    else:
        state.i_cursor_y = max(
            0, min(state.window_height - 1, state.i_cursor_y + delta)
        )
    if state.window_width > 1 and state.window_height > 1:
        cursor_update(
            state.i_cursor_x / (state.window_width - 1),
            state.i_cursor_y / (state.window_height - 1),
        )


def _select_shader(i: int) -> None:
    state.current_shader = i


def imgui_menubar() -> None:
    # All controls live in the top menubar. The tone-map shader and test
    # image (were combos) are radio menus; the Controls menu drives the
    # pixel-probe readback cursor, NOT a camera. F1-F4 / 1-8 are the C++
    # shortcuts shown for discovery; hold an arrow for continuous motion.
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
        i: int
        name: str
        if imgui.begin_menu("Tone-map shader", True):
            for i, name in enumerate(shader_names):
                _common.menu_action(
                    name,
                    f"F{i + 1}",
                    lambda i=i: _select_shader(i),
                    selected=(state.current_shader == i),
                )
            imgui.end_menu()
        if imgui.begin_menu("Test image", True):
            for i, name in enumerate(image_names):
                _common.menu_action(
                    name,
                    str(i + 1),
                    lambda i=i: setup_textures(i),
                    selected=(state.current_image == i),
                )
            imgui.end_menu()
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Cursor left", "Left", lambda: _nudge_cursor(0, -1))
        _common.menu_action(
            "Cursor right", "Right", lambda: _nudge_cursor(0, 1)
        )
        _common.menu_action("Cursor up", "Up", lambda: _nudge_cursor(1, -1))
        _common.menu_action("Cursor down", "Down", lambda: _nudge_cursor(1, 1))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    # Shader and image selection moved to the imgui panel; the arrow
    # keys still drive the pixel-probe cursor (a debug interaction).
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
        return
    if key == glfw.KEY_LEFT:
        state.i_cursor_x = max(0, state.i_cursor_x - 1)
    elif key == glfw.KEY_RIGHT:
        state.i_cursor_x = min(state.window_width - 1, state.i_cursor_x + 1)
    elif key == glfw.KEY_UP:
        state.i_cursor_y = max(0, state.i_cursor_y - 1)
    elif key == glfw.KEY_DOWN:
        state.i_cursor_y = min(state.window_height - 1, state.i_cursor_y + 1)
    else:
        return
    if state.window_width > 1 and state.window_height > 1:
        cursor_update(
            state.i_cursor_x / (state.window_width - 1),
            state.i_cursor_y / (state.window_height - 1),
        )


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window: typing.Any = glfw.create_window(  # glfw window handle
        state.window_width,
        state.window_height,
        "Floating-Point Texture Demo",
        None,
        None,
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    state.window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl: GlfwRenderer = GlfwRenderer(window)
    # Register our callbacks AFTER GlfwRenderer (it installs non-chaining glfw
    # key + cursor callbacks); imgui still gets mouse via process_inputs.
    glfw.set_key_callback(window, on_key)
    glfw.set_cursor_pos_callback(window, on_mouse_pos)

    print("Floating-Point Texture Demo")
    print("  arrows or mouse: move cursor   Esc: quit")

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
