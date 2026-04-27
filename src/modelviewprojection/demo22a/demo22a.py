# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

# Demo 22a -- Textured Pyramid.  Ported from OpenGL SuperBible 4e
# chapter 8 example "Pyramid".
#
# This is the gentle introduction to texturing:  one mesh, one texture,
# no shadows.  Demo 22 ("Block") layers lighting + planar shadows + a
# multi-texture cube on top of the same idea -- read this one first.
#
# Implementation notes:
#
# * OpenGL 3.3 core profile, single shader pair (pyramid.vert /
#   pyramid.frag).  The shader has uniforms for "useTexture" and
#   "useLighting" so the same program drives every stage of the
#   imgui control panel.
# * Per-face normals are computed once in Python (see _build_pyramid)
#   from the cross product of two edges, exactly like the SuperBible
#   original called m3dFindNormal().
# * Texture filtering (NEAREST vs LINEAR) is exposed in imgui so
#   students can see the difference between blocky-texel sampling and
#   bilinear interpolation.
#
# Controls:
#   ImGui panel            -- textured / lit / wireframe toggles,
#                             texture filter, ambient/diffuse sliders
#   LEFT / RIGHT           -- yaw the camera
#   PAGE_UP / PAGE_DOWN    -- pitch the camera
#   UP / DOWN              -- walk forward / backward (camera-relative)
#   Q / E                  -- yaw the pyramid (replaces SuperBible
#                             arrow keys, since arrows fly the camera)
#   A / D                  -- pitch the pyramid
#   ESC                    -- quit

import ctypes
import dataclasses
import math
import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

import modelviewprojection.pyMatrixStack as ms

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


# ---------------------------------------------------------------------------
# GLFW + GL 3.3 core context setup
# ---------------------------------------------------------------------------

if not glfw.init():
    sys.exit()

pwd = os.path.dirname(os.path.abspath(__file__))

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)

window = glfw.create_window(
    600, 600, "ModelViewProjection Demo 22a -- Textured Pyramid",
    None, None,
)
if not window:
    glfw.terminate()
    sys.exit()
glfw.make_context_current(window)


imgui.create_context()
impl = GlfwRenderer(window)


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)


GL.glClearColor(0.0, 0.0, 0.0, 1.0)
GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)
GL.glEnable(GL.GL_CULL_FACE)
GL.glFrontFace(GL.GL_CCW)
GL.glCullFace(GL.GL_BACK)


# ---------------------------------------------------------------------------
# Scene state
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


# Pyramid is unit-scale (about 1 wide, 0.8 tall).  Sit the camera back
# a bit and look slightly downward so the pyramid is centered.
camera: Camera = Camera(x=0.0, y=0.4, z=3.0, rot_y=0.0, rot_x=0.0)

pyramid_yaw: float = 0.0
pyramid_pitch: float = 0.0

# imgui-driven toggles -- module level so they survive across frames.
use_texture: bool = True
use_lighting: bool = True
wireframe: bool = False
filter_nearest: bool = False  # False -> GL_LINEAR, True -> GL_NEAREST
ambient: float = 0.25
diffuse: float = 0.75


def handle_inputs() -> None:
    global pyramid_yaw, pyramid_pitch
    move_step: float = 0.05  # pyramid is ~1 unit across

    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera.rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera.rot_x -= 0.03
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.x -= move_step * math.sin(camera.rot_y)
        camera.z -= move_step * math.cos(camera.rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.x += move_step * math.sin(camera.rot_y)
        camera.z += move_step * math.cos(camera.rot_y)

    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        pyramid_yaw += 0.05
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        pyramid_yaw -= 0.05
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        pyramid_pitch += 0.05
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        pyramid_pitch -= 0.05


# ---------------------------------------------------------------------------
# Shader program
# ---------------------------------------------------------------------------


def compile_shader_program() -> int:
    with open(os.path.join(pwd, "pyramid.vert")) as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, "pyramid.frag")) as f:
        fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)
    return shaders.compileProgram(vs, fs)


program: int = compile_shader_program()

u_mvp = GL.glGetUniformLocation(program, "mvpMatrix")
u_model = GL.glGetUniformLocation(program, "modelMatrix")
u_flat = GL.glGetUniformLocation(program, "flatColor")
u_use_lighting = GL.glGetUniformLocation(program, "useLighting")
u_use_texture = GL.glGetUniformLocation(program, "useTexture")
u_light_dir = GL.glGetUniformLocation(program, "lightDirWS")
u_ambient = GL.glGetUniformLocation(program, "ambientColor")
u_diffuse = GL.glGetUniformLocation(program, "diffuseColor")
u_tex = GL.glGetUniformLocation(program, "tex")


def set_mvp_uniforms() -> None:
    GL.glUniformMatrix4fv(
        u_mvp, 1, GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
            dtype=np.float32,
        ),
    )
    GL.glUniformMatrix4fv(
        u_model, 1, GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.model),
            dtype=np.float32,
        ),
    )


# ---------------------------------------------------------------------------
# Texture
# ---------------------------------------------------------------------------


def load_texture(path: str) -> int:
    img = iio.imread(path)
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    h, w = img.shape[:2]
    img = np.ascontiguousarray(img, dtype=np.uint8)

    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
    )
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D, 0, GL.GL_RGB8, w, h, 0,
        GL.GL_RGB, GL.GL_UNSIGNED_BYTE, img,
    )
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    return tex


tex_stone = load_texture(os.path.join(pwd, "stone.tga"))


# ---------------------------------------------------------------------------
# Geometry -- pyramid with per-face normals + uv coords.
#
# Five corners (numbered to match the SuperBible source):
#   0: top
#   1: back-left  base
#   2: back-right base
#   3: front-right base
#   4: front-left base
#
# Six triangles:  two for the square base, four for the slanted sides.
# Each side gets a uv triangle (0.5, 1.0) -> (0, 0) -> (1, 0) so the
# stone texture's apex meets the pyramid's apex.
# ---------------------------------------------------------------------------


_FLOATS_PER_VERTEX = 8  # 3 pos + 3 normal + 2 uv
_STRIDE = _FLOATS_PER_VERTEX * 4


def _face_normal(a, b, c) -> tuple[float, float, float]:
    """Outward normal of triangle (a, b, c) listed counter-clockwise."""
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = c
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / L, ny / L, nz / L)


def _build_pyramid() -> np.ndarray:
    corners = [
        ( 0.0,  0.80,  0.00),  # 0 top
        (-0.5,  0.00, -0.50),  # 1 back-left
        ( 0.5,  0.00, -0.50),  # 2 back-right
        ( 0.5,  0.00,  0.50),  # 3 front-right
        (-0.5,  0.00,  0.50),  # 4 front-left
    ]

    # base normal points down, two triangles cover the square.  uv
    # tiles the stone texture once across the base.
    base_n = (0.0, -1.0, 0.0)
    triangles = [
        # base (CCW from below, so normal faces -Y)
        (corners[2], corners[4], corners[1], base_n,
         [(1, 1), (0, 0), (0, 1)]),
        (corners[2], corners[3], corners[4], base_n,
         [(1, 1), (1, 0), (0, 0)]),
        # front face (apex, front-left, front-right)
        (corners[0], corners[4], corners[3],
         _face_normal(corners[0], corners[4], corners[3]),
         [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)]),
        # left face (apex, back-left, front-left)
        (corners[0], corners[1], corners[4],
         _face_normal(corners[0], corners[1], corners[4]),
         [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)]),
        # back face (apex, back-right, back-left)
        (corners[0], corners[2], corners[1],
         _face_normal(corners[0], corners[2], corners[1]),
         [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)]),
        # right face (apex, front-right, back-right)
        (corners[0], corners[3], corners[2],
         _face_normal(corners[0], corners[3], corners[2]),
         [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)]),
    ]

    out: list[float] = []
    for a, b, c, n, uvs in triangles:
        for vert, uv in zip((a, b, c), uvs):
            out.extend(vert)
            out.extend(n)
            out.extend(uv)
    return np.array(out, dtype=np.float32)


def _build_pyramid_wire() -> np.ndarray:
    corners = [
        ( 0.0,  0.80,  0.00),
        (-0.5,  0.00, -0.50),
        ( 0.5,  0.00, -0.50),
        ( 0.5,  0.00,  0.50),
        (-0.5,  0.00,  0.50),
    ]
    edges = [
        # base
        (1, 2), (2, 3), (3, 4), (4, 1),
        # apex to each base corner
        (0, 1), (0, 2), (0, 3), (0, 4),
    ]
    out: list[float] = []
    for a, b in edges:
        for ci in (a, b):
            out.extend(corners[ci])
            out.extend((0.0, 0.0, 0.0))
            out.extend((0.0, 0.0))
    return np.array(out, dtype=np.float32)


def make_vao(vertex_data: np.ndarray) -> tuple[int, int, int]:
    vertex_data = np.ascontiguousarray(vertex_data, dtype=np.float32)
    vao = GL.glGenVertexArrays(1)
    vbo = GL.glGenBuffers(1)
    GL.glBindVertexArray(vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL.GL_STATIC_DRAW
    )
    GL.glEnableVertexAttribArray(0)
    GL.glVertexAttribPointer(
        0, 3, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(0)
    )
    GL.glEnableVertexAttribArray(1)
    GL.glVertexAttribPointer(
        1, 3, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(12)
    )
    GL.glEnableVertexAttribArray(2)
    GL.glVertexAttribPointer(
        2, 2, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(24)
    )
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glBindVertexArray(0)
    return vao, vbo, vertex_data.size // _FLOATS_PER_VERTEX


pyramid_vao, pyramid_vbo, pyramid_count = make_vao(_build_pyramid())
wire_vao, wire_vbo, wire_count = make_vao(_build_pyramid_wire())


# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------

# SuperBible original used a positional light at (-10, 5, 5).  We use
# the same direction as a directional light so the shader matches demo22.
LIGHT_DIR_WS = np.array([-10.0, 5.0, 5.0], dtype=np.float32)
LIGHT_DIR_WS = LIGHT_DIR_WS / np.linalg.norm(LIGHT_DIR_WS)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

TARGET_FRAMERATE: int = 60
time_at_beginning_of_previous_frame: float = glfw.get_time()

while not glfw.window_should_close(window):
    while (
        glfw.get_time()
        < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass
    time_at_beginning_of_previous_frame = glfw.get_time()

    glfw.poll_events()
    impl.process_inputs()
    handle_inputs()

    imgui.new_frame()
    imgui.set_next_window_size(
        imgui.ImVec2(300, 260), imgui.Cond_.first_use_ever
    )
    imgui.begin("Pyramid", True)
    _, use_texture = imgui.checkbox("Textured", use_texture)
    _, use_lighting = imgui.checkbox("Lit", use_lighting)
    _, wireframe = imgui.checkbox("Wireframe", wireframe)
    imgui.separator()
    imgui.text("Texture filter:")
    if imgui.radio_button("Linear (smooth)", not filter_nearest):
        filter_nearest = False
    if imgui.radio_button("Nearest (blocky)", filter_nearest):
        filter_nearest = True
    imgui.separator()
    _, ambient = imgui.slider_float("Ambient", ambient, 0.0, 1.0)
    _, diffuse = imgui.slider_float("Diffuse", diffuse, 0.0, 1.0)
    imgui.end()

    # Apply the imgui-selected texture filter (cheap; just sets two
    # parameters on the bound texture object).
    flt = GL.GL_NEAREST if filter_nearest else GL.GL_LINEAR
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex_stone)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, flt)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, flt)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    aspect = float(width) / float(height) if height > 0 else 1.0
    ms.perspective(
        field_of_view=45.0,
        aspect_ratio=aspect,
        near_z=0.1,
        far_z=40.0,
    )

    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)
    ms.translate(ms.MatrixStack.view, -camera.x, -camera.y, -camera.z)

    GL.glUseProgram(program)
    GL.glUniform3f(u_light_dir, *LIGHT_DIR_WS.tolist())
    GL.glUniform3f(u_ambient, ambient, ambient, ambient)
    GL.glUniform3f(u_diffuse, diffuse, diffuse, diffuse)
    GL.glUniform1i(u_tex, 0)

    with ms.push_matrix(ms.MatrixStack.model):
        ms.rotate_y(ms.MatrixStack.model, pyramid_yaw)
        ms.rotate_x(ms.MatrixStack.model, pyramid_pitch)

        if wireframe:
            GL.glUniform1i(u_use_lighting, 0)
            GL.glUniform1i(u_use_texture, 0)
            GL.glUniform3f(u_flat, 1.0, 1.0, 0.0)
            set_mvp_uniforms()
            GL.glBindVertexArray(wire_vao)
            GL.glDrawArrays(GL.GL_LINES, 0, wire_count)
            GL.glBindVertexArray(0)
        else:
            GL.glUniform1i(u_use_lighting, 1 if use_lighting else 0)
            GL.glUniform1i(u_use_texture, 1 if use_texture else 0)
            GL.glUniform3f(u_flat, 0.8, 0.6, 0.4)  # sandstone fallback
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex_stone)
            set_mvp_uniforms()
            GL.glBindVertexArray(pyramid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, pyramid_count)
            GL.glBindVertexArray(0)

    GL.glUseProgram(0)

    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)


# Clean up GL resources before tearing down the context.
GL.glBindVertexArray(0)
GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
GL.glUseProgram(0)
GL.glDeleteVertexArrays(1, [pyramid_vao])
GL.glDeleteVertexArrays(1, [wire_vao])
GL.glDeleteBuffers(1, [pyramid_vbo])
GL.glDeleteBuffers(1, [wire_vbo])
GL.glDeleteTextures(1, [tex_stone])
GL.glDeleteProgram(program)

glfw.terminate()
