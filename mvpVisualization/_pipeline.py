"""Shared helpers for the MVP visualizations.

Each visualization at ``mvpVisualization/<dir>/<demo>.py`` (one level under
this module) imports it via::

    PWD = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(PWD))
    import _pipeline as _p

Same convention as ``ports/openglsuperbiblev4/_common.py``, just one directory
shallower because the demos live at depth 1 instead of depth 2.

What this module owns:
    - GLFW + ImGui boilerplate: ``setup_window(title)``, ``install_esc_close``,
      ``install_camera_scroll``.
    - Shader compilation: ``compile_program(pwd, vert, frag, geom=None)``.
      Reads files relative to the *demo's own* pwd so each demo dir stays
      self-contained for shaders.
    - VAO builders: ``make_triangle_vao(...)`` and ``make_lines_vao(...)``.
      Both register their handles into ``all_vaos`` / ``all_vbos`` for
      cleanup; ``compile_program`` registers into ``all_programs``.
    - Standard mesh data: ``paddle_vertices``, ``square_vertices``,
      ``build_ground_vertices()``, ``build_axis_vertices()``,
      ``build_ndc_cube_vertices()``.
    - Per-frame uniform set: ``set_uniforms(u_m, u_v, u_p)``.
    - Common dataclass: ``Camera`` (orbit camera with r, rot_y, rot_x).
    - ``cleanup()`` releases every registered handle on shutdown.

What stays in the demo file:
    - Pipeline creation (each demo has different shader programs / uniform
      sets / attribute layouts).
    - The per-pipeline ``draw_*`` functions.
    - Demo-specific geometry (e.g. the 2D NDC outline in modelview2d, the
      perspective Frustum in modelviewperspectiveprojection).
    - The main loop.
"""

import ctypes
import math
import os
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders
from imgui_bundle import imgui, imgui_md
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
from numpy import ndarray

import modelviewprojection.pyMatrixStack as ms


glfloat_size: int = 4
floatsPerVertex: int = 3
floatsPerColor: int = 3


# ---------------------------------------------------------------------------
# GL handle registries -- everything created via this module gets appended
# here and released by cleanup().
# ---------------------------------------------------------------------------

all_vaos: list[int] = []
all_vbos: list[int] = []
all_programs: list[int] = []


def cleanup() -> None:
    """Release every GL handle registered through this module.  Call once
    after the main loop exits, before ``glfw.terminate()``."""
    if all_vaos:
        GL.glDeleteVertexArrays(len(all_vaos), all_vaos)
    if all_vbos:
        GL.glDeleteBuffers(len(all_vbos), all_vbos)
    for prog in all_programs:
        GL.glDeleteProgram(prog)


# ---------------------------------------------------------------------------
# Window + ImGui setup -- collapses the per-file init blocks (and the stray
# duplicate ``imgui.create_context()`` / ``GlfwRenderer(window)`` that lived
# in 5 of 6 demos) into a single entry point.
# ---------------------------------------------------------------------------


def init_fonts_and_markdown() -> None:
    imgui_md.initialize_markdown()
    font_loader: imgui_md.VoidFunction = imgui_md.get_font_loader_function()
    font_loader()


def setup_window(title: str, width: int = 1920, height: int = 1080):
    """Initialize GLFW + a 3.3-core context + ImGui.  Returns
    ``(window, impl, imguiio)``.  Sets the standard background colour and
    enables depth testing."""
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)

    imgui.create_context()

    window = glfw.create_window(int(width), int(height), title, None, None)
    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        sys.exit(1)
    glfw.make_context_current(window)

    # macOS Core Profile requires a non-zero VAO bound at all times for
    # any vertex-attribute or draw call (VAO 0 is prohibited).  We
    # generate one here and leave it bound as the default; per-mesh
    # VAOs override-bind when they need a specific layout, and we
    # never call glBindVertexArray(0).  Mesa and NVIDIA tolerate the
    # spec violation silently; Apple's driver does not.
    _default_vao = GL.glGenVertexArrays(1)
    GL.glBindVertexArray(_default_vao)

    impl = GlfwRenderer(window)
    if not impl:
        glfw.terminate()
        sys.exit(1)

    init_fonts_and_markdown()
    imguiio = imgui.get_io()

    GL.glClearColor(13.0 / 255.0, 64.0 / 255.0, 5.0 / 255.0, 1.0)
    GL.glClearDepth(1.0)
    GL.glDepthFunc(GL.GL_LESS)
    GL.glEnable(GL.GL_DEPTH_TEST)

    return window, impl, imguiio


def install_esc_close(window) -> None:
    """Standard Escape-closes-window key handler."""
    def on_key(win, key, scancode, action, mods):
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(win, 1)
    glfw.set_key_callback(window, on_key)


def install_camera_scroll(window, imguiio, camera) -> None:
    """Standard mouse-wheel-zooms-camera scroll callback.  Chains with any
    pre-existing scroll callback.  Skip this in 2D demos with no zoom."""
    prev_cb = [glfw.set_scroll_callback(window, None)]

    def scroll_cb(win, x_offset, y_offset):
        if prev_cb[0] is not None:
            prev_cb[0](win, x_offset, y_offset)
        if not imguiio.want_capture_mouse:
            camera.r = camera.r + -1 * (y_offset * math.log(camera.r))
            if camera.r < 3.0:
                camera.r = 3.0

    glfw.set_scroll_callback(window, scroll_cb)


# ---------------------------------------------------------------------------
# Shader compilation -- reads from each demo's own pwd so .vert/.frag/.geom
# files stay co-located with the demo.
# ---------------------------------------------------------------------------


def compile_program(
    pwd: str,
    vert: str,
    frag: str,
    geom: Optional[str] = None,
) -> int:
    """Compile a vert+frag (and optional geom) program from files in ``pwd``.
    The resulting program is registered for cleanup."""
    with open(os.path.join(pwd, vert), "r") as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, frag), "r") as f:
        fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)
    if geom is None:
        prog = shaders.compileProgram(vs, fs)
    else:
        with open(os.path.join(pwd, geom), "r") as f:
            gs = shaders.compileShader(f.read(), GL.GL_GEOMETRY_SHADER)
        prog = shaders.compileProgram(vs, gs, fs)
    all_programs.append(prog)
    return prog


# ---------------------------------------------------------------------------
# VAO builders -- each registers its VAO + VBO(s) for cleanup.
# ---------------------------------------------------------------------------


# Two-step VAO/VBO construction.  The OpenGL model is:
#   1. A VBO holds bytes (vertex data, color data, etc.).
#   2. A VAO records "this attribute slot reads N floats from THIS VBO
#      at THIS offset/stride."  A VAO can mix attributes from multiple
#      VBOs; one VBO can be referenced by multiple VAOs with
#      different layouts.
#
# Splitting them lets two meshes that share geometry (e.g. paddle1
# and paddle2 sharing paddle vertices) reference one VBO from two
# VAOs -- the deduplication win in demo21.


@dataclass(frozen=True)
class AttribSpec:
    """One vertex attribute pulled from one VBO.

    Fields:
        vbo:      the VBO this attribute reads from.
        location: the shader attribute slot (``glGetAttribLocation``
                  result, or pinned via ``layout(location=N)``).
        size:     floats per vertex (2/3/4).
        layout:   ``(stride_bytes, offset_bytes)``.  Kept as a tuple
                  because the two are coupled -- they describe one
                  buffer-layout decision together.
    """
    vbo: int
    location: int
    size: int
    layout: Tuple[int, int]


def make_vbo(data: ndarray, usage: int = GL.GL_STATIC_DRAW) -> int:
    """Allocate a VBO and upload ``data`` (any ndarray, must be
    contiguous float32 -- the helper coerces).  Touches no VAO state.
    The handle is registered into ``all_vbos`` for cleanup."""
    data = np.ascontiguousarray(data, dtype=np.float32)
    vbo = GL.glGenBuffers(1)
    all_vbos.append(vbo)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, data.nbytes, data, usage)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    return vbo


def make_vao(attribs: list[AttribSpec]) -> int:
    """Build a VAO that reads each ``AttribSpec`` from its VBO.  The
    handle is registered into ``all_vaos`` for cleanup."""
    vao = GL.glGenVertexArrays(1)
    all_vaos.append(vao)
    GL.glBindVertexArray(vao)
    for a in attribs:
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, a.vbo)
        GL.glEnableVertexAttribArray(a.location)
        stride, offset = a.layout
        GL.glVertexAttribPointer(
            a.location, a.size, GL.GL_FLOAT, False,
            stride, ctypes.c_void_p(offset),
        )
    return vao


# ---------------------------------------------------------------------------
# Convenience wrappers used by the visualization demos.  Both build their
# VBOs and VAOs via the two primitives above.
# ---------------------------------------------------------------------------


def make_triangle_vao(
    vertices: ndarray,
    r: float,
    g: float,
    b: float,
    *,
    attr_position: int,
    attr_color: int,
) -> Tuple[int, int]:
    """VAO for the triangle pipeline: positions + per-vertex color (the same
    RGB triple repeated once per vertex).  Returns (vao, vertex_count).  The
    ``attr_*`` parameters are the shader's attribute indices, which differ
    per program."""
    vertices = np.ascontiguousarray(vertices, dtype=np.float32).flatten()
    n_verts = vertices.size // floatsPerVertex
    colors = np.tile(np.array([r, g, b], dtype=np.float32), n_verts)

    pos_vbo = make_vbo(vertices)
    color_vbo = make_vbo(colors)
    vao = make_vao([
        AttribSpec(vbo=pos_vbo, location=attr_position,
                   size=floatsPerVertex, layout=(0, 0)),
        AttribSpec(vbo=color_vbo, location=attr_color,
                   size=floatsPerColor, layout=(0, 0)),
    ])
    return vao, n_verts


def make_lines_vao(vertices: ndarray, attr_position: int) -> Tuple[int, int]:
    """Position-only VAO for the lines pipelines (ground/axis/cube/frustum).
    Returns (vao, vertex_count)."""
    vertices = np.ascontiguousarray(vertices, dtype=np.float32).flatten()
    n_verts = vertices.size // floatsPerVertex
    vbo = make_vbo(vertices)
    vao = make_vao([
        AttribSpec(vbo=vbo, location=attr_position,
                   size=floatsPerVertex, layout=(0, 0)),
    ])
    return vao, n_verts


# ---------------------------------------------------------------------------
# Standard mesh data shared across the visualizations.
# ---------------------------------------------------------------------------

# fmt: off
paddle_vertices: ndarray = np.array(
    [
        -1.0, -3.0, 0.0,
         1.0, -3.0, 0.0,
         1.0,  3.0, 0.0,
         1.0,  3.0, 0.0,
        -1.0,  3.0, 0.0,
        -1.0, -3.0, 0.0,
    ],
    dtype=np.float32,
)

square_vertices: ndarray = np.array(
    [
        -0.5, -0.5, 0.0,
         0.5, -0.5, 0.0,
         0.5,  0.5, 0.0,
         0.5,  0.5, 0.0,
        -0.5,  0.5, 0.0,
        -0.5, -0.5, 0.0,
    ],
    dtype=np.float32,
)
# fmt: on


def build_ground_vertices() -> ndarray:
    """A 41x41 grid of perpendicular line segments at y=-5 (x and z range
    -20..20)."""
    verts = []
    for x in range(-20, 21, 1):
        for z in range(-20, 21, 1):
            verts.append(float(-x))
            verts.append(float(-5.0))
            verts.append(float(z))
            verts.append(float(x))
            verts.append(float(-5.0))
            verts.append(float(z))
            verts.append(float(x))
            verts.append(float(-5.0))
            verts.append(float(-z))
            verts.append(float(x))
            verts.append(float(-5.0))
            verts.append(float(z))
    return np.array(verts, dtype=np.float32)


def build_axis_vertices() -> ndarray:
    """A Y-pointing axis line plus a 2-segment arrowhead.  ``draw_axis``
    in each demo binds this 3 times with model rotations to make X/Y/Z."""
    # fmt: off
    verts = [
        0.0,  0.0,  0.0,
        0.0,  1.0,  0.0,
        # arrow
        0.0,  1.0,  0.0,
        0.25, 0.75, 0.0,
        0.0,  1.0,  0.0,
       -0.25, 0.75, 0.0,
    ]
    # fmt: on
    return np.array(verts, dtype=np.float32)


def build_ground_cylinders(
    extent: float = 20.0,
    step: float = 1.0,
    y: float = -5.0,
    radius: float = 0.05,
    slices: int = 20,
) -> ndarray:
    """Grid of cylinder edges at the y plane: one horizontal cylinder
    per integer z, one vertical cylinder per integer x, each spanning
    [-extent, extent].  Replaces the redundant-line-pairs approach of
    ``build_ground_vertices()`` with the 82 visually-unique edges (41
    along each axis)."""
    n = int(extent / step)
    edges: list = []
    for i in range(-n, n + 1):
        coord = i * step
        # horizontal line at z = coord, x spanning [-extent, extent]
        edges.append(((-extent, y, coord), (extent, y, coord)))
        # vertical line at x = coord, z spanning [-extent, extent]
        edges.append(((coord, y, -extent), (coord, y, extent)))
    return build_cylinders_for_edges(edges, radius, slices)


def build_axis_arrow_solid(
    rod_radius: float = 0.05,
    rod_length: float = 0.85,
    cone_radius: float = 0.12,
    cone_length: float = 0.15,
    slices: int = 20,
) -> ndarray:
    """Triangle mesh for a +Y-pointing axis arrow: cylinder shaft from
    y=0 to y=rod_length, cone arrowhead from y=rod_length to
    y=rod_length+cone_length.  Y-aligned so the existing draw_axis
    rotations (rotate_z(-90) for X, rotate_y(90)+rotate_z(90) for Z,
    default for Y) keep working.

    Returns a flat float32 vertex array suitable for ``make_lines_vao``
    + ``glDrawArrays(GL_TRIANGLES, ...)``.  Components per slice:
    cylinder side (2 triangles), cylinder bottom cap (1), cone base
    disk (1), cone side (1) -- 5 triangles * slices total."""
    h_rod = rod_length
    h_tip = rod_length + cone_length
    verts: list[float] = []
    for i in range(slices):
        a0 = 2.0 * math.pi * i / slices
        a1 = 2.0 * math.pi * (i + 1) / slices
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)

        # Cylinder side -- quad split into two triangles
        verts += [c0 * rod_radius, 0.0,   s0 * rod_radius]
        verts += [c1 * rod_radius, 0.0,   s1 * rod_radius]
        verts += [c1 * rod_radius, h_rod, s1 * rod_radius]

        verts += [c0 * rod_radius, 0.0,   s0 * rod_radius]
        verts += [c1 * rod_radius, h_rod, s1 * rod_radius]
        verts += [c0 * rod_radius, h_rod, s0 * rod_radius]

        # Cylinder bottom cap (closes the y=0 end)
        verts += [0.0,             0.0,   0.0]
        verts += [c0 * rod_radius, 0.0,   s0 * rod_radius]
        verts += [c1 * rod_radius, 0.0,   s1 * rod_radius]

        # Cone base disk (closes the y=rod_length end of the cone, which
        # is wider than the cylinder top so the gap is visible)
        verts += [0.0,              h_rod, 0.0]
        verts += [c0 * cone_radius, h_rod, s0 * cone_radius]
        verts += [c1 * cone_radius, h_rod, s1 * cone_radius]

        # Cone side -- triangle from base ring to tip
        verts += [c0 * cone_radius, h_rod, s0 * cone_radius]
        verts += [c1 * cone_radius, h_rod, s1 * cone_radius]
        verts += [0.0,              h_tip, 0.0]

    return np.array(verts, dtype=np.float32)


def build_origin_sphere_solid(
    radius: float = 0.10,
    slices: int = 15,
    stacks: int = 15,
) -> ndarray:
    """Triangle mesh for a small solid sphere centered at the origin --
    the white dot that gltDrawUnitAxes finishes with, ported into the
    procedural pipeline.  Same vertex layout (flat float32, 3 components
    per vertex) as ``build_axis_arrow_solid`` so it can be drawn through
    ``make_lines_vao`` + the axis_program.

    Returns 2 * slices * stacks triangles."""
    verts: list[float] = []
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        s0, c0 = math.sin(lat0), math.cos(lat0)
        s1, c1 = math.sin(lat1), math.cos(lat1)
        for j in range(slices):
            lng0 = 2.0 * math.pi * float(j) / slices
            lng1 = 2.0 * math.pi * float(j + 1) / slices
            cl0, sl0 = math.cos(lng0), math.sin(lng0)
            cl1, sl1 = math.cos(lng1), math.sin(lng1)
            # Two CCW triangles per quad-strip cell, viewed from outside.
            p00 = (radius * cl0 * c0, radius * sl0 * c0, radius * s0)
            p01 = (radius * cl1 * c0, radius * sl1 * c0, radius * s0)
            p10 = (radius * cl0 * c1, radius * sl0 * c1, radius * s1)
            p11 = (radius * cl1 * c1, radius * sl1 * c1, radius * s1)
            verts += [*p10, *p00, *p11]
            verts += [*p11, *p00, *p01]
    return np.array(verts, dtype=np.float32)


def build_cylinders_for_edges(
    edges: list,
    radius: float = 0.05,
    slices: int = 20,
) -> ndarray:
    """Build a triangle mesh containing one cylinder per edge in ``edges``.
    Each entry is a ``((x0, y0, z0), (x1, y1, z1))`` pair: the cylinder
    runs from p0 to p1 with the given radius, capped at both ends.

    Returns a flat float32 array suitable for ``make_lines_vao`` +
    ``glDrawArrays(GL_TRIANGLES, ...)``.  5 triangles per slice per edge
    (cylinder side = 2, bottom cap = 1, top cap = 1, plus 1 spare for
    diagonal symmetry of the side strip)."""
    verts: list[float] = []
    for raw_p0, raw_p1 in edges:
        p0 = np.array(raw_p0, dtype=np.float32)
        p1 = np.array(raw_p1, dtype=np.float32)
        forward = p1 - p0
        length = float(np.linalg.norm(forward))
        if length < 1e-9:
            continue
        forward_unit = forward / length

        # Pick a reference axis not parallel to forward, then derive an
        # orthonormal (right, up) frame perpendicular to forward.
        if abs(forward_unit[1]) > 0.9:
            ref = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        else:
            ref = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        right = np.cross(forward_unit, ref)
        right = right / float(np.linalg.norm(right))
        up = np.cross(forward_unit, right)

        for i in range(slices):
            a0 = 2.0 * math.pi * i / slices
            a1 = 2.0 * math.pi * (i + 1) / slices
            off0 = right * (math.cos(a0) * radius) + up * (math.sin(a0) * radius)
            off1 = right * (math.cos(a1) * radius) + up * (math.sin(a1) * radius)
            b0 = p0 + off0
            b1 = p0 + off1
            t0 = p1 + off0
            t1 = p1 + off1

            # Cylinder side -- two triangles per slice
            verts += [float(b0[0]), float(b0[1]), float(b0[2])]
            verts += [float(b1[0]), float(b1[1]), float(b1[2])]
            verts += [float(t1[0]), float(t1[1]), float(t1[2])]

            verts += [float(b0[0]), float(b0[1]), float(b0[2])]
            verts += [float(t1[0]), float(t1[1]), float(t1[2])]
            verts += [float(t0[0]), float(t0[1]), float(t0[2])]

            # Bottom cap (closes the p0 end)
            verts += [float(p0[0]), float(p0[1]), float(p0[2])]
            verts += [float(b1[0]), float(b1[1]), float(b1[2])]
            verts += [float(b0[0]), float(b0[1]), float(b0[2])]

            # Top cap (closes the p1 end, opposite winding)
            verts += [float(p1[0]), float(p1[1]), float(p1[2])]
            verts += [float(t0[0]), float(t0[1]), float(t0[2])]
            verts += [float(t1[0]), float(t1[1]), float(t1[2])]

    return np.array(verts, dtype=np.float32)


def build_ndc_cube_cylinders(radius: float = 0.05, slices: int = 20) -> ndarray:
    """Solid cylinder mesh for the 12 edges of the NDC cube.  Replacement
    for ``build_ndc_cube_vertices()`` when rendering the NDC outline as
    solid white tubes instead of thick lines."""
    edges = [
        # back square (z = -1)
        ((-1.0, -1.0, -1.0), ( 1.0, -1.0, -1.0)),
        (( 1.0, -1.0, -1.0), ( 1.0,  1.0, -1.0)),
        (( 1.0,  1.0, -1.0), (-1.0,  1.0, -1.0)),
        ((-1.0,  1.0, -1.0), (-1.0, -1.0, -1.0)),
        # front square (z = +1)
        ((-1.0, -1.0,  1.0), ( 1.0, -1.0,  1.0)),
        (( 1.0, -1.0,  1.0), ( 1.0,  1.0,  1.0)),
        (( 1.0,  1.0,  1.0), (-1.0,  1.0,  1.0)),
        ((-1.0,  1.0,  1.0), (-1.0, -1.0,  1.0)),
        # connecting edges
        (( 1.0,  1.0, -1.0), ( 1.0,  1.0,  1.0)),
        (( 1.0, -1.0, -1.0), ( 1.0, -1.0,  1.0)),
        ((-1.0,  1.0, -1.0), (-1.0,  1.0,  1.0)),
        ((-1.0, -1.0, -1.0), (-1.0, -1.0,  1.0)),
    ]
    return build_cylinders_for_edges(edges, radius, slices)


def build_ndc_cube_vertices() -> ndarray:
    """The 12 edges of the NDC cube as line segments.  Used by all demos
    EXCEPT modelview2d (which uses a 2D z=0 outline -- defined inline there)."""
    # fmt: off
    verts = [
        # back square (z=-1)
        -1.0, -1.0, -1.0,
         1.0, -1.0, -1.0,
         1.0, -1.0, -1.0,
         1.0,  1.0, -1.0,
         1.0,  1.0, -1.0,
        -1.0,  1.0, -1.0,
        -1.0,  1.0, -1.0,
        -1.0, -1.0, -1.0,
        # front square (z=+1)
        -1.0, -1.0,  1.0,
         1.0, -1.0,  1.0,
         1.0, -1.0,  1.0,
         1.0,  1.0,  1.0,
         1.0,  1.0,  1.0,
        -1.0,  1.0,  1.0,
        -1.0,  1.0,  1.0,
        -1.0, -1.0,  1.0,
        # connect the squares
         1.0,  1.0, -1.0,
         1.0,  1.0,  1.0,
         1.0, -1.0, -1.0,
         1.0, -1.0,  1.0,
        -1.0,  1.0, -1.0,
        -1.0,  1.0,  1.0,
        -1.0, -1.0, -1.0,
        -1.0, -1.0,  1.0,
    ]
    # fmt: on
    return np.array(verts, dtype=np.float32)


# ---------------------------------------------------------------------------
# Per-frame uniform set.
# ---------------------------------------------------------------------------


def set_uniforms(u_m: int, u_v: int, u_p: int) -> None:
    """Set current model/view/projection matrices on the bound program at
    the given uniform locations.  Caller is responsible for ``glUseProgram``.

    Note: ``glUniform*`` updates the program object's default-uniform-block
    state -- it does not "upload" bytes to GPU memory the way
    ``glBufferData`` does.  See plans/notes-uniform-terminology.md."""
    GL.glUniformMatrix4fv(
        u_m,
        1,
        GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.model), dtype=np.float32
        ),
    )
    GL.glUniformMatrix4fv(
        u_v,
        1,
        GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.view), dtype=np.float32
        ),
    )
    GL.glUniformMatrix4fv(
        u_p,
        1,
        GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.projection),
            dtype=np.float32,
        ),
    )


# ---------------------------------------------------------------------------
# Standard 3rd-person orbit camera, instantiated by each demo with its own
# starting (r, rot_y, rot_x).
# ---------------------------------------------------------------------------


@dataclass
class Camera:
    r: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0
