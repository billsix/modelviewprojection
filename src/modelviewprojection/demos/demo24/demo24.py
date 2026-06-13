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

# Demo 24 -- SphereWorld.  Ported from OpenGL SuperBible 4e chapter 9
# example "sphereworld" (the textured + shadowed version).
#
# This is the capstone for the 3.3-Core arc:  it pulls together every
# concept the previous demos established and runs them all at once.
#
#     demo16  -- 3D and depth
#     demo19e -- FPS-style camera over a flat ground plane
#     demo20+ -- shaders
#     demo22  -- Lambert lighting, textures, planar shadows
#     demo23  -- Blinn-Phong + complex hand-built mesh + per-face normals
#
# What's new here:
#
# * Procedural meshes -- a UV sphere and a torus generated in Python
#   from parametric formulas (no hand-coded triangle list, unlike the
#   jet in demo23 or the cube in demo22).
# * Many lit instances -- 30 randomly placed spheres, a rotating torus,
#   and a small orbiting sphere, all sharing one shader and lighting
#   setup.  Each gets its own model matrix via pyMatrixStack.
# * Stencil-buffered planar shadows -- the shadow projection happens
#   on the CPU as a 4x4 matrix multiplied into the model stack
#   *before* each actor's local transform, so the same VBOs draw a
#   second time as their flattened silhouettes.  The stencil buffer
#   prevents overlapping shadows from double-darkening.
# * Ground texture wrap mode -- grass.tga uses GL_REPEAT so the floor
#   can tile a small texture across a 40x40 unit plane, while the orb
#   and wood textures use CLAMP_TO_EDGE like demo22a's stone.
#
# Controls:
#   ImGui panel            -- shadows / lighting / wireframe toggles,
#                             ambient / diffuse / specular sliders,
#                             shininess
#   LEFT / RIGHT           -- yaw the camera
#   PAGE_UP / PAGE_DOWN    -- pitch the camera
#   UP / DOWN              -- walk forward / backward (camera-relative)
#   ESC                    -- quit

import ctypes
import dataclasses
import math
import os
import random
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

import modelviewprojection.pyMatrixStack as ms
from modelviewprojection.util.cameracontrols import walk_around_camera
from modelviewprojection.util.windowing import on_key

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
# Stencil bits are the unusual ask:  the planar shadow pass uses the
# stencil buffer so overlapping shadows don't double-darken.
glfw.window_hint(glfw.STENCIL_BITS, 8)

window = glfw.create_window(
    800,
    600,
    "ModelViewProjection Demo 24 -- SphereWorld",
    None,
    None,
)
if not window:
    glfw.terminate()
    sys.exit()
glfw.make_context_current(window)


imgui.create_context()
impl = GlfwRenderer(window)


glfw.set_key_callback(window, on_key)


# Grayish sky -- matches SuperBible's fLowLight (0.25, 0.25, 0.25, 1).
GL.glClearColor(0.25, 0.25, 0.25, 1.0)
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


# Stand at the origin looking down the -Z axis, eye height ~0 (the
# ground is at y=-0.4 so this puts us about 0.4 units above it).
camera: Camera = Camera(x=0.0, y=0.0, z=0.0, rot_y=0.0, rot_x=0.0)

# imgui state -- module level so it survives across frames.
shadows_on: bool = True
lighting_on: bool = True
wireframe: bool = False
ambient: float = 0.25  # SuperBible fLowLight
diffuse: float = 1.0  # SuperBible fBrightLight
specular: float = 1.0
shininess: float = 128.0  # SuperBible glMateriali(..., 128)

# Light position is parameterized by spherical coordinates around the
# world origin so it can be slid around at runtime.  Defaults put the
# light low and in front of the camera (camera starts at origin
# looking down -Z) so the yellow marker is visible from frame 1, and
# the low elevation casts long visible shadows -- both points the
# students should notice.  The SuperBible original was higher and
# behind the camera at (-100, 100, 50); slide the sliders to recreate.
light_az_deg: float = 270.0  # 0 = +X, 90 = +Z, 180 = -X, 270 = -Z
light_el_deg: float = 15.0  # angle above the XZ plane
light_distance: float = 60.0  # distance from origin


def handle_inputs() -> None:
    walk_around_camera(window, camera, move_step=0.1)


# ---------------------------------------------------------------------------
# Shader program
# ---------------------------------------------------------------------------


def compile_shader_program() -> int:
    with open(os.path.join(pwd, "sphereworld.vert")) as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, "sphereworld.frag")) as f:
        fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)
    return shaders.compileProgram(vs, fs)


program: int = compile_shader_program()

u_mvp = GL.glGetUniformLocation(program, "mvpMatrix")
u_model = GL.glGetUniformLocation(program, "modelMatrix")
u_base = GL.glGetUniformLocation(program, "baseColor")
u_camera_pos = GL.glGetUniformLocation(program, "cameraPosWS")
u_light_pos = GL.glGetUniformLocation(program, "lightPosWS")
u_ambient = GL.glGetUniformLocation(program, "ambientColor")
u_diffuse = GL.glGetUniformLocation(program, "diffuseColor")
u_specular = GL.glGetUniformLocation(program, "specularColor")
u_shininess = GL.glGetUniformLocation(program, "shininess")
u_render_mode = GL.glGetUniformLocation(program, "renderMode")
u_tex = GL.glGetUniformLocation(program, "tex")


def set_mvp_uniforms() -> None:
    GL.glUniformMatrix4fv(
        u_mvp,
        1,
        GL.GL_TRUE,
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


def load_texture(path: str, repeat: bool) -> int:
    img = iio.imread(path)
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    h, w = img.shape[:2]
    img = np.ascontiguousarray(img, dtype=np.uint8)

    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    wrap = GL.GL_REPEAT if repeat else GL.GL_CLAMP_TO_EDGE
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, wrap)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, wrap)
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR
    )
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    channels = img.shape[2]
    fmt = GL.GL_RGB if channels == 3 else GL.GL_RGBA
    internal = GL.GL_RGB8 if channels == 3 else GL.GL_RGBA8
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D,
        0,
        internal,
        w,
        h,
        0,
        fmt,
        GL.GL_UNSIGNED_BYTE,
        img,
    )
    GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    return tex


tex_grass = load_texture(os.path.join(pwd, "grass.tga"), repeat=True)
tex_wood = load_texture(os.path.join(pwd, "wood.tga"), repeat=False)
tex_orb = load_texture(os.path.join(pwd, "orb.tga"), repeat=False)


# ---------------------------------------------------------------------------
# Procedural meshes
#
# Each generator returns an interleaved float32 array:
#   pos.x  pos.y  pos.z   nrm.x  nrm.y  nrm.z   uv.s  uv.t
# (8 floats per vertex, same layout as demo22a so make_vao() works
# unchanged.)
#
# Winding for back-face culling (front = CCW from outside the surface):
#   sphere uses (p00, p10, p01) + (p10, p11, p01)
#   torus  uses (p00, p01, p10) + (p10, p01, p11)
#   ground uses (p00, p01, p10) + (p10, p01, p11)
# The difference comes from the parameterizations:  for the sphere
# dr/du x dr/dv already points outward, while the torus and ground
# parameterizations have it pointing the wrong way, so we swap.
# ---------------------------------------------------------------------------

_FLOATS_PER_VERTEX = 8
_STRIDE = _FLOATS_PER_VERTEX * 4


def _build_sphere(radius: float, slices: int, stacks: int) -> np.ndarray:
    out: list[float] = []
    for i in range(stacks):
        v0 = i / stacks
        v1 = (i + 1) / stacks
        phi0 = math.pi * v0 - math.pi / 2.0  # -pi/2 (south) .. pi/2 (north)
        phi1 = math.pi * v1 - math.pi / 2.0
        cphi0, sphi0 = math.cos(phi0), math.sin(phi0)
        cphi1, sphi1 = math.cos(phi1), math.sin(phi1)
        for j in range(slices):
            u0 = j / slices
            u1 = (j + 1) / slices
            t0 = 2.0 * math.pi * u0
            t1 = 2.0 * math.pi * u1
            ct0, st0 = math.cos(t0), math.sin(t0)
            ct1, st1 = math.cos(t1), math.sin(t1)

            # Four corners of this latitude/longitude quad.  Normal
            # equals the unit-radius position (it's a sphere).
            p00 = (
                (cphi0 * st0, sphi0, cphi0 * ct0),
                (cphi0 * st0, sphi0, cphi0 * ct0),
                (u0, v0),
            )
            p10 = (
                (cphi0 * st1, sphi0, cphi0 * ct1),
                (cphi0 * st1, sphi0, cphi0 * ct1),
                (u1, v0),
            )
            p01 = (
                (cphi1 * st0, sphi1, cphi1 * ct0),
                (cphi1 * st0, sphi1, cphi1 * ct0),
                (u0, v1),
            )
            p11 = (
                (cphi1 * st1, sphi1, cphi1 * ct1),
                (cphi1 * st1, sphi1, cphi1 * ct1),
                (u1, v1),
            )

            for vert in (p00, p10, p01, p10, p11, p01):
                pos, nrm, uv = vert
                out.extend(p * radius for p in pos)
                out.extend(nrm)
                out.extend(uv)
    return np.array(out, dtype=np.float32)


def _build_torus(R: float, r: float, sides: int, rings: int) -> np.ndarray:
    """Torus around the Y axis.  R = major radius (center of tube to
    Y axis), r = minor radius (tube thickness).  sides = segments
    around the major ring, rings = segments around the minor ring."""
    out: list[float] = []
    for i in range(sides):
        u0 = i / sides * 2.0 * math.pi
        u1 = (i + 1) / sides * 2.0 * math.pi
        cu0, su0 = math.cos(u0), math.sin(u0)
        cu1, su1 = math.cos(u1), math.sin(u1)
        for j in range(rings):
            v0 = j / rings * 2.0 * math.pi
            v1 = (j + 1) / rings * 2.0 * math.pi
            cv0, sv0 = math.cos(v0), math.sin(v0)
            cv1, sv1 = math.cos(v1), math.sin(v1)

            def vert(cu, su, cv, sv, us, vs):
                pos = ((R + r * cv) * cu, r * sv, (R + r * cv) * su)
                nrm = (cv * cu, sv, cv * su)
                return (pos, nrm, (us, vs))

            p00 = vert(cu0, su0, cv0, sv0, i / sides, j / rings)
            p01 = vert(cu0, su0, cv1, sv1, i / sides, (j + 1) / rings)
            p10 = vert(cu1, su1, cv0, sv0, (i + 1) / sides, j / rings)
            p11 = vert(cu1, su1, cv1, sv1, (i + 1) / sides, (j + 1) / rings)

            for v in (p00, p01, p10, p10, p01, p11):
                pos, nrm, uv = v
                out.extend(pos)
                out.extend(nrm)
                out.extend(uv)
    return np.array(out, dtype=np.float32)


def _build_ground(
    extent: float, step: float, y: float, tex_step: float
) -> np.ndarray:
    """Flat XZ grid at height y.  Normal points +Y everywhere.  UVs
    increment by tex_step per cell so the (REPEAT-wrapped) texture
    tiles."""
    out: list[float] = []
    n_cells = int(round((2 * extent) / step))
    for i in range(n_cells):
        x0 = -extent + i * step
        x1 = x0 + step
        s0 = i * tex_step
        s1 = s0 + tex_step
        for j in range(n_cells):
            z0 = -extent + j * step
            z1 = z0 + step
            t0 = j * tex_step
            t1 = t0 + tex_step

            p00 = ((x0, y, z0), (0.0, 1.0, 0.0), (s0, t0))
            p10 = ((x1, y, z0), (0.0, 1.0, 0.0), (s1, t0))
            p01 = ((x0, y, z1), (0.0, 1.0, 0.0), (s0, t1))
            p11 = ((x1, y, z1), (0.0, 1.0, 0.0), (s1, t1))

            for v in (p00, p01, p10, p10, p01, p11):
                pos, nrm, uv = v
                out.extend(pos)
                out.extend(nrm)
                out.extend(uv)
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


# Sphere big = inhabitant (radius 0.3, SuperBible gltDrawSphere(0.3, 21, 11))
# Sphere small = orbiter (radius 0.1, gltDrawSphere(0.1, 21, 11))
# Torus = (R 0.35, r 0.15, gltDrawTorus(0.35, 0.15, 61, 37))
sphere_big_vao, sphere_big_vbo, sphere_big_count = make_vao(
    _build_sphere(0.3, 21, 11)
)
sphere_small_vao, sphere_small_vbo, sphere_small_count = make_vao(
    _build_sphere(0.1, 21, 11)
)
torus_vao, torus_vbo, torus_count = make_vao(_build_torus(0.35, 0.15, 61, 37))

# Ground:  40-unit-wide grid centered on origin, 1-unit cells, at
# y=-0.4 (matches SuperBible).  texStep = 1/(20*0.075) ≈ 0.667 per
# cell, so the grass texture tiles ~30 times across the floor.
GROUND_Y = -0.4
GROUND_EXTENT = 20.0
ground_vao, ground_vbo, ground_count = make_vao(
    _build_ground(GROUND_EXTENT, 1.0, GROUND_Y, 1.0 / (GROUND_EXTENT * 0.075))
)


# ---------------------------------------------------------------------------
# Random sphere placements
#
# Fixed seed so the layout is stable across runs (the SuperBible used
# rand() with no seed, which on many libcs gives the same sequence
# anyway -- but Python's random is independent of that, so we pin it).
# ---------------------------------------------------------------------------

_rng = random.Random(42)
NUM_INHABITANTS = 30
sphere_origins: list[tuple[float, float, float]] = []
for _ in range(NUM_INHABITANTS):
    sphere_origins.append(
        (
            ((_rng.randint(0, 399)) - 200) * 0.1,
            0.0,
            ((_rng.randint(0, 399)) - 200) * 0.1,
        )
    )


# ---------------------------------------------------------------------------
# Lighting & shadow projection
# ---------------------------------------------------------------------------


def light_position_ws(
    az_deg: float, el_deg: float, distance: float
) -> tuple[float, float, float]:
    """Spherical -> Cartesian.  azimuth=0 is along +X; positive azimuth
    rotates toward +Z (counter-clockwise looking down from +Y).
    elevation=0 is on the XZ plane; positive elevation lifts toward
    +Y."""
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    return (
        distance * math.cos(el) * math.cos(az),
        distance * math.sin(el),
        distance * math.cos(el) * math.sin(az),
    )


def planar_shadow_matrix(
    plane: tuple[float, float, float, float],
    light: tuple[float, float, float, float],
) -> np.ndarray:
    """Return the 4x4 matrix that projects world-space points onto the
    given plane (a*x + b*y + c*z + d = 0) along rays from the light
    position.

    Standard form:  M = (n . L) * I - L * n^T,  where n=(a,b,c,d)
    and L=(Lx,Ly,Lz,Lw).  Stored row-major like np.matrix expects."""
    a, b, c, d = plane
    Lx, Ly, Lz, Lw = light
    dot = a * Lx + b * Ly + c * Lz + d * Lw
    return np.array(
        [
            [dot - a * Lx, -b * Lx, -c * Lx, -d * Lx],
            [-a * Ly, dot - b * Ly, -c * Ly, -d * Ly],
            [-a * Lz, -b * Lz, dot - c * Lz, -d * Lz],
            [-a * Lw, -b * Lw, -c * Lw, dot - d * Lw],
        ],
        dtype=np.float64,
    )


# Ground plane y = GROUND_Y, normal +Y, so 0*x + 1*y + 0*z + (-GROUND_Y) = 0
# i.e. plane = (0, 1, 0, 0.4).  Light position is recomputed each
# frame from the imgui sliders, so the shadow matrix is too.
GROUND_PLANE = (0.0, 1.0, 0.0, -GROUND_Y)

# Yellow ball drawn at the light's location (chapt05/shadow.cpp:272).
# Origin's small sphere mesh is radius 0.1; we scale it 20x in the
# model matrix so it's visible from across the world (radius 2.0).
LIGHT_MARKER_SCALE: float = 20.0
LIGHT_MARKER_COLOR: tuple[float, float, float] = (1.0, 1.0, 0.0)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def _bind_and_draw(vao: int, count: int, mode=GL.GL_TRIANGLES) -> None:
    GL.glBindVertexArray(vao)
    GL.glDrawArrays(mode, 0, count)
    GL.glBindVertexArray(0)


def draw_inhabitants(yrot: float) -> None:
    """Draw the 30 spheres + the rotating torus/orbiter pair.  Caller
    has already set renderMode + texture binding state appropriate to
    either the lit or shadow pass."""
    # Scattered spheres -- orb texture.
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex_orb)
    for ox, oy, oz in sphere_origins:
        with ms.push_matrix(ms.MatrixStack.model):
            ms.translate(ms.MatrixStack.model, ox, oy, oz)
            set_mvp_uniforms()
            _bind_and_draw(sphere_big_vao, sphere_big_count)

    # Torus + orbiting small sphere, sitting at (0, 0.1, -2.5).
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model, 0.0, 0.1, -2.5)

        # Small orbiter:  -2*yrot about Y, then translate +1 along X.
        # Bound texture is still tex_orb from the loop above.
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_y(ms.MatrixStack.model, -2.0 * yrot)
            ms.translate(ms.MatrixStack.model, 1.0, 0.0, 0.0)
            set_mvp_uniforms()
            _bind_and_draw(sphere_small_vao, sphere_small_count)

        # Torus:  yrot about Y, wood texture.
        ms.rotate_y(ms.MatrixStack.model, yrot)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_wood)
        set_mvp_uniforms()
        _bind_and_draw(torus_vao, torus_count)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

TARGET_FRAMERATE: int = 60
time_at_beginning_of_previous_frame: float = glfw.get_time()
start_time: float = glfw.get_time()

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

    # Animation tied to wall clock so the scene moves at a consistent
    # speed regardless of frame rate.  SuperBible original was 0.5
    # degrees per 33ms ≈ 15 deg/sec ≈ 0.26 rad/sec.
    yrot = (glfw.get_time() - start_time) * 0.26

    imgui.new_frame()
    imgui.set_next_window_size(
        imgui.ImVec2(300, 280), imgui.Cond_.first_use_ever
    )
    imgui.set_next_window_size(
        imgui.ImVec2(320, 360), imgui.Cond_.first_use_ever
    )
    imgui.begin("SphereWorld", True)
    _, shadows_on = imgui.checkbox("Shadows", shadows_on)
    _, lighting_on = imgui.checkbox("Lighting", lighting_on)
    _, wireframe = imgui.checkbox("Wireframe", wireframe)
    imgui.separator()
    imgui.text("Light position (yellow ball):")
    _, light_az_deg = imgui.slider_float(
        "Azimuth (deg)", light_az_deg, 0.0, 360.0
    )
    _, light_el_deg = imgui.slider_float(
        "Elevation (deg)", light_el_deg, 5.0, 89.0
    )
    _, light_distance = imgui.slider_float(
        "Distance", light_distance, 20.0, 200.0
    )
    imgui.separator()
    _, ambient = imgui.slider_float("Ambient", ambient, 0.0, 1.0)
    _, diffuse = imgui.slider_float("Diffuse", diffuse, 0.0, 1.0)
    _, specular = imgui.slider_float("Specular", specular, 0.0, 1.0)
    _, shininess = imgui.slider_float("Shininess", shininess, 1.0, 256.0)
    imgui.end()

    light_pos = light_position_ws(light_az_deg, light_el_deg, light_distance)
    shadow_matrix = planar_shadow_matrix(
        GROUND_PLANE, (light_pos[0], light_pos[1], light_pos[2], 1.0)
    )

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClearStencil(0)
    GL.glClear(
        GL.GL_COLOR_BUFFER_BIT  # ty: ignore[unsupported-operator]
        | GL.GL_DEPTH_BUFFER_BIT
        | GL.GL_STENCIL_BUFFER_BIT
    )

    GL.glPolygonMode(
        GL.GL_FRONT_AND_BACK, GL.GL_LINE if wireframe else GL.GL_FILL
    )

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    aspect = float(width) / float(height) if height > 0 else 1.0
    ms.perspective(
        field_of_view=35.0,  # SuperBible used 35 degrees
        aspect_ratio=aspect,
        near_z=0.1,
        # Far plane has to contain the light marker even when the
        # imgui slider pushes it out to distance 200 and the camera
        # has walked the opposite direction; 250 leaves headroom.
        far_z=250.0,
    )

    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)
    ms.translate(ms.MatrixStack.view, -camera.x, -camera.y, -camera.z)

    GL.glUseProgram(program)
    GL.glUniform3f(u_light_pos, *light_pos)
    GL.glUniform3f(u_camera_pos, camera.x, camera.y, camera.z)
    if lighting_on:
        GL.glUniform3f(u_ambient, ambient, ambient, ambient)
        GL.glUniform3f(u_diffuse, diffuse, diffuse, diffuse)
        GL.glUniform3f(u_specular, specular, specular, specular)
    else:
        # Effectively unlit: full ambient term, no diffuse/specular.
        GL.glUniform3f(u_ambient, 1.0, 1.0, 1.0)
        GL.glUniform3f(u_diffuse, 0.0, 0.0, 0.0)
        GL.glUniform3f(u_specular, 0.0, 0.0, 0.0)
    GL.glUniform1f(u_shininess, shininess)
    GL.glUniform1i(u_tex, 0)
    GL.glUniform3f(u_base, 1.0, 1.0, 1.0)

    if wireframe:
        # Single yellow wireframe pass over everything; skip shadows
        # because the projection is invisible without fills.
        GL.glUniform1i(u_render_mode, 2)
        GL.glUniform3f(u_base, 1.0, 1.0, 0.0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_grass)
        set_mvp_uniforms()
        _bind_and_draw(ground_vao, ground_count)
        draw_inhabitants(yrot)
    else:
        # ---- Lit pass for the ground ----
        GL.glUniform1i(u_render_mode, 1)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_grass)
        set_mvp_uniforms()
        _bind_and_draw(ground_vao, ground_count)

        # ---- Shadow pass ----
        # Inject the planar shadow matrix into the model stack BEFORE
        # any actor transforms, so each actor's vertices get squashed
        # to the ground plane.  Stencil + blend let the shadow show
        # through the ground (depth test off) without doubling where
        # silhouettes overlap.
        if shadows_on:
            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            GL.glEnable(GL.GL_STENCIL_TEST)
            GL.glStencilFunc(GL.GL_EQUAL, 0, 0xFF)
            GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_INCR)
            # Backface culling on the squashed (degenerate) geometry
            # produces gaps; drop it for the shadow pass.
            GL.glDisable(GL.GL_CULL_FACE)
            GL.glUniform1i(u_render_mode, 0)

            with ms.push_matrix(ms.MatrixStack.model):
                ms.multiply(ms.MatrixStack.model, np.matrix(shadow_matrix))
                draw_inhabitants(yrot)

            GL.glEnable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_STENCIL_TEST)
            GL.glDisable(GL.GL_BLEND)
            GL.glEnable(GL.GL_DEPTH_TEST)

        # ---- Lit pass for the inhabitants ----
        GL.glUniform1i(u_render_mode, 1)
        draw_inhabitants(yrot)

        # ---- Light position marker ----
        # Lifted from chapt05/shadow.cpp:272-277:  translate to the
        # light, draw a small unlit yellow sphere as the "bulb" so
        # students can see *where* the light is when they slide it
        # around.  We reuse the orbiter sphere (radius 0.1) and scale
        # it up via the model matrix; renderMode=2 short-circuits both
        # texture sampling and lighting.
        GL.glUniform1i(u_render_mode, 2)
        GL.glUniform3f(u_base, *LIGHT_MARKER_COLOR)
        with ms.push_matrix(ms.MatrixStack.model):
            ms.translate(ms.MatrixStack.model, *light_pos)
            ms.scale(
                ms.MatrixStack.model,
                LIGHT_MARKER_SCALE,
                LIGHT_MARKER_SCALE,
                LIGHT_MARKER_SCALE,
            )
            set_mvp_uniforms()
            _bind_and_draw(sphere_small_vao, sphere_small_count)

    GL.glUseProgram(0)
    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

GL.glBindVertexArray(0)
GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
GL.glUseProgram(0)
GL.glDeleteVertexArrays(1, [sphere_big_vao])
GL.glDeleteVertexArrays(1, [sphere_small_vao])
GL.glDeleteVertexArrays(1, [torus_vao])
GL.glDeleteVertexArrays(1, [ground_vao])
GL.glDeleteBuffers(1, [sphere_big_vbo])
GL.glDeleteBuffers(1, [sphere_small_vbo])
GL.glDeleteBuffers(1, [torus_vbo])
GL.glDeleteBuffers(1, [ground_vbo])
GL.glDeleteTextures(1, [tex_grass])
GL.glDeleteTextures(1, [tex_wood])
GL.glDeleteTextures(1, [tex_orb])
GL.glDeleteProgram(program)

glfw.terminate()
