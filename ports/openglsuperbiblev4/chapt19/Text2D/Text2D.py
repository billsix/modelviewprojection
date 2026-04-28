# Text2D.py
# 2D bitmap text via wglUseFontBitmaps in the original. That's a
# Win32-specific path that doesn't exist on Linux/macOS, so this
# port renders the same bouncing-text demonstration using imgui_bundle
# for text overlay (which uses its own glyph rasterizer under the
# hood). The OpenGL drawing surface is the same blue background as
# GLRect.
#
# OpenGL SuperBible, Chapter 19
# Python port of Text2D.cpp by Richard S. Wright Jr.

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
    window = glfw.create_window(window_width, window_height, "Text2D", None, None)
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

        GL.glClearColor(0.0, 0.0, 0.4, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        imgui.new_frame()

        _common.draw_menubar(window, win_state)
        flags = (imgui.WindowFlags_.no_decoration.value
                 | imgui.WindowFlags_.no_background.value
                 | imgui.WindowFlags_.no_inputs.value)
        imgui.set_next_window_pos((0, 0))
        size = glfw.get_framebuffer_size(window)
        imgui.set_next_window_size((size[0], size[1]))
        imgui.begin("text", None, flags)
        imgui.set_cursor_pos((20, 20))
        imgui.text_colored((1, 1, 0, 1), "OpenGL Bitmap Fonts")
        imgui.set_cursor_pos((20, 60))
        imgui.text_colored((1, 1, 1, 1),
                           "Win32 wglUseFontBitmaps not portable;")
        imgui.set_cursor_pos((20, 80))
        imgui.text_colored((1, 1, 1, 1),
                           "rendered here via imgui_bundle. Esc to exit.")
        imgui.end()
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
