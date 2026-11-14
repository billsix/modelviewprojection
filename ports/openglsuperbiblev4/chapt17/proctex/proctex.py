# proctex.py
# Procedural texture demo: a single sphere drawn three different
# ways by the fragment shader. checkerboard divides surface UVs into
# squares; beachball uses lat/long stripes; toyball does the
# half-spheres + star pattern from the SIGGRAPH RenderMan classic.
#
# Shader selection and tessellation live on an imgui panel; left/right
# rotate the light; X/Y/Z move the camera (shift = -); Esc to quit.
#
# OpenGL SuperBible, Chapter 17
# Python port of proctex.cpp by Benjamin Lipchak

import dataclasses
import os
import sys
import typing

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
import _primitives  # noqa: E402

CHECKERBOARD: int = 0
BEACHBALL: int = 1
TOYBALL: int = 2
TOTAL_SHADER_SETS: int = 3
shader_names: list[str] = ["checkerboard", "beachball", "toyball"]

camera_zoom: float = 0.4
light_pos: np.ndarray = np.array([140.0, 250.0, 140.0, 1.0], dtype=np.float32)


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    window: typing.Any = None  # glfw window handle; set in main()
    window_width: int = 1024
    window_height: int = 768

    v_shader: list[int] = dataclasses.field(
        default_factory=lambda: [0] * TOTAL_SHADER_SETS
    )
    f_shader: list[int] = dataclasses.field(
        default_factory=lambda: [0] * TOTAL_SHADER_SETS
    )
    prog_obj: list[int] = dataclasses.field(
        default_factory=lambda: [0] * TOTAL_SHADER_SETS
    )
    which_shader: int = CHECKERBOARD

    camera_pos: list[float] = dataclasses.field(
        default_factory=lambda: [50.0, 50.0, 150.0, 1.0]
    )

    light_rotation: float = 0.0
    tess: int = 75
    # placeholder; rebuild_sphere() builds the real sphere at import
    sphere_mesh: _primitives.Mesh = dataclasses.field(
        default_factory=lambda: (0, [])
    )


state: AppState = AppState()


def transform_vec3(v: np.ndarray, m: np.ndarray) -> np.ndarray:
    out: np.ndarray = np.zeros(3, dtype=np.float32)
    r: int
    for r in range(3):
        out[r] = (
            m[r] * v[0] + m[r + 4] * v[1] + m[r + 8] * v[2] + m[r + 12] * v[3]
        )
    return out


def rebuild_sphere() -> None:
    """Re-tessellate the sphere. Called once at import, then ONLY when the tess
    level changes (UP/DOWN keys) -- the sin/cos work happens on that key event,
    never in the per-frame render path."""
    state.sphere_mesh = _primitives.build_sphere(50.0, state.tess, state.tess)


rebuild_sphere()


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


def draw_models() -> None:
    GL.glPushMatrix()
    GL.glRotatef(state.light_rotation, 0.0, 1.0, 0.0)
    mv: np.ndarray = np.array(
        GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX), dtype=np.float32
    ).flatten()
    light_pos_eye: np.ndarray = transform_vec3(light_pos, mv)
    GL.glPopMatrix()
    p: int = state.prog_obj[state.which_shader]
    loc: int = GL.glGetUniformLocation(p, "lightPos")
    if loc != -1:
        GL.glUniform3fv(loc, 1, light_pos_eye)
    _primitives.draw_mesh(state.sphere_mesh)


def render_scene() -> None:
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if state.window_width > state.window_height:
        ar: float = float(state.window_width) / float(state.window_height)
        GL.glFrustum(
            -ar * camera_zoom,
            ar * camera_zoom,
            -camera_zoom,
            camera_zoom,
            1.0,
            1000.0,
        )
    else:
        ar = float(state.window_height) / float(state.window_width)
        GL.glFrustum(
            -camera_zoom,
            camera_zoom,
            -ar * camera_zoom,
            ar * camera_zoom,
            1.0,
            1000.0,
        )
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


def select_shader(n: int) -> None:
    state.which_shader = n
    GL.glUseProgram(state.prog_obj[state.which_shader])


def _nudge_light(d: float) -> None:
    state.light_rotation += d


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column; hold the key for continuous
    # motion. Changing tessellation re-tessellates the sphere on the spot.
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
        imgui.separator()
        if imgui.begin_menu("Tessellation", True):
            tess_slider: tuple[bool, int] = imgui.slider_int(
                "##tess", state.tess, 5, 150
            )
            state.tess = tess_slider[1]
            if tess_slider[0]:
                rebuild_sphere()
            imgui.end_menu()
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Light -", "Left", lambda: _nudge_light(-5.0))
        _common.menu_action("Light +", "Right", lambda: _nudge_light(5.0))
        imgui.separator()
        _common.menu_action(
            "Camera +X",
            "X",
            lambda: state.camera_pos.__setitem__(0, state.camera_pos[0] + 5.0),
        )
        _common.menu_action(
            "Camera -X",
            "Shift+X",
            lambda: state.camera_pos.__setitem__(0, state.camera_pos[0] - 5.0),
        )
        _common.menu_action(
            "Camera +Y",
            "Y",
            lambda: state.camera_pos.__setitem__(1, state.camera_pos[1] + 5.0),
        )
        _common.menu_action(
            "Camera -Y",
            "Shift+Y",
            lambda: state.camera_pos.__setitem__(1, state.camera_pos[1] - 5.0),
        )
        _common.menu_action(
            "Camera +Z",
            "Z",
            lambda: state.camera_pos.__setitem__(2, state.camera_pos[2] + 5.0),
        )
        _common.menu_action(
            "Camera -Z",
            "Shift+Z",
            lambda: state.camera_pos.__setitem__(2, state.camera_pos[2] - 5.0),
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    i: int
    for i in range(TOTAL_SHADER_SETS):
        prepare_shader(i)
    select_shader(CHECKERBOARD)


def change_size(w: int, h: int) -> None:
    state.window_width = w
    state.window_height = h


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, mods: int
) -> None:
    # Shader selection and tessellation moved to the imgui panel; keys here
    # are navigation only. These keys are mirrored by the panel's "Controls"
    # buttons (which name each key).
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
        return
    if key == glfw.KEY_LEFT:
        _nudge_light(-5.0)
    elif key == glfw.KEY_RIGHT:
        _nudge_light(5.0)
    elif key == glfw.KEY_X:
        state.camera_pos[0] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Y:
        state.camera_pos[1] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Z:
        state.camera_pos[2] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window: typing.Any = glfw.create_window(  # glfw window handle
        state.window_width,
        state.window_height,
        "Procedural Texture Mapping Demo",
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
