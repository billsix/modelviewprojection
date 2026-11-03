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

"""3D graphing calculator -- plot an authored ``f(x, y)`` as a surface.

A standalone program (run it by path).  It plots one of a list of first-class
Python surfaces -- written into this file -- as a height field over the x-z
ground plane (the function value is the up/y coordinate), shown as a wireframe
and/or a height-coloured solid mesh.  The imgui Controls menu sets the grid
sampling steps **dx** and **dy** (live rebuild) and toggles wireframe/solid;
the Surface menu picks which function; an orbit camera (left-drag / arrows /
scroll) looks around it.  Lighting is deliberately out of scope here -- the lit
triangle-mesh (Blinn-Phong) version is tasks/graphing-calculator-3d-lit-mesh.md.

Reuse: window + imgui + GL context, the orbit camera, the menubar helpers and
the loop come from ``mvpvisualization.cayley_gl``; the line + per-vertex-colour
pipelines, their shared shaders, and the VAO/VBO builders from ``_pipeline``;
the perspective view from ``matrix_stack`` (via ``setup_orbit_view``).  Only the
``ports/`` subtree is off-limits.
"""

import atexit
import dataclasses
import math
import os
import sys
import types
import typing

import glfw
import numpy as np
import OpenGL.GL as GL

import modelviewprojection.matrix_stack as ms
from modelviewprojection.mvpvisualization import _pipeline as _p
from modelviewprojection.mvpvisualization import cayley_gl
from modelviewprojection.mvpvisualization import labels as _labels

if typing.TYPE_CHECKING:
    from glfw import _GLFWwindowPointerT

    GLFWWindow: typing.TypeAlias = _GLFWwindowPointerT


imgui: types.ModuleType = cayley_gl.imgui

#: An RGB colour in 0..1.
Color: typing.TypeAlias = tuple[float, float, float]


# ---------------------------------------------------------------------------
# The surfaces to plot -- FIRST-CLASS Python callables, authored here.  Each
# takes (x, y) over the square domain below and returns a height.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Surface:
    """One graphed surface: f(x, y), a label, a colour, and the LaTeX (authored
    in source) that the billboard renderer typesets as its equation caption."""

    fn: typing.Callable[[float, float], float]
    label: str
    color: Color
    latex: str


def _ripple(x: float, y: float) -> float:
    r: float = math.sqrt(x * x + y * y)
    return 2.0 * math.sin(r)


SURFACES: list[Surface] = [
    Surface(
        fn=lambda x, y: x * y / 4.0,
        label="saddle: x*y/4",
        color=(0.95, 0.55, 0.35),
        latex=r"z=\tfrac{xy}{4}",
    ),
    Surface(
        fn=lambda x, y: (x * x + y * y) / 8.0,
        label="paraboloid: (x^2+y^2)/8",
        color=(0.45, 0.8, 0.95),
        latex=r"z=\tfrac{x^2+y^2}{8}",
    ),
    Surface(
        fn=_ripple,
        label="ripple: 2 sin(r)",
        color=(0.6, 0.9, 0.5),
        latex=r"z=2\sin\sqrt{x^2+y^2}",
    ),
    Surface(
        fn=lambda x, y: math.sin(x) * math.cos(y),
        label="waves: sin(x) cos(y)",
        color=(0.9, 0.75, 0.45),
        latex=r"z=\sin(x)\cos(y)",
    ),
]


DOMAIN_HALF: float = 6.0  # surfaces span [-6, 6] x [-6, 6]
AXIS_LENGTH: float = 7.0
TICK_LENGTH: float = 0.12
AXIS_COLOR: Color = (0.6, 0.6, 0.72)


# ---------------------------------------------------------------------------
# View + window state.
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class View3D:
    """Which surface is shown, the sampling steps, and the draw modes."""

    current: int = 0
    dx: float = 0.5
    dy: float = 0.5
    show_wireframe: bool = True
    show_solid: bool = False  # start as a bare wireframe mesh; solid is opt-in
    show_labels: bool = True


view: View3D = View3D()
win_state: cayley_gl.WindowState = cayley_gl.WindowState()
mouse_prev: tuple[float, float] | None = None


# ---------------------------------------------------------------------------
# Height-field geometry.  Domain x -> world x, domain y -> world z (ground
# plane), height f(x, y) -> world y (up).
# ---------------------------------------------------------------------------


def _axis_count(step: float) -> int:
    return max(1, int(round((2.0 * DOMAIN_HALF) / step)))


def _height_color(base: Color, t: float) -> list[float]:
    """Shade ``base`` by normalised height ``t`` in 0..1 (dark low, bright
    high) so the solid surface reads without any lighting."""
    scale: float = 0.3 + 0.7 * t
    return [base[0] * scale, base[1] * scale, base[2] * scale]


def build_wireframe(surface: Surface, dx: float, dy: float) -> np.ndarray:
    """Grid lines of the height field as GL_LINES (both grid directions)."""
    nx: int = _axis_count(dx)
    ny: int = _axis_count(dy)
    verts: list[float] = []

    def height(i: int, j: int) -> tuple[float, float, float]:
        x: float = -DOMAIN_HALF + i * (2.0 * DOMAIN_HALF) / nx
        z: float = -DOMAIN_HALF + j * (2.0 * DOMAIN_HALF) / ny
        return x, float(surface.fn(x, z)), z

    for j in range(ny + 1):
        for i in range(nx):
            x0, y0, z0 = height(i, j)
            x1, y1, z1 = height(i + 1, j)
            verts.extend([x0, y0, z0, x1, y1, z1])
    for i in range(nx + 1):
        for j in range(ny):
            x0, y0, z0 = height(i, j)
            x1, y1, z1 = height(i, j + 1)
            verts.extend([x0, y0, z0, x1, y1, z1])
    return np.array(verts, dtype=np.float32)


def build_solid(
    surface: Surface, dx: float, dy: float
) -> tuple[np.ndarray, np.ndarray]:
    """Two triangles per cell (GL_TRIANGLES) plus a per-vertex colour that
    shades by height.  Returns (positions, colours)."""
    nx: int = _axis_count(dx)
    ny: int = _axis_count(dy)
    grid: list[list[tuple[float, float, float]]] = []
    lo: float = math.inf
    hi: float = -math.inf
    for i in range(nx + 1):
        row: list[tuple[float, float, float]] = []
        for j in range(ny + 1):
            x: float = -DOMAIN_HALF + i * (2.0 * DOMAIN_HALF) / nx
            z: float = -DOMAIN_HALF + j * (2.0 * DOMAIN_HALF) / ny
            y: float = float(surface.fn(x, z))
            lo = min(lo, y)
            hi = max(hi, y)
            row.append((x, y, z))
        grid.append(row)
    span: float = hi - lo if hi > lo else 1.0

    positions: list[float] = []
    colors: list[float] = []

    def emit(p: tuple[float, float, float]) -> None:
        positions.extend([p[0], p[1], p[2]])
        colors.extend(_height_color(surface.color, (p[1] - lo) / span))

    for i in range(nx):
        for j in range(ny):
            a: tuple[float, float, float] = grid[i][j]
            b: tuple[float, float, float] = grid[i + 1][j]
            c: tuple[float, float, float] = grid[i + 1][j + 1]
            d: tuple[float, float, float] = grid[i][j + 1]
            for p in (a, b, c, a, c, d):
                emit(p)
    return (
        np.array(positions, dtype=np.float32),
        np.array(colors, dtype=np.float32),
    )


def build_axes() -> np.ndarray:
    """The three axes (through the origin) plus tick marks (GL_LINES)."""
    verts: list[float] = [
        -AXIS_LENGTH,
        0.0,
        0.0,
        AXIS_LENGTH,
        0.0,
        0.0,
        0.0,
        -AXIS_LENGTH,
        0.0,
        0.0,
        AXIS_LENGTH,
        0.0,
        0.0,
        0.0,
        -AXIS_LENGTH,
        0.0,
        0.0,
        AXIS_LENGTH,
    ]
    n: int = int(DOMAIN_HALF)
    for i in range(-n, n + 1):
        if i == 0:
            continue
        c: float = float(i)
        # ticks along x (mark up), along z (mark up), along y (mark along x)
        verts.extend([c, -TICK_LENGTH, 0.0, c, TICK_LENGTH, 0.0])
        verts.extend([0.0, -TICK_LENGTH, c, 0.0, TICK_LENGTH, c])
        verts.extend([-TICK_LENGTH, c, 0.0, TICK_LENGTH, c, 0.0])
    return np.array(verts, dtype=np.float32)


# ---------------------------------------------------------------------------
# This file is a program, not a module: it now acquires a window + GL context
# and runs its own loop.  A tool that imports it to inspect it stops here.
# ---------------------------------------------------------------------------
if __name__ != "__main__":
    sys.exit("this is a program, run it directly rather than importing it")


window, impl, imguiio = cayley_gl.setup("3D Graphing Calculator")
GL.glClearColor(0.07, 0.07, 0.09, 1.0)
GL.glEnable(GL.GL_DEPTH_TEST)
camera: _p.Camera = cayley_gl.make_camera(r=22.0)
cayley_gl.install_scroll(window, imguiio, camera)

MVP_SHADER_DIR: str = os.path.dirname(os.path.abspath(cayley_gl.__file__))
line_pipeline: _p.Pipeline = _p.build_pipeline(
    "uniform_color.vert",
    "passthrough.frag",
    shader_dir=MVP_SHADER_DIR,
    color=True,
)
surface_pipeline: _p.Pipeline = _p.build_pipeline(
    "per_vertex_color.vert",
    "passthrough.frag",
    shader_dir=MVP_SHADER_DIR,
    per_vertex_color=True,
)
# Runtime TeX billboard labels (no-op if texExpToPng is not on PATH).
label_renderer: _labels.LabelRenderer = _labels.LabelRenderer(MVP_SHADER_DIR)
atexit.register(label_renderer.cleanup)


@dataclasses.dataclass
class SurfaceMeshes:
    """The rebuildable wireframe + solid meshes for the current surface."""

    wire_vao: int
    wire_vbo: int
    wire_count: int
    solid_vao: int
    solid_pos_vbo: int
    solid_color_vbo: int
    solid_count: int


def _dynamic_lines(verts: np.ndarray) -> tuple[int, int, int]:
    data: np.ndarray = np.ascontiguousarray(verts, dtype=np.float32)
    vbo: int = _p.make_vbo(data, usage=GL.GL_DYNAMIC_DRAW)
    vao: int = _p.make_vao(
        [
            _p.AttribSpec(
                vbo=vbo,
                location=line_pipeline.attr_position,
                size=_p.floats_per_vertex,
                layout=(0, 0),
            )
        ]
    )
    return vao, vbo, data.size // _p.floats_per_vertex


def _dynamic_solid(
    positions: np.ndarray, colors: np.ndarray
) -> tuple[int, int, int, int]:
    pos: np.ndarray = np.ascontiguousarray(positions, dtype=np.float32)
    col: np.ndarray = np.ascontiguousarray(colors, dtype=np.float32)
    pos_vbo: int = _p.make_vbo(pos, usage=GL.GL_DYNAMIC_DRAW)
    color_vbo: int = _p.make_vbo(col, usage=GL.GL_DYNAMIC_DRAW)
    vao: int = _p.make_vao(
        [
            _p.AttribSpec(
                vbo=pos_vbo,
                location=surface_pipeline.attr_position,
                size=_p.floats_per_vertex,
                layout=(0, 0),
            ),
            _p.AttribSpec(
                vbo=color_vbo,
                location=surface_pipeline.attr_color,
                size=3,
                layout=(0, 0),
            ),
        ]
    )
    return vao, pos_vbo, color_vbo, pos.size // _p.floats_per_vertex


def _reupload(vbo: int, verts: np.ndarray) -> int:
    data: np.ndarray = np.ascontiguousarray(verts, dtype=np.float32)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, data.nbytes, data, GL.GL_DYNAMIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    return data.size


def build_meshes() -> SurfaceMeshes:
    surface: Surface = SURFACES[view.current]
    wire: np.ndarray = build_wireframe(surface, view.dx, view.dy)
    positions, colors = build_solid(surface, view.dx, view.dy)
    wire_vao, wire_vbo, wire_n = _dynamic_lines(wire)
    solid_vao, pos_vbo, color_vbo, solid_n = _dynamic_solid(positions, colors)
    return SurfaceMeshes(
        wire_vao=wire_vao,
        wire_vbo=wire_vbo,
        wire_count=wire_n,
        solid_vao=solid_vao,
        solid_pos_vbo=pos_vbo,
        solid_color_vbo=color_vbo,
        solid_count=solid_n,
    )


meshes: SurfaceMeshes = build_meshes()
axes_vao, axes_count = _p.make_lines_vao(
    build_axes(), line_pipeline.attr_position
)
# (current, dx, dy) the meshes were last built at -- rebuild when it changes.
built_key: tuple[int, float, float] = (view.current, view.dx, view.dy)


def rebuild_meshes_if_needed() -> None:
    global built_key
    key: tuple[int, float, float] = (view.current, view.dx, view.dy)
    if key == built_key:
        return
    surface: Surface = SURFACES[view.current]
    wire: np.ndarray = build_wireframe(surface, view.dx, view.dy)
    positions, colors = build_solid(surface, view.dx, view.dy)
    meshes.wire_count = _reupload(meshes.wire_vbo, wire) // _p.floats_per_vertex
    _reupload(meshes.solid_color_vbo, colors)
    meshes.solid_count = (
        _reupload(meshes.solid_pos_vbo, positions) // _p.floats_per_vertex
    )
    built_key = key


# ---------------------------------------------------------------------------
# Drawing.
# ---------------------------------------------------------------------------


def draw_lines(vao: int, count: int, color: Color) -> None:
    GL.glUseProgram(line_pipeline.program)
    GL.glBindVertexArray(vao)
    GL.glUniform3f(line_pipeline.u_color, *color)
    _p.set_uniforms(line_pipeline.u_m, line_pipeline.u_v, line_pipeline.u_p)
    GL.glDrawArrays(GL.GL_LINES, 0, count)


def draw_solid() -> None:
    GL.glUseProgram(surface_pipeline.program)
    GL.glBindVertexArray(meshes.solid_vao)
    _p.set_uniforms(
        surface_pipeline.u_m, surface_pipeline.u_v, surface_pipeline.u_p
    )
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, meshes.solid_count)


def imgui_menubar() -> None:
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        cayley_gl.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Surface", True):
        for idx, surface in enumerate(SURFACES):
            cayley_gl.menu_action(
                surface.label,
                "",
                lambda i=idx: _select(i),
                selected=(idx == view.current),
            )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _, view.dx = imgui.slider_float("Grid step dx", view.dx, 0.2, 2.0)
        _, view.dy = imgui.slider_float("Grid step dy", view.dy, 0.2, 2.0)
        cayley_gl.menu_action(
            "Wireframe", "W", _toggle_wire, selected=view.show_wireframe
        )
        cayley_gl.menu_action(
            "Solid surface", "S", _toggle_solid, selected=view.show_solid
        )
        cayley_gl.menu_action(
            "Labels", "L", toggle_labels, selected=view.show_labels
        )
        imgui.end_menu()
    if imgui.begin_menu("View", True):
        cayley_gl.menu_action(
            "Fullscreen",
            "F11",
            lambda: cayley_gl.toggle_fullscreen(window, win_state),
            selected=win_state.fullscreen,
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def _select(index: int) -> None:
    view.current = index


def _toggle_wire() -> None:
    view.show_wireframe = not view.show_wireframe


def _toggle_solid() -> None:
    view.show_solid = not view.show_solid


def on_key(
    window: "GLFWWindow", key: int, scancode: int, action: int, mods: int
) -> None:
    cayley_gl.common_key(window, win_state, key, action)
    if action != glfw.PRESS:
        return
    if key == glfw.KEY_W:
        _toggle_wire()
    elif key == glfw.KEY_S:
        _toggle_solid()
    elif key == glfw.KEY_L:
        toggle_labels()


def toggle_labels() -> None:
    view.show_labels = not view.show_labels


def draw_labels(w: int, h: int) -> None:
    """Billboard LaTeX labels: the x/y/z axis tips (domain x -> world x, domain
    y -> world z, height -> world y) and the current surface's equation above
    the plot."""
    v_m: np.ndarray = ms.get_current_matrix(ms.MatrixStack.view)
    p_m: np.ndarray = ms.get_current_matrix(ms.MatrixStack.projection)
    label_renderer.begin(v_m, p_m, (w, h))
    label_renderer.draw("x", (AXIS_LENGTH + 0.4, 0.0, 0.0))
    label_renderer.draw("y", (0.0, 0.0, AXIS_LENGTH + 0.4))
    label_renderer.draw("z", (0.0, AXIS_LENGTH + 0.4, 0.0))
    label_renderer.draw(
        SURFACES[view.current].latex, (0.0, AXIS_LENGTH + 1.6, 0.0)
    )
    label_renderer.end()


def frame(w: int, h: int) -> None:
    global mouse_prev
    rebuild_meshes_if_needed()
    mouse_prev = cayley_gl.orbit_input(window, imguiio, camera, mouse_prev)
    cayley_gl.setup_orbit_view(camera, w, h)
    draw_lines(axes_vao, axes_count, AXIS_COLOR)
    if view.show_solid:
        draw_solid()
    if view.show_wireframe:
        draw_lines(
            meshes.wire_vao,
            meshes.wire_count,
            SURFACES[view.current].color,
        )
    if view.show_labels and label_renderer.available:
        draw_labels(w, h)


cayley_gl.run_loop(window, impl, frame, imgui_menubar, on_key)
