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

"""2D graphing calculator -- plot authored ``f(x)`` functions.

A standalone program (run it by path).  It plots a list of first-class Python
functions -- written into this file, graphing-calculator style, not typed in at
runtime -- over a pannable, zoomable set of axes with tick marks and a grid.
The imgui menubar's Controls menu sets the view: x/y center (pan), the y
half-height (zoom), and the tick/grid spacing.

Reuse: the window + imgui + GL context, the menubar helpers, and the loop come
from the course's shared ``mvpvisualization.cayley_gl`` toolkit; the
solid-colour line pipeline and the VAO/VBO builders from ``_pipeline``; and the
view is the plot->NDC **ortho edge** realised onto the projection stack
(``matrix_stack``).  This is the same Cayley-graph machinery the demos use --
the ortho is an affine (invertible) map from plot space to NDC.
"""

import dataclasses
import enum
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

if typing.TYPE_CHECKING:
    # glfw types window handles as `_GLFWwindowPointerT`: private, absent at
    # runtime, so alias it under TYPE_CHECKING for the callback annotation.
    from glfw import _GLFWwindowPointerT

    GLFWWindow: typing.TypeAlias = _GLFWwindowPointerT


# imgui via cayley_gl so glfw + OpenGL.GL import before imgui_bundle.
imgui: types.ModuleType = cayley_gl.imgui

#: An RGB colour in 0..1 -- the uniform the line pipeline reads.
Color: typing.TypeAlias = tuple[float, float, float]


# ---------------------------------------------------------------------------
# The functions to plot -- FIRST-CLASS Python callables, authored here.
# Add a line to this list to graph another function; nothing is typed at
# runtime.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class PlottedFunction:
    """One graphed function: the callable, a label, and its curve colour."""

    fn: typing.Callable[[float], float]
    label: str
    color: Color


FUNCTIONS: list[PlottedFunction] = [
    PlottedFunction(
        fn=lambda x: math.sin(x), label="sin(x)", color=(0.95, 0.35, 0.35)
    ),
    PlottedFunction(
        fn=lambda x: math.cos(x), label="cos(x)", color=(0.35, 0.75, 0.95)
    ),
    PlottedFunction(
        fn=lambda x: 0.25 * x * x - 2.0,
        label="x^2/4 - 2",
        color=(0.55, 0.9, 0.5),
    ),
    PlottedFunction(
        fn=lambda x: 0.05 * x * x * x,
        label="x^3/20",
        color=(0.95, 0.8, 0.4),
    ),
]


# ---------------------------------------------------------------------------
# Fixed plot extents (world/plot coordinates) for the grid and axes, which are
# built once over this range; pan/zoom only move the ortho window across them.
# The curves instead resample to the visible window each time the view moves.
# ---------------------------------------------------------------------------

PLOT_HALF_RANGE: float = 50.0  # grid/axes span [-50, 50] in x and y
TICK_LENGTH: float = 0.15  # half-length of an axis tick mark, world units

GRID_COLOR: Color = (0.16, 0.16, 0.2)
AXIS_COLOR: Color = (0.6, 0.6, 0.72)

# Basis-vector reference frame (the BASIS backdrop): unit e1/e2 arrows measured
# in plot units, so they scale with zoom like the grid, mirroring the 3D
# cayley_gl.draw_axis convention -- e1 red, e2 green, the origin a white dot.
BASIS_HEAD_LEN: float = 0.18  # arrowhead length, fraction of the unit shaft
BASIS_HEAD_HALF_W: float = 0.09  # arrowhead half-width, plot units
ORIGIN_DOT_RADIUS: float = 0.08  # plot units
E1_COLOR: Color = (1.0, 0.25, 0.25)
E2_COLOR: Color = (0.25, 0.95, 0.35)
ORIGIN_COLOR: Color = (1.0, 1.0, 1.0)


# ---------------------------------------------------------------------------
# View + window state.
# ---------------------------------------------------------------------------


class Backdrop(enum.Enum):
    """What reference frame is drawn behind the plotted curves."""

    GRID = enum.auto()  # graph paper: grid + axes + tick marks
    AXES = enum.auto()  # just the axes with tick marks
    BASIS = enum.auto()  # the origin (white dot) and the e1/e2 unit vectors


@dataclasses.dataclass
class View2D:
    """The pannable/zoomable ortho window over plot space."""

    center_x: float = 0.0
    center_y: float = 0.0
    half_height: float = 8.0  # world units from center to top edge (zoom)
    tick_spacing: float = 1.0
    backdrop: Backdrop = Backdrop.GRID


view: View2D = View2D()
win_state: cayley_gl.WindowState = cayley_gl.WindowState()
#: Previous cursor position while a left-drag pan is in progress (else None).
mouse_prev: tuple[float, float] | None = None


# ---------------------------------------------------------------------------
# Geometry builders -- plain numpy float arrays of GL_LINES / GL_LINE_STRIP
# vertices in plot coordinates (z = 0).
# ---------------------------------------------------------------------------


def sample_curve(
    fn: typing.Callable[[float], float],
    x_lo: float,
    x_hi: float,
    n_samples: int,
) -> np.ndarray:
    """Sample ``fn`` across ``[x_lo, x_hi]`` into a GL_LINE_STRIP vertex array.

    The sample range and count follow the visible window -- one point per pixel
    column -- the way a graphing calculator plots.  Tying the sampling to the
    view keeps the polyline smooth when zoomed in and stops it degenerating
    into dropped sub-pixel segments (the dashed-at-the-peaks look) when zoomed
    out, which a fixed sample set over a fixed range cannot do at both ends.
    """
    xs: np.ndarray = np.linspace(x_lo, x_hi, n_samples)
    verts: list[float] = []
    for x in xs:
        xf: float = float(x)
        verts.extend([xf, float(fn(xf)), 0.0])
    return np.array(verts, dtype=np.float32)


def build_grid(spacing: float) -> np.ndarray:
    """Grid lines at every ``spacing`` across the plot range (GL_LINES)."""
    verts: list[float] = []
    n: int = int(PLOT_HALF_RANGE / spacing)
    for i in range(-n, n + 1):
        c: float = i * spacing
        verts.extend([c, -PLOT_HALF_RANGE, 0.0, c, PLOT_HALF_RANGE, 0.0])
        verts.extend([-PLOT_HALF_RANGE, c, 0.0, PLOT_HALF_RANGE, c, 0.0])
    return np.array(verts, dtype=np.float32)


def build_axes_and_ticks(spacing: float) -> np.ndarray:
    """The two axes plus a tick mark at every ``spacing`` (GL_LINES)."""
    verts: list[float] = []
    # the x axis (y = 0) then the y axis (x = 0)
    verts.extend([-PLOT_HALF_RANGE, 0.0, 0.0, PLOT_HALF_RANGE, 0.0, 0.0])
    verts.extend([0.0, -PLOT_HALF_RANGE, 0.0, 0.0, PLOT_HALF_RANGE, 0.0])
    n: int = int(PLOT_HALF_RANGE / spacing)
    for i in range(-n, n + 1):
        if i == 0:
            continue
        c: float = i * spacing
        # tick on the x axis (a short vertical mark), and on the y axis.
        verts.extend([c, -TICK_LENGTH, 0.0, c, TICK_LENGTH, 0.0])
        verts.extend([-TICK_LENGTH, c, 0.0, TICK_LENGTH, c, 0.0])
    return np.array(verts, dtype=np.float32)


def build_basis_shaft(dx: float, dy: float) -> np.ndarray:
    """The shaft of the unit basis vector along (dx, dy) (GL_LINES)."""
    return np.array([0.0, 0.0, 0.0, dx, dy, 0.0], dtype=np.float32)


def build_basis_head(dx: float, dy: float) -> np.ndarray:
    """A filled triangular arrowhead at the tip of unit vector (dx, dy)."""
    perp_x: float = -dy
    perp_y: float = dx
    back_x: float = dx * (1.0 - BASIS_HEAD_LEN)
    back_y: float = dy * (1.0 - BASIS_HEAD_LEN)
    tip: list[float] = [dx, dy, 0.0]
    left: list[float] = [
        back_x + BASIS_HEAD_HALF_W * perp_x,
        back_y + BASIS_HEAD_HALF_W * perp_y,
        0.0,
    ]
    right: list[float] = [
        back_x - BASIS_HEAD_HALF_W * perp_x,
        back_y - BASIS_HEAD_HALF_W * perp_y,
        0.0,
    ]
    return np.array(tip + left + right, dtype=np.float32)


def build_origin_dot() -> np.ndarray:
    """A filled circle at the origin (GL_TRIANGLE_FAN: center then rim)."""
    verts: list[float] = [0.0, 0.0, 0.0]
    segments: int = 24
    for i in range(segments + 1):
        theta: float = 2.0 * math.pi * float(i) / float(segments)
        verts.extend(
            [
                ORIGIN_DOT_RADIUS * math.cos(theta),
                ORIGIN_DOT_RADIUS * math.sin(theta),
                0.0,
            ]
        )
    return np.array(verts, dtype=np.float32)


# ---------------------------------------------------------------------------
# This file is a program, not a module: it now acquires a window + GL context
# and runs its own loop.  A tool that imports it to inspect it stops here.
# ---------------------------------------------------------------------------
if __name__ != "__main__":
    sys.exit("this is a program, run it directly rather than importing it")


window, impl, imguiio = cayley_gl.setup("2D Graphing Calculator")
GL.glClearColor(0.07, 0.07, 0.09, 1.0)

# Anti-alias the lines.  A curve is thousands of tiny GL_LINE_STRIP segments;
# where it runs near-horizontal (the sin/cos peaks and troughs) those sub-pixel
# segments drop out under GL's diamond-exit rule and the curve looks dashed.
# Smooth-line coverage, blended in, fills those gaps and softens every edge.
GL.glEnable(GL.GL_LINE_SMOOTH)
GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)
GL.glEnable(GL.GL_BLEND)
GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

# The shared solid-colour line pipeline + its shaders live in mvpvisualization.
MVP_SHADER_DIR: str = os.path.dirname(os.path.abspath(cayley_gl.__file__))
line_pipeline: _p.Pipeline = _p.build_pipeline(
    "uniform_color.vert",
    "passthrough.frag",
    shader_dir=MVP_SHADER_DIR,
    color=True,
)


@dataclasses.dataclass
class DynamicLines:
    """A GL_LINES mesh whose vertices are re-uploaded when spacing changes."""

    vao: int
    vbo: int
    count: int


def build_dynamic_lines(verts: np.ndarray) -> DynamicLines:
    contiguous: np.ndarray = np.ascontiguousarray(verts, dtype=np.float32)
    vbo: int = _p.make_vbo(contiguous, usage=GL.GL_DYNAMIC_DRAW)
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
    return DynamicLines(
        vao=vao, vbo=vbo, count=contiguous.size // _p.floats_per_vertex
    )


def update_dynamic_lines(lines: DynamicLines, verts: np.ndarray) -> None:
    contiguous: np.ndarray = np.ascontiguousarray(verts, dtype=np.float32)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, lines.vbo)
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER,
        contiguous.nbytes,
        contiguous,
        GL.GL_DYNAMIC_DRAW,
    )
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    lines.count = contiguous.size // _p.floats_per_vertex


grid_lines: DynamicLines = build_dynamic_lines(build_grid(view.tick_spacing))
axis_lines: DynamicLines = build_dynamic_lines(
    build_axes_and_ticks(view.tick_spacing)
)
# Curves are resampled to the visible window each time the view moves, so they
# start as empty dynamic meshes and the first frame fills them.
curve_lines: list[DynamicLines] = [
    build_dynamic_lines(sample_curve(pf.fn, -1.0, 1.0, 2)) for pf in FUNCTIONS
]
# (x_lo, x_hi, n_samples) the curves were last sampled at (rebuild on change)
curve_build_key: tuple[float, float, int] | None = None
# spacing the dynamic grid/axis meshes were last built at (rebuild on change)
built_spacing: float = view.tick_spacing

# The basis-vector backdrop is static geometry in plot units (built once; the
# ortho view scales it with zoom).
e1_shaft: DynamicLines = build_dynamic_lines(build_basis_shaft(1.0, 0.0))
e1_head: DynamicLines = build_dynamic_lines(build_basis_head(1.0, 0.0))
e2_shaft: DynamicLines = build_dynamic_lines(build_basis_shaft(0.0, 1.0))
e2_head: DynamicLines = build_dynamic_lines(build_basis_head(0.0, 1.0))
origin_dot: DynamicLines = build_dynamic_lines(build_origin_dot())


def rebuild_grid_if_needed() -> None:
    global built_spacing
    if view.tick_spacing == built_spacing:
        return
    update_dynamic_lines(grid_lines, build_grid(view.tick_spacing))
    update_dynamic_lines(axis_lines, build_axes_and_ticks(view.tick_spacing))
    built_spacing = view.tick_spacing


def rebuild_curves_if_needed(w: int, h: int) -> None:
    """Resample every curve across the visible x window when the view moves."""
    global curve_build_key
    aspect: float = float(w) / float(h) if h else 1.0
    half_w: float = view.half_height * aspect
    x_lo: float = view.center_x - half_w
    x_hi: float = view.center_x + half_w
    n_samples: int = max(2, int(w))  # one sample per pixel column
    key: tuple[float, float, int] = (round(x_lo, 3), round(x_hi, 3), n_samples)
    if key == curve_build_key:
        return
    for lines, pf in zip(curve_lines, FUNCTIONS):
        update_dynamic_lines(lines, sample_curve(pf.fn, x_lo, x_hi, n_samples))
    curve_build_key = key


# ---------------------------------------------------------------------------
# Drawing + view.
# ---------------------------------------------------------------------------


def draw_lines(vao: int, count: int, color: Color, mode: _p.GLenum) -> None:
    GL.glUseProgram(line_pipeline.program)
    GL.glBindVertexArray(vao)
    GL.glUniform3f(line_pipeline.u_color, *color)
    _p.set_uniforms(line_pipeline.u_m, line_pipeline.u_v, line_pipeline.u_p)
    GL.glDrawArrays(mode, 0, count)


def apply_ortho_view(w: int, h: int) -> None:
    """Set the plot->NDC ortho edge from the current pan/zoom (the Cayley
    edge, realised onto the projection stack)."""
    GL.glViewport(0, 0, w, h)
    aspect: float = float(w) / float(h) if h else 1.0
    half_w: float = view.half_height * aspect
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)
    ms.ortho(
        left=view.center_x - half_w,
        right=view.center_x + half_w,
        bottom=view.center_y - view.half_height,
        top=view.center_y + view.half_height,
        near=0.0,
        far=550.0,
    )
    # push the z=0 plot plane in front of the camera, inside [near, far]
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -100.0)


def handle_pan_zoom_keys() -> None:
    """Held-key pan (arrows) and zoom (-/= or +), polled each frame."""
    pan_step: float = view.half_height * 0.04
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        view.center_x -= pan_step
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        view.center_x += pan_step
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        view.center_y -= pan_step
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        view.center_y += pan_step
    if glfw.get_key(window, glfw.KEY_MINUS) == glfw.PRESS:
        view.half_height = min(PLOT_HALF_RANGE, view.half_height * 1.03)
    if glfw.get_key(window, glfw.KEY_EQUAL) == glfw.PRESS:
        view.half_height = max(0.25, view.half_height / 1.03)


def mouse_pan(h: int) -> None:
    """Left-drag pans the view so the grabbed plot point tracks the cursor.

    The pixel delta converts to world units by ``2*half_height / height`` (the
    ortho window's world-per-pixel, the same on x and y), so a drag moves the
    plot by exactly the distance dragged at any zoom.  Ignored while imgui owns
    the mouse (a menu is open under the pointer).
    """
    global mouse_prev
    pos: tuple[float, float] = glfw.get_cursor_pos(window)
    down: bool = (
        glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
    )
    if down and not imguiio.want_capture_mouse and mouse_prev is not None:
        world_per_px: float = 2.0 * view.half_height / float(h) if h else 0.0
        view.center_x -= (pos[0] - mouse_prev[0]) * world_per_px
        view.center_y += (pos[1] - mouse_prev[1]) * world_per_px
    mouse_prev = pos if down else None


def install_scroll_zoom() -> None:
    """Mouse wheel scales the zoom (half_height), chaining imgui's callback."""
    # None is glfw's documented "clear and return the previous callback" value;
    # the stub types it as the callback, hence the suppression.
    prev_cb: list[typing.Any] = [glfw.set_scroll_callback(window, None)]  # ty: ignore[invalid-argument-type]

    def scroll_cb(win: "GLFWWindow", x_off: float, y_off: float) -> None:
        if prev_cb[0] is not None:
            prev_cb[0](win, x_off, y_off)
        if not imguiio.want_capture_mouse:
            view.half_height = min(
                PLOT_HALF_RANGE, max(0.25, view.half_height * 0.9**y_off)
            )

    glfw.set_scroll_callback(window, scroll_cb)


def reset_view() -> None:
    view.center_x = 0.0
    view.center_y = 0.0
    view.half_height = 8.0


def set_backdrop(mode: Backdrop) -> None:
    view.backdrop = mode


def cycle_backdrop() -> None:
    members: list[Backdrop] = list(Backdrop)
    idx: int = members.index(view.backdrop)
    view.backdrop = members[(idx + 1) % len(members)]


def draw_basis_frame() -> None:
    """Origin (white dot) + the e1/e2 unit-vector arrows (BASIS backdrop)."""
    # Dot first, so it stays on top at the origin where the shafts begin.
    draw_lines(
        origin_dot.vao, origin_dot.count, ORIGIN_COLOR, GL.GL_TRIANGLE_FAN
    )
    draw_lines(e1_shaft.vao, e1_shaft.count, E1_COLOR, GL.GL_LINES)
    draw_lines(e1_head.vao, e1_head.count, E1_COLOR, GL.GL_TRIANGLES)
    draw_lines(e2_shaft.vao, e2_shaft.count, E2_COLOR, GL.GL_LINES)
    draw_lines(e2_head.vao, e2_head.count, E2_COLOR, GL.GL_TRIANGLES)


def imgui_menubar() -> None:
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        cayley_gl.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _, view.center_x = imgui.slider_float(
            "X center", view.center_x, -PLOT_HALF_RANGE, PLOT_HALF_RANGE
        )
        _, view.center_y = imgui.slider_float(
            "Y center", view.center_y, -PLOT_HALF_RANGE, PLOT_HALF_RANGE
        )
        _, view.half_height = imgui.slider_float(
            "Zoom (Y half-height)", view.half_height, 0.25, PLOT_HALF_RANGE
        )
        _, view.tick_spacing = imgui.slider_float(
            "Tick/grid spacing", view.tick_spacing, 0.25, 10.0
        )
        cayley_gl.menu_action(
            "Backdrop: Grid",
            "G",
            lambda: set_backdrop(Backdrop.GRID),
            selected=view.backdrop == Backdrop.GRID,
        )
        cayley_gl.menu_action(
            "Backdrop: Axes + ticks",
            "",
            lambda: set_backdrop(Backdrop.AXES),
            selected=view.backdrop == Backdrop.AXES,
        )
        cayley_gl.menu_action(
            "Backdrop: Origin + e1/e2",
            "",
            lambda: set_backdrop(Backdrop.BASIS),
            selected=view.backdrop == Backdrop.BASIS,
        )
        cayley_gl.menu_action("Reset View", "0", reset_view)
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


def on_key(
    window: "GLFWWindow", key: int, scancode: int, action: int, mods: int
) -> None:
    cayley_gl.common_key(window, win_state, key, action)
    if action != glfw.PRESS:
        return
    if key == glfw.KEY_G:
        cycle_backdrop()
    elif key == glfw.KEY_0:
        reset_view()


def frame(w: int, h: int) -> None:
    handle_pan_zoom_keys()
    mouse_pan(h)
    rebuild_grid_if_needed()
    rebuild_curves_if_needed(w, h)
    apply_ortho_view(w, h)
    if view.backdrop == Backdrop.GRID:
        draw_lines(grid_lines.vao, grid_lines.count, GRID_COLOR, GL.GL_LINES)
    if view.backdrop in (Backdrop.GRID, Backdrop.AXES):
        draw_lines(axis_lines.vao, axis_lines.count, AXIS_COLOR, GL.GL_LINES)
    if view.backdrop == Backdrop.BASIS:
        draw_basis_frame()
    # The shared GL setup leaves depth-testing on (GL_LESS) and everything
    # here is at z=0, so a curve pixel landing on an already-drawn backdrop
    # pixel has equal depth and is rejected -- which punched holes in a curve
    # right where a sin/cos peak runs along the y=1 grid line.  Clear depth
    # after the backdrop so the plotted curves always draw over it.
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
    for pf, lines in zip(FUNCTIONS, curve_lines):
        draw_lines(lines.vao, lines.count, pf.color, GL.GL_LINE_STRIP)


install_scroll_zoom()
cayley_gl.run_loop(window, impl, frame, imgui_menubar, on_key)
