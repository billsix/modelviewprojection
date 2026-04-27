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
#     demo22  -- Lambert lighting, textures, shadow-mapped shadows
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
# * Shadow mapping -- the scene is rendered twice per frame.  First a
#   *depth-only* pre-pass into an off-screen FBO from the light's
#   point of view (perspective projection from the actual point-light
#   position); then the color pass samples that depth map to decide
#   per-fragment whether a given world-space point is occluded from
#   the light or not.  Replaces the stencil-buffered planar-shadow
#   trick used by the SuperBible original.
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
# Stencil buffer is no longer needed (shadow mapping replaced the
# planar-shadow stencil dance), but leaving the hint in place is
# harmless and keeps context creation symmetric with the SuperBible
# original which requested GLUT_STENCIL.
glfw.window_hint(glfw.STENCIL_BITS, 8)

window = glfw.create_window(
    800, 600, "ModelViewProjection Demo 24 -- SphereWorld",
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
ambient: float = 0.25     # SuperBible fLowLight
diffuse: float = 1.0      # SuperBible fBrightLight
specular: float = 1.0
shininess: float = 128.0  # SuperBible glMateriali(..., 128)

# Light position is parameterized by spherical coordinates around the
# world origin so it can be slid around at runtime.  Defaults put the
# light low and in front of the camera (camera starts at origin
# looking down -Z) so the yellow marker is visible from frame 1, and
# the low elevation casts long visible shadows -- both points the
# students should notice.  The SuperBible original was higher and
# behind the camera at (-100, 100, 50); slide the sliders to recreate.
light_az_deg: float = 270.0     # 0 = +X, 90 = +Z, 180 = -X, 270 = -Z
light_el_deg: float = 15.0      # angle above the XZ plane
light_distance: float = 60.0    # distance from origin


def handle_inputs() -> None:
    move_step: float = 0.1

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


# ---------------------------------------------------------------------------
# Shader program
# ---------------------------------------------------------------------------


def _compile(vert_name: str, frag_name: str) -> int:
    with open(os.path.join(pwd, vert_name)) as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, frag_name)) as f:
        fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)
    return shaders.compileProgram(vs, fs)


# Two programs:  the main one, and a depth-only one used for the
# shadow-map pre-pass (it just rasterizes positions into the off-
# screen FBO's depth attachment).
program: int = _compile("sphereworld.vert", "sphereworld.frag")
depth_program: int = _compile("depth.vert", "depth.frag")

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
u_use_shadows = GL.glGetUniformLocation(program, "useShadows")
u_shadow_map = GL.glGetUniformLocation(program, "shadowMap")
u_light_space = GL.glGetUniformLocation(program, "lightSpaceMatrix")

u_depth_model = GL.glGetUniformLocation(depth_program, "modelMatrix")
u_depth_light_space = GL.glGetUniformLocation(
    depth_program, "lightSpaceMatrix"
)


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
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
    )
    channels = img.shape[2]
    fmt = GL.GL_RGB if channels == 3 else GL.GL_RGBA
    internal = GL.GL_RGB8 if channels == 3 else GL.GL_RGBA8
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D, 0, internal, w, h, 0,
        fmt, GL.GL_UNSIGNED_BYTE, img,
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
        phi0 = math.pi * v0 - math.pi / 2.0   # -pi/2 (south) .. pi/2 (north)
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
            p00 = ((cphi0 * st0, sphi0, cphi0 * ct0),
                   (cphi0 * st0, sphi0, cphi0 * ct0), (u0, v0))
            p10 = ((cphi0 * st1, sphi0, cphi0 * ct1),
                   (cphi0 * st1, sphi0, cphi0 * ct1), (u1, v0))
            p01 = ((cphi1 * st0, sphi1, cphi1 * ct0),
                   (cphi1 * st0, sphi1, cphi1 * ct0), (u0, v1))
            p11 = ((cphi1 * st1, sphi1, cphi1 * ct1),
                   (cphi1 * st1, sphi1, cphi1 * ct1), (u1, v1))

            for vert in (p00, p10, p01, p10, p11, p01):
                pos, nrm, uv = vert
                out.extend(p * radius for p in pos)
                out.extend(nrm)
                out.extend(uv)
    return np.array(out, dtype=np.float32)


def _build_torus(R: float, r: float,
                 sides: int, rings: int) -> np.ndarray:
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

            p00 = vert(cu0, su0, cv0, sv0, i / sides,       j / rings)
            p01 = vert(cu0, su0, cv1, sv1, i / sides,       (j + 1) / rings)
            p10 = vert(cu1, su1, cv0, sv0, (i + 1) / sides, j / rings)
            p11 = vert(cu1, su1, cv1, sv1, (i + 1) / sides, (j + 1) / rings)

            for v in (p00, p01, p10, p10, p01, p11):
                pos, nrm, uv = v
                out.extend(pos)
                out.extend(nrm)
                out.extend(uv)
    return np.array(out, dtype=np.float32)


def _build_ground(extent: float, step: float, y: float,
                  tex_step: float) -> np.ndarray:
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
    _build_sphere(0.3, 21, 11))
sphere_small_vao, sphere_small_vbo, sphere_small_count = make_vao(
    _build_sphere(0.1, 21, 11))
torus_vao, torus_vbo, torus_count = make_vao(
    _build_torus(0.35, 0.15, 61, 37))

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
    sphere_origins.append((
        ((_rng.randint(0, 399)) - 200) * 0.1,
        0.0,
        ((_rng.randint(0, 399)) - 200) * 0.1,
    ))


# ---------------------------------------------------------------------------
# Lighting & shadow projection
# ---------------------------------------------------------------------------


def light_position_ws(az_deg: float, el_deg: float,
                      distance: float) -> tuple[float, float, float]:
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


# Yellow ball drawn at the light's location (chapt05/shadow.cpp:272).
# Origin's small sphere mesh is radius 0.1; we scale it 20x in the
# model matrix so it's visible from across the world (radius 2.0).
LIGHT_MARKER_SCALE: float = 20.0
LIGHT_MARKER_COLOR: tuple[float, float, float] = (1.0, 1.0, 0.0)


# ---------------------------------------------------------------------------
# Shadow map -- off-screen depth-only framebuffer
# ---------------------------------------------------------------------------
# Same recipe as demo22:  GL_DEPTH_COMPONENT24 texture, FBO with no
# color attachment, GL_NONE for the draw/read buffers.  See demo22
# for the longer commentary; here we just wire it up.

SHADOW_MAP_SIZE: int = 1024

shadow_depth_tex = GL.glGenTextures(1)
GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_depth_tex)
GL.glTexImage2D(
    GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT24,
    SHADOW_MAP_SIZE, SHADOW_MAP_SIZE, 0,
    GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT, None,
)
GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
GL.glTexParameteri(
    GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_BORDER
)
GL.glTexParameteri(
    GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_BORDER
)
GL.glTexParameterfv(
    GL.GL_TEXTURE_2D, GL.GL_TEXTURE_BORDER_COLOR,
    np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
)
GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

shadow_fbo = GL.glGenFramebuffers(1)
GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, shadow_fbo)
GL.glFramebufferTexture2D(
    GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT,
    GL.GL_TEXTURE_2D, shadow_depth_tex, 0,
)
GL.glDrawBuffer(GL.GL_NONE)
GL.glReadBuffer(GL.GL_NONE)
if (GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)
        != GL.GL_FRAMEBUFFER_COMPLETE):
    raise RuntimeError("shadow FBO is not complete")
GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)


def look_at(eye: np.ndarray, target: np.ndarray,
            up: np.ndarray) -> np.matrix:
    """Right-handed look-at:  world-to-view matrix that puts `eye` at
    the origin, looking down -Z toward `target`."""
    f = target - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.identity(4, dtype=np.float32)
    m[0, 0:3] = s
    m[1, 0:3] = u
    m[2, 0:3] = -f
    m[0, 3] = -np.dot(s, eye)
    m[1, 3] = -np.dot(u, eye)
    m[2, 3] =  np.dot(f, eye)
    return np.matrix(m)


def perspective_proj(fov_deg: float, aspect: float,
                     near: float, far: float) -> np.matrix:
    """Right-handed perspective projection (looks down -Z).  Same
    convention as gluPerspective and pyMatrixStack.perspective."""
    f = 1.0 / math.tan(math.radians(fov_deg) / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return np.matrix(m)


def light_space_matrix(light_pos_vec) -> np.matrix:
    """Light view + projection for the positional light.  Eye sits at
    the actual light position; we look at the scene's center
    (origin), which works because all the spheres are scattered
    within ~20 units of origin and the ground is centered there too.

    A 90 degree FOV is wide enough to see the whole 40x40 ground from
    light positions as close as ~20 units (the slider's minimum)."""
    target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    eye = np.array(light_pos_vec, dtype=np.float32)
    up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    if abs(eye[1]) > 0.999 * float(np.linalg.norm(eye)):
        # Light is straight up (or down); pick a different up to
        # avoid the degenerate cross product.
        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    view = look_at(eye, target, up)
    # Near = 1 keeps depth precision usable across distances 20..200.
    # Far = 250 = same as the camera's far plane, so light at the
    # outer slider edge still has depth headroom.
    proj = perspective_proj(90.0, 1.0, 1.0, 250.0)
    return proj @ view


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def _bind_and_draw(vao: int, count: int, mode=GL.GL_TRIANGLES) -> None:
    GL.glBindVertexArray(vao)
    GL.glDrawArrays(mode, 0, count)
    GL.glBindVertexArray(0)


def draw_inhabitants(yrot: float) -> None:
    """Draw the 30 spheres + the rotating torus/orbiter pair.  Caller
    has already set renderMode + texture binding state for the lit
    color pass."""
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


def _set_depth_model_matrix() -> None:
    """Push the current model matrix to the depth program's uniform.
    set_mvp_uniforms() uses the *color* program's locations; for the
    depth pass we have a separate uniform that takes only the model
    matrix (since lightSpaceMatrix replaces the camera's view+proj)."""
    GL.glUniformMatrix4fv(
        u_depth_model, 1, GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.model),
            dtype=np.float32,
        ),
    )


def draw_shadow_casters_depth(yrot: float) -> None:
    """Re-walk the same scene tree as draw_inhabitants() + the ground,
    but writing only depth (the depth program is already bound).
    Light marker is intentionally excluded -- the bulb shouldn't
    cast a shadow on itself.

    The ground gets included so it can self-shadow at grazing
    angles (rare here, but cheap to add)."""
    # Ground.
    with ms.push_matrix(ms.MatrixStack.model):
        _set_depth_model_matrix()
        GL.glBindVertexArray(ground_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, ground_count)

    # Scattered inhabitant spheres.
    for ox, oy, oz in sphere_origins:
        with ms.push_matrix(ms.MatrixStack.model):
            ms.translate(ms.MatrixStack.model, ox, oy, oz)
            _set_depth_model_matrix()
            GL.glBindVertexArray(sphere_big_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, sphere_big_count)

    # Torus + orbiter cluster.
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model, 0.0, 0.1, -2.5)

        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_y(ms.MatrixStack.model, -2.0 * yrot)
            ms.translate(ms.MatrixStack.model, 1.0, 0.0, 0.0)
            _set_depth_model_matrix()
            GL.glBindVertexArray(sphere_small_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, sphere_small_count)

        ms.rotate_y(ms.MatrixStack.model, yrot)
        _set_depth_model_matrix()
        GL.glBindVertexArray(torus_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, torus_count)

    GL.glBindVertexArray(0)


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
        "Azimuth (deg)", light_az_deg, 0.0, 360.0)
    _, light_el_deg = imgui.slider_float(
        "Elevation (deg)", light_el_deg, 5.0, 89.0)
    _, light_distance = imgui.slider_float(
        "Distance", light_distance, 20.0, 200.0)
    imgui.separator()
    _, ambient = imgui.slider_float("Ambient", ambient, 0.0, 1.0)
    _, diffuse = imgui.slider_float("Diffuse", diffuse, 0.0, 1.0)
    _, specular = imgui.slider_float("Specular", specular, 0.0, 1.0)
    _, shininess = imgui.slider_float("Shininess", shininess, 1.0, 256.0)
    imgui.end()

    light_pos = light_position_ws(light_az_deg, light_el_deg, light_distance)
    light_space = light_space_matrix(light_pos)
    light_space_arr = np.ascontiguousarray(light_space, dtype=np.float32)

    width, height = glfw.get_framebuffer_size(window)

    # ============================================================
    # Pass 1 -- depth pre-pass into the shadow FBO.  Skipped when
    # the user has turned shadows off or is in wireframe mode.
    # ============================================================
    if shadows_on and not wireframe:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, shadow_fbo)
        GL.glViewport(0, 0, SHADOW_MAP_SIZE, SHADOW_MAP_SIZE)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        # Front-face culling during the depth pass shifts shadow acne
        # to the *outside* of objects, where the geometry hides it.
        GL.glCullFace(GL.GL_FRONT)
        GL.glUseProgram(depth_program)
        GL.glUniformMatrix4fv(
            u_depth_light_space, 1, GL.GL_TRUE, light_space_arr
        )
        ms.set_to_identity_matrix(ms.MatrixStack.model)
        draw_shadow_casters_depth(yrot)
        GL.glUseProgram(0)
        GL.glCullFace(GL.GL_BACK)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    # ============================================================
    # Pass 2 -- color pass into the default framebuffer.
    # ============================================================
    GL.glViewport(0, 0, width, height)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPolygonMode(
        GL.GL_FRONT_AND_BACK, GL.GL_LINE if wireframe else GL.GL_FILL
    )

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    aspect = float(width) / float(height) if height > 0 else 1.0
    ms.perspective(
        field_of_view=35.0,    # SuperBible used 35 degrees
        aspect_ratio=aspect,
        near_z=0.1,
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
    GL.glUniform1i(u_shadow_map, 1)             # texture unit 1
    GL.glUniformMatrix4fv(u_light_space, 1, GL.GL_TRUE, light_space_arr)
    GL.glUniform1i(u_use_shadows, 1 if (shadows_on and not wireframe) else 0)
    GL.glUniform3f(u_base, 1.0, 1.0, 1.0)

    # Bind the shadow depth texture on unit 1 for the rest of this
    # color pass.  The main texture (grass/wood/orb) lives on unit 0.
    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_depth_tex)
    GL.glActiveTexture(GL.GL_TEXTURE0)

    if wireframe:
        # Single yellow wireframe pass over everything.
        GL.glUniform1i(u_render_mode, 2)
        GL.glUniform3f(u_base, 1.0, 1.0, 0.0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_grass)
        set_mvp_uniforms()
        _bind_and_draw(ground_vao, ground_count)
        draw_inhabitants(yrot)
    else:
        # ---- Lit pass for the ground (the main shadow receiver) ----
        GL.glUniform1i(u_render_mode, 1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_grass)
        set_mvp_uniforms()
        _bind_and_draw(ground_vao, ground_count)

        # ---- Lit pass for the inhabitants ----
        # The fragment shader samples the shadow map and darkens the
        # diffuse+specular terms wherever this fragment is occluded
        # from the light's POV.  No second draw call needed -- the
        # shadow comes "for free" out of the lit pass.
        draw_inhabitants(yrot)

        # ---- Light position marker (yellow ball) ----
        # Drawn unlit and *with shadows off*, so the bulb glows
        # uniformly and isn't darkened by its own occluder samples.
        GL.glUniform1i(u_render_mode, 2)
        GL.glUniform1i(u_use_shadows, 0)
        GL.glUniform3f(u_base, *LIGHT_MARKER_COLOR)
        with ms.push_matrix(ms.MatrixStack.model):
            ms.translate(ms.MatrixStack.model, *light_pos)
            ms.scale(ms.MatrixStack.model,
                     LIGHT_MARKER_SCALE,
                     LIGHT_MARKER_SCALE,
                     LIGHT_MARKER_SCALE)
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
