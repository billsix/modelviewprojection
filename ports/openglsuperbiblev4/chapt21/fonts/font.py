# font.py
# The original uses glXUseXFont + glCallLists to render a fixed
# bitmap string with X11 fonts. That path is X-server-side and not
# portable to non-X platforms. This port renders the same demo
# (a single string on a green background) using imgui_bundle.
#
# OpenGL SuperBible, Chapter 21
# Python port of font.c by Nick Haemel

import os
import sys

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    
    window_width, window_height = _common.resolve_default_window_size()
    window = glfw.create_window(window_width, window_height, "Fonts", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    glfw.make_context_current(window)
    impl = _common.init_imgui(window)
    win_state = _common.WindowState()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            break
        GL.glClearColor(0.0, 1.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        imgui.new_frame()

        _common.draw_menubar(window, win_state)
        size = glfw.get_framebuffer_size(window)
        flags = (imgui.WindowFlags_.no_decoration.value
                 | imgui.WindowFlags_.no_background.value
                 | imgui.WindowFlags_.no_inputs.value)
        imgui.set_next_window_pos((0, 0))
        imgui.set_next_window_size((size[0], size[1]))
        imgui.begin("text", None, flags)
        imgui.set_window_font_scale(2.5)
        imgui.text_colored((0, 0, 0, 1), "GLX Fonts")
        imgui.end()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
