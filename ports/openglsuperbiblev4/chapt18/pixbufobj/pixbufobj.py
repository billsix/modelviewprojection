# pixbufobj.py
# Pixel Buffer Objects (PBOs): the demo renders a slowly-rotating
# texture quad, then reads the framebuffer back into one of three
# ring-buffered images and re-uses those as additional inputs to the
# next frame's blend (cheap motion blur). The PBO path keeps the
# pixel data on the GPU so glReadPixels and glTexImage2D don't
# round-trip through client memory.
#
# Keys: Esc quits. Motion blur, PBO mode, and animation speed live on
# an imgui panel.
#
# OpenGL SuperBible, Chapter 18
# Python port of pixbufobj.cpp by Benjamin Lipchak

import os
import sys
import time

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit control button
window_width: int = 512
window_height: int = 512
data_width: int = 512
data_height: int = 512
data_pitch: int = 512 * 3
data_offset_x: int = 0
data_offset_y: int = 0

use_pbos: bool = False
use_motion_blur: bool = True

pixels: list = [
    None,
    None,
    None,
]  # numpy arrays in client mode, None when on GPU
frame_good: list = [False, False, False]
current_frame: int = 0
angle_increment: float = 1.0
usage_hint: int = GL.GL_STREAM_COPY


def setup_textures() -> None:
    img = iio.imread(os.path.join(PWD, "reservoir.tga"))
    img = np.flipud(img)
    if img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]
    img = np.ascontiguousarray(img, dtype=np.uint8)
    h, w = img.shape[:2]

    half = (img.astype(np.uint16) >> 1).astype(np.uint8)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 1)
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D,
        0,
        GL.GL_RGB8,
        w,
        h,
        0,
        GL.GL_RGB,
        GL.GL_UNSIGNED_BYTE,
        half,
    )
    for p in (GL.GL_TEXTURE_MAG_FILTER, GL.GL_TEXTURE_MIN_FILTER):
        GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_LINEAR)
    for p in (GL.GL_TEXTURE_WRAP_S, GL.GL_TEXTURE_WRAP_T):
        GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_CLAMP_TO_BORDER)

    quarter = (half.astype(np.uint16) >> 1).astype(np.uint8)
    for i in (2, 3, 4):
        GL.glBindTexture(GL.GL_TEXTURE_2D, i)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB8,
            w,
            h,
            0,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            quarter,
        )
        for p in (GL.GL_TEXTURE_MAG_FILTER, GL.GL_TEXTURE_MIN_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_LINEAR)
        for p in (GL.GL_TEXTURE_WRAP_S, GL.GL_TEXTURE_WRAP_T):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_CLAMP_TO_BORDER)

    for i in range(3):
        GL.glActiveTexture(GL.GL_TEXTURE0 + i)
        GL.glBindTexture(GL.GL_TEXTURE_2D, i + 1)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_ADD)
        GL.glEnable(GL.GL_TEXTURE_2D)
    if not use_motion_blur:
        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glLoadIdentity()


def render_scene() -> None:
    global current_frame
    current_frame = (current_frame + 1) % 3
    last_frame = (current_frame + 2) % 3
    frame_before_that = (current_frame + 1) % 3

    # Re-assert the per-unit 2D enables each frame. setup_textures enabled
    # GL_TEXTURE_2D on units 0/1/2 once, but the cleanup at the END of
    # render_scene disables units 1/2 (so they don't multitexture the imgui
    # menubar), so they must be turned back on here. Unit 2 follows the
    # motion-blur state (matches setup_textures / toggle_motion_blur).
    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glActiveTexture(GL.GL_TEXTURE2)
    if use_motion_blur:
        GL.glEnable(GL.GL_TEXTURE_2D)
    else:
        GL.glDisable(GL.GL_TEXTURE_2D)

    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glTranslatef(0.5, 0.5, 0.0)
    GL.glRotatef(angle_increment, 0.0, 0.0, 1.0)
    GL.glTranslatef(-0.5, -0.5, 0.0)

    if not use_motion_blur:
        copied = GL.glGetFloatv(GL.GL_TEXTURE_MATRIX)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glLoadMatrixf(copied)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 1)

    GL.glBegin(GL.GL_QUADS)
    for verts in [
        (-1.0, -1.0, 0.0, 0.0),
        (-1.0, 1.0, 0.0, 1.0),
        (1.0, 1.0, 1.0, 1.0),
        (1.0, -1.0, 1.0, 0.0),
    ]:
        x, y, u, v = verts
        for i in range(3):
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0 + i, u, v)
        GL.glVertex2f(x, y)
    GL.glEnd()

    if use_pbos:
        GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, current_frame + 1)
        GL.glReadPixels(
            data_offset_x,
            data_offset_y,
            data_width,
            data_height,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            None,
        )
        GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, 0)
    else:
        pixels[current_frame] = GL.glReadPixels(
            data_offset_x,
            data_offset_y,
            data_width,
            data_height,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
        )

    frame_good[current_frame] = True

    # Dim the last frame in place. With PBOs we map the buffer for
    # read-write; without, the bytes are already in client memory.
    if use_pbos:
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, last_frame + 1)
        ptr = GL.glMapBuffer(GL.GL_PIXEL_UNPACK_BUFFER, GL.GL_READ_WRITE)
        if ptr:
            arr = np.ctypeslib.as_array(
                (np.ctypes.c_uint8 * (data_height * data_pitch)).from_address(
                    int(ptr)
                )
            )
            arr >>= 2
            GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)
    else:
        if pixels[last_frame] is not None:
            buf = np.frombuffer(pixels[last_frame], dtype=np.uint8).copy()
            buf >>= 2
            pixels[last_frame] = buf.tobytes()

    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 2 + last_frame)
    if use_pbos:
        if frame_good[last_frame]:
            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                GL.GL_RGB8,
                data_width,
                data_height,
                0,
                GL.GL_RGB,
                GL.GL_UNSIGNED_BYTE,
                None,
            )
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
    elif frame_good[last_frame]:
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB8,
            data_width,
            data_height,
            0,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            pixels[last_frame],
        )

    GL.glActiveTexture(GL.GL_TEXTURE2)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 2 + frame_before_that)

    # Leave a clean single-unit state for the imgui menubar, drawn next via
    # the fixed-function GL2 backend on whatever unit is active. render_scene
    # otherwise returns with TEXTURE2 active and units 1/2's 2D textures still
    # enabled (GL_ADD env mode), which would multitexture/garble the menubar
    # AND bind imgui's font onto TEXTURE2, corrupting the blur on later frames.
    # Re-enabled at the top of render_scene next frame.
    GL.glActiveTexture(GL.GL_TEXTURE2)
    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glActiveTexture(GL.GL_TEXTURE0)


def toggle_motion_blur() -> None:
    global use_motion_blur
    use_motion_blur = not use_motion_blur
    if use_motion_blur:
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glLoadIdentity()
        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glEnable(GL.GL_TEXTURE_2D)
    else:
        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glDisable(GL.GL_TEXTURE_2D)
    print(f"motion blur: {'ON' if use_motion_blur else 'OFF'}")


def toggle_pbos() -> None:
    global use_pbos
    use_pbos = not use_pbos
    if use_pbos:
        for i in range(3):
            GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, i + 1)
            data = pixels[i] if pixels[i] is not None else None
            GL.glBufferData(
                GL.GL_PIXEL_PACK_BUFFER,
                data_height * data_pitch,
                data,
                usage_hint,
            )
            pixels[i] = None
        GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, 0)
    else:
        for i in range(3):
            GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, i + 1)
            buf = GL.glGetBufferSubData(
                GL.GL_PIXEL_PACK_BUFFER, 0, data_height * data_pitch
            )
            pixels[i] = bytes(buf)
        GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, 0)
        GL.glDeleteBuffers(3, [1, 2, 3])
    print(f"PBOs: {'ON' if use_pbos else 'OFF'}")


def setup_rc() -> None:
    if GL.glGetIntegerv(GL.GL_MAX_TEXTURE_UNITS) < 3:
        sys.stderr.write("Fewer than 3 texture units!\n")
        sys.exit(1)
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glColor4f(0.0, 0.0, 0.0, 1.0)
    GL.glMatrixMode(GL.GL_TEXTURE)
    setup_textures()


def change_size(w: int, h: int) -> None:
    global window_width, window_height, data_width, data_height
    global data_offset_x, data_offset_y, data_pitch
    window_width = data_width = w
    window_height = data_height = h
    data_offset_x = (window_width - data_width) // 2
    data_offset_y = (window_height - data_height) // 2
    GL.glViewport(data_offset_x, data_offset_y, data_width, data_height)
    data_pitch = ((data_width * 3) + 3) & ~0x3
    setup_textures()
    for i in range(3):
        frame_good[i] = False
        if not use_pbos:
            pixels[i] = bytes(data_height * data_pitch)
        else:
            GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, i + 1)
            GL.glBufferData(
                GL.GL_PIXEL_PACK_BUFFER,
                data_height * data_pitch,
                None,
                usage_hint,
            )
            GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, 0)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def imgui_menubar() -> None:
    # All controls live in the top menubar. This demo has no camera
    # navigation, so there is no separate Controls menu -- just File->Quit
    # plus the render options.
    global angle_increment
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Options", True):
        # toggle_motion_blur / toggle_pbos flip the global and do the GL
        # state work, so just call them when the item is clicked.
        if imgui.menu_item("Motion blur", "", use_motion_blur, True)[0]:
            toggle_motion_blur()
        if imgui.menu_item("Use PBOs", "", use_pbos, True)[0]:
            toggle_pbos()
        imgui.separator()
        _, angle_increment = imgui.slider_float(
            "Animation speed", angle_increment, -10.0, 10.0
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    # Render-option toggles moved to the imgui panel; only Esc remains
    # (this demo has no camera navigation).
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(
        window_width, window_height, "Pixel Buffer Object Demo", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    print("Pixel Buffer Object Demo")
    print("  Esc: quit")

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    frame_count = 0
    last_t = time.time()
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        render_scene()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)
        frame_count += 1
        if frame_count == 100:
            now = time.time()
            fps = 100.0 / (now - last_t)
            label = "with PBOs" if use_pbos else "without PBOs"
            glfw.set_window_title(window, f"Draw scene {label} {fps:.1f} fps")
            last_t = now
            frame_count = 0
    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
