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

# Demo 22 -- "3D Effects" / Block.
# Ported from OpenGL SuperBible 4e, chapter 1 example "Block".  Pick
# one of six progressively-more-realistic renderings of the same scene
# from the imgui control panel:
#
#   step 0:  wireframe cube (every edge drawn)
#   step 1:  solid uniform-colour cube (looks 2-D and goofy)
#   step 2:  same cube, with a directional light + Lambert shading
#   step 3:  lit cube + planar shadow on the floor
#   step 4:  textured cube + textured floor + shadow
#
# Implementation notes:
#
# * OpenGL 3.3 core profile.  No fixed-function lighting/texturing --
#   every stage goes through the same shader pair (block.vert /
#   block.frag) with different uniforms.
# * The "planar shadow" is a real linear transformation:  a 4x4 matrix
#   that flattens any point onto the floor plane along the light
#   direction.  See `planar_shadow_matrix` below.
# * The view rotation starts at +30 degrees about X and -30 degrees
#   about Y, matching the SuperBible original on the first frame.
#
# Controls:
#   ImGui panel            -- pick which stage to render
#   LEFT / RIGHT           -- yaw the camera
#   PAGE_UP / PAGE_DOWN    -- pitch the camera
#   UP / DOWN              -- walk forward / backward (camera relative)
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
    600, 600, "ModelViewProjection Demo 22 -- 3D Effects",
    None, None,
)
if not window:
    glfw.terminate()
    sys.exit()
glfw.make_context_current(window)


# ImGui setup -- mirrors the pattern used in demo21.
imgui.create_context()
impl = GlfwRenderer(window)


n_step: int = 0
STAGE_LABELS: list[str] = [
    "0  --  wireframe",
    "1  --  solid (no lighting)",
    "2  --  solid + Lambert lighting",
    "3  --  lit + planar shadow",
    "4  --  textured + lit + shadow",
]


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


# Setting our key callback after GlfwRenderer was constructed replaces
# the renderer's default keyboard handler.  That is fine here -- we
# only need the mouse to interact with the imgui radio buttons, and
# GlfwRenderer's mouse callbacks were installed separately and remain
# in place.
glfw.set_key_callback(window, on_key)


@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


# Initial pose:  position the camera so the cube and floor are visible
# at roughly the same angle as the SuperBible original (+30 deg X,
# -30 deg Y baked into the world).  Re-deriving:  the world rotation
# R_x(30) * R_y(-30) is equivalent to a camera with yaw = +30, pitch =
# -30 looking back along that direction.  Distance ~100 from the cube.
camera: Camera = Camera(
    x=40.0,
    y=43.0,
    z=85.0,
    rot_y=math.radians(30.0),
    rot_x=math.radians(-30.0),
)


def handle_inputs() -> None:
    """Same control scheme as demos 19 and 21:
       LEFT/RIGHT yaw, PAGE_UP/PAGE_DOWN pitch, UP/DOWN walk."""
    global camera
    move_step: float = 2.0  # scene units; cube is 50 units across

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


GL.glClearColor(0.0, 0.0, 0.0, 1.0)
GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)
#GL.glLineWidth(2)


# ---------------------------------------------------------------------------
# Shader program
# ---------------------------------------------------------------------------


def compile_shader_program() -> int:
    with open(os.path.join(pwd, "block.vert")) as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, "block.frag")) as f:
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
    """Push the current pyMatrixStack matrices into the bound program."""
    GL.glUniformMatrix4fv(
        u_mvp,
        1,
        GL.GL_TRUE,  # row-major, since pyMatrixStack stores row-major
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
            dtype=np.float32,
        ),
    )
    GL.glUniformMatrix4fv(
        u_model,
        1,
        GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.model),
            dtype=np.float32,
        ),
    )


# ---------------------------------------------------------------------------
# Texture loading
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
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
    )
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D,
        0,
        GL.GL_RGB8,
        w,
        h,
        0,
        GL.GL_RGB,
        GL.GL_UNSIGNED_BYTE,
        img,
    )
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    return tex


tex_floor = load_texture(os.path.join(pwd, "floor.tga"))
tex_block_front = load_texture(os.path.join(pwd, "Block4.tga"))
tex_block_top = load_texture(os.path.join(pwd, "Block5.tga"))
tex_block_right = load_texture(os.path.join(pwd, "Block6.tga"))


# ---------------------------------------------------------------------------
# Geometry helpers.  Each VAO uses three attributes:
#   location 0: position (vec3)
#   location 1: normal   (vec3)   -- ignored when lighting is off
#   location 2: texcoord (vec2)   -- ignored when texturing is off
# Wireframe VAOs put zeros in normal/texcoord since they are unused.
# ---------------------------------------------------------------------------


_FLOATS_PER_VERTEX = 8  # 3 pos + 3 normal + 2 uv
_STRIDE = _FLOATS_PER_VERTEX * 4


def make_vao(vertex_data: np.ndarray) -> tuple[int, int, int]:
    """Build a VAO + VBO for an interleaved [pos3, normal3, uv2] array.
    Returns (vao, vbo, vertex_count).
    """
    vertex_data = np.ascontiguousarray(vertex_data, dtype=np.float32)
    vao = GL.glGenVertexArrays(1)
    vbo = GL.glGenBuffers(1)

    GL.glBindVertexArray(vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER,
        vertex_data.nbytes,
        vertex_data,
        GL.GL_STATIC_DRAW,
    )

    # position
    GL.glEnableVertexAttribArray(0)
    GL.glVertexAttribPointer(
        0, 3, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(0)
    )
    # normal
    GL.glEnableVertexAttribArray(1)
    GL.glVertexAttribPointer(
        1, 3, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(12)
    )
    # texcoord
    GL.glEnableVertexAttribArray(2)
    GL.glVertexAttribPointer(
        2, 2, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(24)
    )

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glBindVertexArray(0)

    return vao, vbo, vertex_data.size // _FLOATS_PER_VERTEX


# Cube geometry --------------------------------------------------------------
#
# 8 corners of a 50x50x50 cube centered on the origin, then 6 faces, each
# with a single outward normal and the same 0..1 texcoord square.  Faces
# are laid out in this order (matters for stage 5 which textures a subset
# of faces):
#
#   face 0  +Z (front)
#   face 1  -Z (back)
#   face 2  +Y (top)
#   face 3  -Y (bottom)
#   face 4  +X (right)
#   face 5  -X (left)


def _build_cube_solid() -> np.ndarray:
    s = 25.0
    # for each face: 4 corner positions (CCW from outside), then a single
    # outward normal, then the corresponding 4 uv coords.
    faces = [
        # +Z
        (
            [(-s, -s, +s), (+s, -s, +s), (+s, +s, +s), (-s, +s, +s)],
            (0.0, 0.0, 1.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # -Z
        (
            [(+s, -s, -s), (-s, -s, -s), (-s, +s, -s), (+s, +s, -s)],
            (0.0, 0.0, -1.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # +Y
        (
            [(-s, +s, +s), (+s, +s, +s), (+s, +s, -s), (-s, +s, -s)],
            (0.0, 1.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # -Y
        (
            [(-s, -s, -s), (+s, -s, -s), (+s, -s, +s), (-s, -s, +s)],
            (0.0, -1.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # +X
        (
            [(+s, -s, +s), (+s, -s, -s), (+s, +s, -s), (+s, +s, +s)],
            (1.0, 0.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # -X
        (
            [(-s, -s, -s), (-s, -s, +s), (-s, +s, +s), (-s, +s, -s)],
            (-1.0, 0.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
    ]

    out: list[float] = []
    for corners, normal, uvs in faces:
        # two triangles per face: (0,1,2) and (0,2,3)
        for i in (0, 1, 2, 0, 2, 3):
            out.extend(corners[i])
            out.extend(normal)
            out.extend(uvs[i])
    return np.array(out, dtype=np.float32)


def _build_cube_wire_full() -> np.ndarray:
    s = 25.0
    corners = [
        (-s, -s, -s), (+s, -s, -s), (+s, +s, -s), (-s, +s, -s),  # back face
        (-s, -s, +s), (+s, -s, +s), (+s, +s, +s), (-s, +s, +s),  # front face
    ]
    edges = [
        # back face
        (0, 1), (1, 2), (2, 3), (3, 0),
        # front face
        (4, 5), (5, 6), (6, 7), (7, 4),
        # connecting edges
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    out: list[float] = []
    for a, b in edges:
        for ci in (a, b):
            out.extend(corners[ci])
            out.extend((0.0, 0.0, 0.0))  # unused normal
            out.extend((0.0, 0.0))       # unused uv
    return np.array(out, dtype=np.float32)


cube_solid_vao, _, cube_solid_count = make_vao(_build_cube_solid())
cube_wire_vao, _, cube_wire_count = make_vao(_build_cube_wire_full())


# Floor geometry -------------------------------------------------------------

FLOOR_Y = -25.3


def _build_floor() -> np.ndarray:
    e = 100.0
    y = FLOOR_Y
    # CCW seen from above (+Y normal)
    corners = [(-e, y, -e), (-e, y, +e), (+e, y, +e), (+e, y, -e)]
    uvs = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
    n = (0.0, 1.0, 0.0)
    out: list[float] = []
    for i in (0, 1, 2, 0, 2, 3):
        out.extend(corners[i])
        out.extend(n)
        out.extend(uvs[i])
    return np.array(out, dtype=np.float32)


floor_vao, _, floor_count = make_vao(_build_floor())


# ---------------------------------------------------------------------------
# Lighting + planar shadow constants
# ---------------------------------------------------------------------------


# matches the SuperBible original (-80, 120, 100, 0):  a directional light.
LIGHT_DIR_WS = np.array([-80.0, 120.0, 100.0], dtype=np.float32)
LIGHT_DIR_WS = LIGHT_DIR_WS / np.linalg.norm(LIGHT_DIR_WS)

# floor plane equation:  ax + by + cz + d = 0.  Floor is y = FLOOR_Y, so:
FLOOR_PLANE = (0.0, 1.0, 0.0, -FLOOR_Y)


# doc-region-begin planar shadow
def planar_shadow_matrix(plane, light) -> np.matrix:
    """
    Returns a 4x4 matrix that, applied to a world-space point, projects
    that point onto `plane` along the direction (or position) `light`.

    plane: (a, b, c, d) such that a*x + b*y + c*z + d = 0.
    light: (Lx, Ly, Lz, Lw).  Lw == 0 for a directional light.

    This is a singular matrix (determinant zero) -- it collapses 3-space
    onto a 2-D plane, which is exactly what a shadow does.
    """
    a, b, c, d = plane
    lx, ly, lz, lw = light
    dot = a * lx + b * ly + c * lz + d * lw
    return np.matrix(
        [
            [dot - lx * a,    -lx * b,       -lx * c,       -lx * d],
            [-ly * a,         dot - ly * b,  -ly * c,       -ly * d],
            [-lz * a,         -lz * b,       dot - lz * c,  -lz * d],
            [-lw * a,         -lw * b,       -lw * c,       dot - lw * d],
        ],
        dtype=np.float32,
    )
# doc-region-end planar shadow


SHADOW_MATRIX = planar_shadow_matrix(
    FLOOR_PLANE, (*LIGHT_DIR_WS.tolist(), 0.0)
)


# ---------------------------------------------------------------------------
# Per-stage rendering
# ---------------------------------------------------------------------------


def setup_uniforms(
    *,
    use_lighting: bool,
    use_texture: bool,
    flat_color: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> None:
    GL.glUniform1i(u_use_lighting, 1 if use_lighting else 0)
    GL.glUniform1i(u_use_texture, 1 if use_texture else 0)
    GL.glUniform3f(u_flat, *flat_color)
    GL.glUniform3f(u_light_dir, *LIGHT_DIR_WS.tolist())
    GL.glUniform3f(u_ambient, 0.2, 0.2, 0.2)
    GL.glUniform3f(u_diffuse, 0.7, 0.7, 0.7)
    GL.glUniform1i(u_tex, 0)


def draw_floor(stage: int) -> None:
    with ms.push_matrix(ms.MatrixStack.model):
        if stage == 4:
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex_floor)
            setup_uniforms(use_lighting=False, use_texture=True)
        else:
            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(0.0, 0.0, 0.9),
            )
        set_mvp_uniforms()
        GL.glBindVertexArray(floor_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, floor_count)
        GL.glBindVertexArray(0)


def draw_cube(stage: int) -> None:
    """Draw the cube (and, for stages 3/4, its planar shadow)."""

    # All cube drawing happens inside this push so the cube's translation
    # is independent of the floor.
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model, -10.0, 0.0, 10.0)

        if stage == 0:
            # full wireframe
            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(1.0, 0.0, 0.0),
            )
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_wire_vao)
            GL.glDrawArrays(GL.GL_LINES, 0, cube_wire_count)
            GL.glBindVertexArray(0)

        elif stage == 1:
            # solid uniform red -- no lighting, no texture
            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(0.8, 0.0, 0.0),
            )
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)
            GL.glBindVertexArray(0)

        elif stage == 2:
            # lit cube
            setup_uniforms(
                use_lighting=True,
                use_texture=False,
                flat_color=(0.8, 0.0, 0.0),
            )
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)
            GL.glBindVertexArray(0)

        elif stage == 3:
            # lit cube + planar shadow
            setup_uniforms(
                use_lighting=True,
                use_texture=False,
                flat_color=(0.8, 0.0, 0.0),
            )
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)
            GL.glBindVertexArray(0)

        elif stage == 4:
            # textured cube on all six faces + shadow.  Opposite faces
            # share a texture, so the cube looks like a wooden block from
            # any angle.  Face vertex offsets in the solid VAO are 6
            # apart in the order:  +Z, -Z, +Y, -Y, +X, -X.
            faces_to_draw = [
                (tex_block_front, 0),   # +Z front
                (tex_block_front, 6),   # -Z back
                (tex_block_top,   12),  # +Y top
                (tex_block_top,   18),  # -Y bottom
                (tex_block_right, 24),  # +X right
                (tex_block_right, 30),  # -X left
            ]
            setup_uniforms(use_lighting=True, use_texture=True)
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            for tex, off in faces_to_draw:
                GL.glActiveTexture(GL.GL_TEXTURE0)
                GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
                GL.glDrawArrays(GL.GL_TRIANGLES, off, 6)
            GL.glBindVertexArray(0)

    # Shadow pass -- happens *outside* the cube's own translation push so
    # we can re-apply translation after multiplying by the shadow matrix.
    if stage in (3, 4):
        # The shadow polygons end up exactly coplanar with the floor
        # (both at y = -25.3), which makes the depth test flip-flop pixel
        # by pixel -- the classic "z-fighting" flicker.  glPolygonOffset
        # nudges the shadow's depth slightly toward the camera so it
        # reliably wins the depth test against the floor.  Disabling
        # depth writes also stops the shadow's own overlapping faces
        # from fighting each other.
        GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
        GL.glPolygonOffset(-1.0, -1.0)
        GL.glDepthMask(GL.GL_FALSE)

        with ms.push_matrix(ms.MatrixStack.model):
            # shadow operates on world-space points; we need to flatten
            # AFTER the cube is in the world, so pre-multiply: model =
            # SHADOW * translate(-10,0,10).  pyMatrixStack.multiply does
            # current = current * rhs, so doing multiply(SHADOW) then
            # translate(...) yields exactly that.
            ms.multiply(ms.MatrixStack.model, SHADOW_MATRIX)
            ms.translate(ms.MatrixStack.model, -10.0, 0.0, 10.0)

            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(0.0, 0.0, 0.0),
            )
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)
            GL.glBindVertexArray(0)

        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)


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

    # Build the imgui frame.  Always do imgui.new_frame() before any
    # imgui call this frame, and pair it with imgui.render() / impl.render
    # before swapping buffers.
    imgui.new_frame()
    imgui.set_next_window_size(imgui.ImVec2(280, 220), imgui.Cond_.first_use_ever)
    imgui.begin("Rendering stage", True)
    imgui.text("Pick the level of realism:")
    imgui.separator()
    for i, label in enumerate(STAGE_LABELS):
        if imgui.radio_button(label, n_step == i):
            n_step = i
    imgui.end()

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
        near_z=1.0,
        far_z=1000.0,
    )

    # FPS-style camera transform:  inverse of (translate by camera.pos
    # then yaw, then pitch).  Same form as demos 19 and 21.
    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)
    ms.translate(ms.MatrixStack.view, -camera.x, -camera.y, -camera.z)

    GL.glUseProgram(program)
    draw_floor(n_step)
    draw_cube(n_step)
    GL.glUseProgram(0)

    imgui.render()
    impl.render(imgui.get_draw_data())

    glfw.swap_buffers(window)


glfw.terminate()
