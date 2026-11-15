# motionblur.py
# Motion blur via the accumulation buffer. Each frame draws the
# revolving sphere 10 times at slightly different rotations and blends
# them together.
#
# Many drivers and window systems (Wayland among them) give a context no
# accumulation buffer. When GL_ACCUM_RED_BITS is 0 the demo does the same
# weighted sum with two textures and additive blending instead: each pass
# is copied into one texture and added, scaled, onto a running sum kept in
# the other.
#
# OpenGL SuperBible, Chapter 6
# Python port of MotionBlur.cpp by Richard S. Wright Jr.

import dataclasses
import os
import sys
import typing

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
import _primitives  # noqa: E402


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    # glfw window handle; set in main() for Quit item
    window: typing.Any = None

    y_rot: float = 45.0

    # True when the context has an accumulation buffer; set in main()
    has_accum: bool = False
    # framebuffer size, for the texture fallback; set in change_size()
    width: int = 1
    height: int = 1
    # fallback textures: the pass just drawn, and the running weighted sum
    pass_texture: int = 0
    sum_texture: int = 0


state: AppState = AppState()


f_light_pos: tuple[float, float, float, float] = (-100.0, 100.0, 50.0, 1.0)
f_no_light: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
f_low_light: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 1.0)
f_bright_light: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)


# The revolving sphere is the same every frame (drawn 10x per frame for
# the accumulation-buffer blur) -- tessellate once at import, replay each pass.
SPHERE: _primitives.Mesh = _primitives.build_sphere(0.1, 17, 9)


def draw_ground() -> None:
    extent: float = 20.0
    step: float = 0.5
    bounce: int = 0
    GL.glShadeModel(GL.GL_FLAT)
    strip: float = -extent
    while strip <= extent:
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        run: float = extent
        while run >= -extent:
            color: float = 1.0 if bounce % 2 == 0 else 0.0
            GL.glColor4f(color, color, color, 0.5)
            GL.glVertex3f(strip, 0.0, run)
            GL.glVertex3f(strip + step, 0.0, run)
            bounce += 1
            run -= step
        GL.glEnd()
        strip += step
    GL.glShadeModel(GL.GL_SMOOTH)


def draw_geometry() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    draw_ground()

    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glTranslatef(0.0, 0.5, -3.5)
    GL.glRotatef(-(state.y_rot * 2.0), 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE)
    GL.glPopMatrix()


PASSES: int = 10


def pass_weight(index: int) -> float:
    # The newest image gets half the weight; the trailing ones share the rest.
    return 0.5 if index == 0 else 0.5 / PASSES


def add_texture(texture: int, weight: float) -> None:
    """Add ``weight`` times ``texture`` to every pixel of the color buffer.

    Call between ``begin_texture_sum`` and ``end_texture_sum``.
    """
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
    # GL_MODULATE multiplies each texel by the current color.
    GL.glColor4f(weight, weight, weight, 1.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glTexCoord2f(0.0, 0.0)
    GL.glVertex2f(-1.0, -1.0)
    GL.glTexCoord2f(1.0, 0.0)
    GL.glVertex2f(1.0, -1.0)
    GL.glTexCoord2f(1.0, 1.0)
    GL.glVertex2f(1.0, 1.0)
    GL.glTexCoord2f(0.0, 1.0)
    GL.glVertex2f(-1.0, 1.0)
    GL.glEnd()


def begin_texture_sum() -> None:
    # Clear the color buffer to black, then add full-window quads to it with
    # no lighting or depth test.
    GL.glPushAttrib(
        GL.GL_ENABLE_BIT
        | GL.GL_CURRENT_BIT
        | GL.GL_COLOR_BUFFER_BIT
        | GL.GL_TEXTURE_BIT
    )
    GL.glDisable(GL.GL_LIGHTING)
    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
    GL.glClearColor(0.0, 0.0, 0.0, 0.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPushMatrix()
    GL.glLoadIdentity()
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glLoadIdentity()


def end_texture_sum() -> None:
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPopMatrix()
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPopMatrix()
    GL.glPopAttrib()


def copy_color_buffer_to(texture: int) -> None:
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
    GL.glCopyTexSubImage2D(
        GL.GL_TEXTURE_2D, 0, 0, 0, 0, 0, state.width, state.height
    )


def render_scene() -> None:
    state.y_rot = 35.0
    index: int
    for index in range(PASSES):
        state.y_rot += 0.75
        draw_geometry()
        if state.has_accum:
            if index == 0:
                GL.glAccum(GL.GL_LOAD, pass_weight(index))
            else:
                GL.glAccum(GL.GL_ACCUM, pass_weight(index))
        else:
            # sum = sum + weight * pass, rebuilt in the color buffer
            copy_color_buffer_to(state.pass_texture)
            begin_texture_sum()
            if index > 0:
                add_texture(state.sum_texture, 1.0)
            add_texture(state.pass_texture, pass_weight(index))
            end_texture_sum()
            copy_color_buffer_to(state.sum_texture)

    if state.has_accum:
        GL.glAccum(GL.GL_RETURN, 1.0)
    # Without an accumulation buffer the color buffer already holds the sum.


def setup_rc() -> None:
    GL.glClearColor(*f_low_light)
    GL.glCullFace(GL.GL_BACK)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, f_no_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, f_low_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, f_bright_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, f_bright_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, f_light_pos)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    state.width = w
    state.height = h
    texture: int
    for texture in (state.pass_texture, state.sum_texture):
        if texture == 0:
            continue
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA8,
            w,
            h,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            None,
        )
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 50.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, -0.4, 0.0)


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    # All controls in the top menubar. This demo has no movement keys, so the
    # bar carries only File -> Quit (mirrors Esc).
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
    imgui.end_main_menu_bar()


def main() -> None:

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    # Request an accumulation buffer (GLUT_ACCUM in the original)
    glfw.window_hint(glfw.ACCUM_RED_BITS, 16)
    glfw.window_hint(glfw.ACCUM_GREEN_BITS, 16)
    glfw.window_hint(glfw.ACCUM_BLUE_BITS, 16)
    glfw.window_hint(glfw.ACCUM_ALPHA_BITS, 16)

    window: typing.Any = glfw.create_window(  # glfw window handle
        800, 600, "Motion Blur with the Accumulation Buffer", None, None
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
    state.has_accum = GL.glGetIntegerv(GL.GL_ACCUM_RED_BITS) > 0
    if not state.has_accum:
        print("No accumulation buffer; blending textures instead.")
        textures: typing.Any = GL.glGenTextures(2)  # numpy array of names
        state.pass_texture = int(textures[0])
        state.sum_texture = int(textures[1])
        texture: int
        for texture in (state.pass_texture, state.sum_texture):
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            # one level, no mipmaps, so the default filter must change
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST
            )
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST
            )
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
