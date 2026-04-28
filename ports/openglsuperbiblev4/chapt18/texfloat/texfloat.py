# texfloat.py
# Floating-point textures (GL_RGB16F): load an HDR EXR image into a
# half-float 2D texture, then run one of four tone-mapping fragment
# shaders to bring it into 0..1. The "iris" and "whitebalance"
# shaders are interactive: they use the brightest texel within a
# 51x51 cursor window to set their exposure or white-balance values.
#
# Keys: F1..F4 = clamped/trivial/iris/whitebalance shader; 1..8 picks
# the EXR image (Blobbies, Desk, GoldenGate, MtTamWest, Ocean,
# Spirals, StillLife, Tree); arrow keys move the cursor (mouse motion
# also updates it); Esc to quit.
#
# OpenGL SuperBible, Chapter 18
# Python port of texfloat.cpp by Benjamin Lipchak

import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
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

CLAMPED, TRIVIAL, IRIS, WHITEBALANCE = 0, 1, 2, 3
TOTAL_SHADERS = 4
shader_names = ["clamped", "trivial", "iris", "whitebalance"]
f_shader = [0] * TOTAL_SHADERS
prog_obj = [0] * TOTAL_SHADERS
current_shader: int = TRIVIAL

exr_files = [
    "Blobbies.exr", "Desk.exr", "GoldenGate.exr", "MtTamWest.exr",
    "Ocean.exr", "Spirals.exr", "StillLife.exr", "Tree.exr",
]

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
    GL.glUseProgram(prog_obj[n])
    loc = GL.glGetUniformLocation(prog_obj[n], "sampler0")
    if loc != -1:
        GL.glUniform1i(loc, 0)
    GL.glUseProgram(0)


def alter_aspect() -> None:
    global x_aspect, y_aspect
    if window_height == 0:
        x_aspect, y_aspect = 0.00001, 1.0
        return
    ta = float(npot_w) / float(npot_h)
    wa = float(window_width) / float(window_height)
    if ta > wa:
        x_aspect, y_aspect = 1.0, wa / ta
    else:
        x_aspect, y_aspect = ta / wa, 1.0


def setup_textures(which: int) -> None:
    global f_texels, npot_w, npot_h, pot_w, pot_h
    img = iio.imread(os.path.join(PWD, "openexr-images", exr_files[which]))
    img = np.flipud(img).astype(np.float32)
    if img.ndim == 3 and img.shape[2] >= 3:
        img = img[:, :, :3]
    npot_h, npot_w = img.shape[:2]
    pot_w, pot_h = npot_w, npot_h
    f_texels = np.ascontiguousarray(img, dtype=np.float32)
    alter_aspect()
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, 1)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB16F, pot_w, pot_h, 0,
                    GL.GL_RGB, GL.GL_FLOAT, f_texels)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                       GL.GL_LINEAR_MIPMAP_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
    print(f"Loaded {exr_files[which]} ({npot_w}x{npot_h})")


def render_scene() -> None:
    global max_r, max_g, max_b
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glUseProgram(prog_obj[current_shader])

    if current_shader in (IRIS, WHITEBALANCE) and f_texels is not None:
        center_u = int(((f_cursor_x / x_aspect) + 1.0) * 0.5 * npot_w)
        center_v = int(((f_cursor_y / y_aspect) + 1.0) * 0.5 * npot_h)
        u0 = max(0, center_u - 25); u1 = min(npot_w, center_u + 26)
        v0 = max(0, center_v - 25); v1 = min(npot_h, center_v + 26)
        if u1 > u0 and v1 > v0:
            patch = f_texels[v0:v1, u0:u1]
            new_max = patch.reshape(-1, 3).max(axis=0)
            max_r += (new_max[0] - max_r) * 0.01
            max_g += (new_max[1] - max_g) * 0.01
            max_b += (new_max[2] - max_b) * 0.01
        loc = GL.glGetUniformLocation(prog_obj[current_shader], "max")
        if loc != -1:
            GL.glUniform3f(loc, max_r, max_g, max_b)

    GL.glBegin(GL.GL_QUADS)
    GL.glTexCoord2f(0.0, 0.0)
    GL.glVertex2f(-x_aspect, -y_aspect)
    GL.glTexCoord2f(0.0, npot_h / pot_h)
    GL.glVertex2f(-x_aspect, y_aspect)
    GL.glTexCoord2f(npot_w / pot_w, npot_h / pot_h)
    GL.glVertex2f(x_aspect, y_aspect)
    GL.glTexCoord2f(npot_w / pot_w, 0.0)
    GL.glVertex2f(x_aspect, -y_aspect)
    GL.glEnd()

    GL.glUseProgram(0)

    if current_shader in (IRIS, WHITEBALANCE):
        hw = 51.0 * x_aspect / npot_w
        hh = 51.0 * y_aspect / npot_h
        GL.glColor4f(1.0, 0.0, 0.0, 1.0)
        GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex2f(f_cursor_x - hw, f_cursor_y - hh)
        GL.glVertex2f(f_cursor_x - hw, f_cursor_y + hh)
        GL.glVertex2f(f_cursor_x + hw, f_cursor_y + hh)
        GL.glVertex2f(f_cursor_x + hw, f_cursor_y - hh)
        GL.glEnd()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    setup_textures(0)
    for i in range(TOTAL_SHADERS):
        prepare_shader(i)


def cursor_update(x: float, y: float) -> None:
    global f_cursor_x, f_cursor_y
    f_cursor_x = max(-x_aspect, min(x_aspect, 2.0 * (x - 0.5)))
    f_cursor_y = max(-y_aspect, min(y_aspect, 2.0 * (y - 0.5)))
    f_cursor_y *= -1.0


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h
    GL.glViewport(0, 0, w, h)
    alter_aspect()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_mouse_pos(_window, x: float, y: float) -> None:
    global i_cursor_x, i_cursor_y
    i_cursor_x = int(x); i_cursor_y = int(y)
    if window_width > 1 and window_height > 1:
        cursor_update(x / (window_width - 1), y / (window_height - 1))


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    global current_shader, i_cursor_x, i_cursor_y
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True); return
    if key == glfw.KEY_F1:
        current_shader = CLAMPED; print("shader: clamped"); return
    if key == glfw.KEY_F2:
        current_shader = TRIVIAL; print("shader: trivial"); return
    if key == glfw.KEY_F3:
        current_shader = IRIS; print("shader: iris"); return
    if key == glfw.KEY_F4:
        current_shader = WHITEBALANCE; print("shader: whitebalance"); return
    if glfw.KEY_1 <= key <= glfw.KEY_8:
        setup_textures(key - glfw.KEY_1); return
    if key == glfw.KEY_LEFT:
        i_cursor_x = max(0, i_cursor_x - 1)
    elif key == glfw.KEY_RIGHT:
        i_cursor_x = min(window_width - 1, i_cursor_x + 1)
    elif key == glfw.KEY_UP:
        i_cursor_y = max(0, i_cursor_y - 1)
    elif key == glfw.KEY_DOWN:
        i_cursor_y = min(window_height - 1, i_cursor_y + 1)
    else:
        return
    if window_width > 1 and window_height > 1:
        cursor_update(i_cursor_x / (window_width - 1),
                      i_cursor_y / (window_height - 1))


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    
    window_width, window_height = _common.resolve_default_window_size()
    window = glfw.create_window(window_width, window_height,
                                "Floating-Point Texture Demo", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_cursor_pos_callback(window, on_mouse_pos)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    impl = _common.init_imgui(window)
    win_state = _common.WindowState()

    print("Floating-Point Texture Demo")
    print("  F1..F4: shader (clamped/trivial/iris/whitebalance)")
    print("  1..8: image (Blobbies/Desk/GoldenGate/MtTamWest/")
    print("               Ocean/Spirals/StillLife/Tree)")
    print("  arrows or mouse: move cursor   Esc: quit")

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
