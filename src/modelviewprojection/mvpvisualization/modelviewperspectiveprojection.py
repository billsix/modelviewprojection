# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""modelviewperspectiveprojection, on the Cayley-graph engine.

The full demo: object placement, the world->camera inverse, the camera drawn as
object with its frustum, the GPU perspective squash, both imgui trees, the
editable virtual camera, frustum sliders, and focus buttons.  ALL of that
choreography + panel is OWNED HERE; ``cayley_gl`` supplies only the generic
mechanisms."""

import math
import os
import sys
import typing
from enum import Enum, auto

import glfw
import numpy as np
import OpenGL.GL as GL
from gacalc.g3 import Vector
from gacalc.transforms import (
    InvertibleFunction,
    compose,
    inverse,
    scale_non_uniform,
    translate,
)

from modelviewprojection import matrix_stack as ms
from modelviewprojection.cayley import (
    cayleygraph,
    cayleyscene,
)
from modelviewprojection.mathutils import rotate_x, rotate_y, rotate_z
from modelviewprojection.mvpvisualization import _pipeline as _p
from modelviewprojection.mvpvisualization import (
    cayley_gl,
)

if typing.TYPE_CHECKING:
    # glfw types every window parameter as `_GLFWwindowPointerT`; it is private
    # and absent at runtime, so alias it here for the annotations below.
    from glfw import _GLFWwindowPointerT

    GLFWWindow: typing.TypeAlias = _GLFWwindowPointerT


# imgui via cayley_gl so glfw + OpenGL.GL import BEFORE imgui_bundle (its own GL
# loader must come after, or PyOpenGL's context tracking breaks at window
# setup).
imgui: typing.Any = cayley_gl.imgui


# --- the scene, declared -- spaces are enum members; the whole (immutable,
# acyclic) graph is passed at once.  The camera edge is named so the editable
# virtual camera can rewrite its Steps' fn in place.
class Space(Enum):
    world = auto()
    paddle1 = auto()
    square = auto()
    paddle2 = auto()
    camera = auto()


camera_edge: cayleygraph.Edge = cayleygraph.Edge(
    src=Space.camera,
    dst=Space.world,
    steps=[
        ("T", translate(Vector(-1.5, 0.0, 8.5))),
        ("R_y", rotate_y(math.radians(25.0))),
        ("R_x", rotate_x(math.radians(15.0))),
    ],
)

graph: cayleygraph.CayleyGraph = cayleygraph.CayleyGraph(
    [
        cayleygraph.Edge(
            src=Space.paddle1,
            dst=Space.world,
            steps=[
                ("T", translate(Vector(-9.0, 1.0, 0.0))),
                ("R_z", rotate_z(math.radians(45.0))),
            ],
        ),
        cayleygraph.Edge(
            src=Space.square,
            dst=Space.paddle1,
            steps=[
                ("T_-Z", translate(Vector(0.0, 0.0, -5.0))),
                ("R_Z", rotate_z(math.radians(30.0))),
                ("T_X", translate(Vector(1.5, 0.0, 0.0))),
                ("R2_Z", rotate_z(math.radians(90.0))),
            ],
        ),
        cayleygraph.Edge(
            src=Space.paddle2,
            dst=Space.world,
            steps=[
                ("T", translate(Vector(9.0, 0.5, 0.0))),
                ("R_z", rotate_z(math.radians(-20.0))),
            ],
        ),
        camera_edge,
    ]
)

scene: cayleyscene.Scene = cayleyscene.Scene(
    graph=graph,
    root=Space.world,
    coordinate_frames=[
        cayleyscene.CoordinateFrame(
            space=Space.paddle1,
            parent=Space.world,
            geometry="paddle1",
            dwell_before=2.0,
        ),
        cayleyscene.CoordinateFrame(
            space=Space.square, parent=Space.paddle1, geometry="square"
        ),
        cayleyscene.CoordinateFrame(
            space=Space.paddle2, parent=Space.world, geometry="paddle2"
        ),
        cayleyscene.CoordinateFrame(
            space=Space.camera,
            parent=Space.world,
            geometry=None,
            dwell_before=5.0,
        ),
    ],
    to_ndc=[
        cayleyscene.InverseOperations(
            from_space=Space.world,
            to_space=Space.camera,
            group_title="World->Camera",
        ),
        cayleyscene.NonInvertibleTransformation(
            group_title="Frustum->Rectangular Prism",
            step_labels=["Squash X", "Squash Y"],
            dwell_before=10.0,
        ),
        cayleyscene.NonInvertibleTransformation(
            group_title="Ortho, Rectangular Prism->NDC",
            step_labels=["T - Center", "Scale"],
        ),
    ],
    end_dwell=5.0,
)
animation: cayleyscene.Animation = cayleyscene.Animation(scene)
controls: cayleyscene.CameraControls = cayleyscene.CameraControls(
    translate_step=camera_edge.steps[0],
    rot_y_step=camera_edge.steps[1],
    rot_x_step=camera_edge.steps[2],
    px=-1.5,
    py=0.0,
    pz=8.5,
    rot_y=math.radians(25.0),
    rot_x=math.radians(15.0),
)
DRAW: dict[Space, str] = {
    Space.paddle1: "paddle1",
    Space.square: "square",
    Space.paddle2: "paddle2",
}
# (button label, node to center on; None centers on the origin / NDC)
FOCUS: list[tuple[str, Space | None]] = [
    ("NDC", None),
    ("Paddle1", Space.paddle1),
    ("Square", Space.square),
    ("Paddle2", Space.paddle2),
    ("Camera", Space.camera),
]
# center_on sentinel for the framebuffer itself (not a graph node): the
# "View From -> Framebuffer" option, selectable only once the framebuffer has
# settled back at its original bottom-left space (see imgui_menubar / frame).
FB_FOCUS: str = "framebuffer"

# --- framebuffer <-> NDC bracket -------------------------------------------
# A student asked why the raster warps when the framebuffer's aspect ratio
# differs from NDC's.  Answer it by SHOWING it: bracket the existing demo with
# a framebuffer<->NDC warp.  A configurable W x H pixel grid (default 20x10) in
# world space, starting with its bottom-left corner at the origin.  Step 1
# translates it to centred (x in +-W/2, y in +-H/2 -- 20x10 is a 2:1 box).
# Then it warps in x,y into the [-1,1] NDC square (x and y scaled by DIFFERENT
# amounts, 1/10 vs 1/5 -- that inequality IS the warp), then extrudes in z to
# the NDC cube, which STAYS on screen (coincident with the NDC cube) while the
# demo runs unchanged; afterwards the framebuffer and the squashed scene warp
# back out together -- NDC square -> prism (aspect) then centre -> bottom-left
# origin (the glViewport scale+offset).  The pixel W/H also drives the demo's
# own frustum aspect, so it is one number everywhere.
FB_W_DEFAULT: int = 20
FB_H_DEFAULT: int = 10
PROLOGUE_HOLD: float = 2.0  # show the flat grid before it starts moving
MORPH_DUR: float = scene.step_duration  # each warp phase, at the demo's tempo
PROLOGUE_DUR: float = PROLOGUE_HOLD + 3.0 * MORPH_DUR  # translate/warp/extrude
DEMO_DUR: float = animation.timeline.duration  # the untouched existing demo
EPILOGUE_WARP: float = MORPH_DUR  # NDC square -> centred prism (un-warp aspect)
EPILOGUE_TRANSLATE: float = MORPH_DUR  # centre -> framebuffer bottom-left
EPILOGUE_HOLD: float = 3.0
TOTAL_DUR: float = (
    PROLOGUE_DUR + DEMO_DUR + EPILOGUE_WARP + EPILOGUE_TRANSLATE + EPILOGUE_HOLD
)

# --- GL setup --------------------------------------------------------------

# This file is a program, not a module: from here on it acquires resources (a
# window, a GL context) and then runs its own loop.  A tool that imports it to
# inspect it stops here instead of opening a window.
if __name__ != "__main__":
    sys.exit(
        "this is a visualization, run it directly rather than importing it"
    )


window, impl, imguiio = cayley_gl.setup(
    "Model View Perspective Projection (Cayley)"
)
camera: _p.Camera = cayley_gl.make_camera()
cayley_gl.install_scroll(window, imguiio, camera)
pwd: str = os.path.dirname(os.path.abspath(__file__))
standard_objects: cayley_gl.StandardObjects = cayley_gl.build_standard(
    shader_dir=pwd,
    animated=True,
    project="project_perspective.glsl",
    frustum=cayley_gl.Frustum(aspect_ratio=FB_W_DEFAULT / FB_H_DEFAULT),
)

state: dict[str, typing.Any] = {
    "time": 0.0,
    "speed": 1.0,
    "paused": False,
    "mouse": None,
    "line_width": 2.0,
    "center_on": None,
    "fb_w": FB_W_DEFAULT,
    "fb_h": FB_H_DEFAULT,
}
win_state: cayley_gl.WindowState = cayley_gl.WindowState()


# --- framebuffer grid mesh + its prologue/epilogue morph -------------------
# The mesh is the prism form (x,y in +-half extent, z in [-1,1]); it is drawn
# only in the prologue/epilogue, morphed each frame by a scale matrix.  It
# reuses the static cube pipeline (uniform-colour lines), so its model matrix
# maps the mesh vertices directly.  A DYNAMIC VBO lets W/H be re-configured.
def _grid_vertices() -> np.ndarray:
    return cayley_gl.framebuffer_grid_lines(
        state["fb_w"],
        state["fb_h"],
        state["fb_w"] / 2.0,
        state["fb_h"] / 2.0,
    )


_grid_verts: np.ndarray = _grid_vertices()
_grid_vbo: int = _p.make_vbo(_grid_verts, usage=GL.GL_DYNAMIC_DRAW)
grid: dict[str, int] = {
    "vbo": _grid_vbo,
    "vao": _p.make_vao(
        [
            _p.AttribSpec(
                vbo=_grid_vbo,
                location=standard_objects.cube_pipeline.attr_position,
                size=_p.floats_per_vertex,
                layout=(0, 0),
            )
        ]
    ),
    "n": _grid_verts.size // _p.floats_per_vertex,
}


def rebuild_framebuffer() -> None:
    """Re-upload the pixel grid and re-derive the frustum aspect after the
    configured pixel W/H changed -- one number drives both the grid and the
    demo's own perspective squash."""
    verts: np.ndarray = _grid_vertices()
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, grid["vbo"])
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER,
        _p.glfloat_size * verts.size,
        verts,
        GL.GL_DYNAMIC_DRAW,
    )
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    grid["n"] = verts.size // _p.floats_per_vertex
    fr: cayley_gl.Frustum | None = standard_objects.frustum
    assert fr is not None  # this scene always has a perspective frustum
    fr.aspect_ratio = state["fb_w"] / state["fb_h"]
    standard_objects.rebuild_frustum()


# --- framebuffer morph, as gacalc InvertibleFunctions ----------------------
# Per CLAUDE.md: express transformations with gacalc, animate with `.at()`,
# reverse with `inverse()`; realize to a 4x4 only for GL upload
# (`cayleyscene.to_matrix`).  The grid mesh is the centred prism (+-hw,+-hh).
def _warp(hw: float, hh: float) -> InvertibleFunction:
    """Centred prism -> NDC square: the aspect scale (x by 1/hw, y by 1/hh)."""
    return scale_non_uniform(1.0 / hw, 1.0 / hh, 1.0)


def _place(hw: float, hh: float) -> InvertibleFunction:
    """Centre -> framebuffer bottom-left origin (offset by a half-extent)."""
    return translate(Vector(hw, hh, 0.0))


def _flatten() -> InvertibleFunction:
    """Prism -> flat (z to 0).  Forward-only (a z-scale of 0 is not invertible);
    used only to animate the prologue extrude via ``.at()``."""
    return scale_non_uniform(1.0, 1.0, 0.0)


def _epilogue_ndc_to_fb(t: float) -> InvertibleFunction:
    """The epilogue's NDC -> framebuffer transform (the viewport map): scale the
    NDC square out to the prism by the half-extents, then translate to the
    bottom-left origin -- two phases, animated LINEARLY.  Used for BOTH the
    grid and the scene, so they follow one curve and stay coincident.

    We build the NDC->framebuffer scale directly (``scale_non_uniform(hw, hh,
    1)`` -- the half-extents) rather than ``inverse(_warp).at(t)`` on
    purpose: gacalc's ``inverse(f).at(t) == inverse(f.at(t))`` is a RECIPROCAL
    curve (an ease-in), which is asymmetric with the linear forward prologue.
    Linear matches the prologue and reads as the plain scale-then-translate
    viewport transform.  (Still gacalc + realized via ``to_matrix`` at the GL
    boundary; ``inverse()`` is used elsewhere -- the center-on frame.)"""
    hw: float = state["fb_w"] / 2.0
    hh: float = state["fb_h"] / 2.0
    epi: float = PROLOGUE_DUR + DEMO_DUR
    r_scale: float = cayleyscene.interp(t, epi, EPILOGUE_WARP)
    r_trans: float = cayleyscene.interp(
        t, epi + EPILOGUE_WARP, EPILOGUE_TRANSLATE
    )
    return compose(
        [
            _place(hw, hh).at(r_trans),
            scale_non_uniform(hw, hh, 1.0).at(r_scale),
        ]
    )


def grid_matrix(t: float) -> tuple[np.ndarray, bool]:
    """Model matrix + visibility for the framebuffer grid at global time ``t``.
    Prologue: translate-to-centre -> warp x,y to the NDC square -> extrude z to
    the NDC cube.  Demo: held at the NDC cube (A3).  Epilogue: NDC -> prism ->
    framebuffer bottom-left.  Always visible, so the bool is always ``True``.
    Built from gacalc functions (``.at()`` animates, ``inverse()`` reverses);
    realized to a matrix only here, for GL upload."""
    hw: float = state["fb_w"] / 2.0
    hh: float = state["fb_h"] / 2.0
    if t < PROLOGUE_DUR:
        # bottom-left flat -> centre -> warp to NDC square -> extrude to cube.
        # _place.at(1-tau): starts at the bottom-left offset, fades to centred.
        # _flatten.at(1-ez): starts flat (z*0), fades to the full prism (z*1).
        tau: float = cayleyscene.interp(t, PROLOGUE_HOLD, MORPH_DUR)
        warp: float = cayleyscene.interp(
            t, PROLOGUE_HOLD + MORPH_DUR, MORPH_DUR
        )
        ez: float = cayleyscene.interp(
            t, PROLOGUE_HOLD + 2.0 * MORPH_DUR, MORPH_DUR
        )
        f: InvertibleFunction = compose(
            [
                _warp(hw, hh).at(warp),
                _place(hw, hh).at(1.0 - tau),
                _flatten().at(1.0 - ez),
            ]
        )
        return cayleyscene.to_matrix(f), True
    epi: float = PROLOGUE_DUR + DEMO_DUR
    if t >= epi:
        # Reverse the viewport transform onto the grid: _warp puts the (prism)
        # mesh at NDC, then the SAME ndc->framebuffer transform the scene uses
        # is applied, so the grid outline and squashed scene stay coincident
        # (they would drift apart under different interpolation curves).
        f = compose([_epilogue_ndc_to_fb(t), _warp(hw, hh)])
        return cayleyscene.to_matrix(f), True
    # A3: during the demo the framebuffer STAYS on screen, held at the NDC cube
    # (coincident with the reference cube) rather than disappearing.
    return cayleyscene.to_matrix(_warp(hw, hh)), True


def scene_epilogue_transform(t: float) -> np.ndarray | None:
    """NDC->framebuffer for the demo's OWN geometry during the epilogue: the
    INVERSE of the framebuffer->NDC viewport transform.  ``inverse(_warp)``
    scales NDC->prism and ``_place`` translates to the bottom-left origin, so
    the squashed scene lands inside the framebuffer prism where the pixels are.
    Applied to the view, so it acts AFTER the shader squash.  The reference NDC
    cube is left at +-1 for contrast.  ``None`` outside the epilogue."""
    epi: float = PROLOGUE_DUR + DEMO_DUR
    if t < epi:
        return None
    return cayleyscene.to_matrix(_epilogue_ndc_to_fb(t))


def draw_grid(m: np.ndarray) -> None:
    p: _p.Pipeline = standard_objects.cube_pipeline
    GL.glUseProgram(p.program)
    GL.glBindVertexArray(grid["vao"])
    GL.glUniform3f(p.u_color, 0.2, 0.8, 1.0)  # cyan, distinct from the cube
    ms.set_current_matrix(ms.MatrixStack.model, m)
    _p.set_uniforms(p.u_m, p.u_v, p.u_p)
    GL.glDrawArrays(GL.GL_LINES, 0, grid["n"])


def jump(start: float) -> None:
    state["time"] = start


def _toggle_pause() -> None:
    state["paused"] = not state["paused"]


def _restart() -> None:
    state["time"] = 0.0


def _toggle_graph() -> None:
    win_state.show_graph = not win_state.show_graph


def _focus(node: Space | str | None) -> None:
    state["center_on"] = node


# camera moves in cameraspace (px/pz adjusted by the heading rot_y), shared by
# the Camera menu actions and the WASD keys.
def _cam_forward() -> None:  # -Z cameraspace
    controls.px -= math.sin(controls.rot_y)
    controls.pz -= math.cos(controls.rot_y)
    controls.apply()


def _cam_back() -> None:  # +Z cameraspace
    controls.px += math.sin(controls.rot_y)
    controls.pz += math.cos(controls.rot_y)
    controls.apply()


def _cam_left() -> None:  # -X cameraspace
    controls.px -= math.cos(controls.rot_y)
    controls.pz += math.sin(controls.rot_y)
    controls.apply()


def _cam_right() -> None:  # +X cameraspace
    controls.px += math.cos(controls.rot_y)
    controls.pz -= math.sin(controls.rot_y)
    controls.apply()


def imgui_menubar() -> None:
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        cayley_gl.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Playback", True):
        cayley_gl.menu_action(
            "Resume" if state["paused"] else "Pause",
            "SPACE",
            _toggle_pause,
            selected=state["paused"],
        )
        cayley_gl.menu_action("Restart", "R", _restart)
        _, state["speed"] = imgui.slider_float(
            "Sim Speed", state["speed"], -10.0, 10.0
        )
        imgui.menu_item(
            f"t = {state['time']:.1f}s / {TOTAL_DUR:.0f}s",
            "",
            False,
            False,
        )
        imgui.end_menu()
    if imgui.begin_menu("Camera", True):
        _, camera.r = imgui.slider_float(
            "Camera Radius", camera.r, 10.0, 1000.0
        )
        imgui.separator()
        cam_changed: bool = False
        for label, key in (
            ("X_Worldspace", "px"),
            ("Y_Worldspace", "py"),
            ("Z_Worldspace", "pz"),
        ):
            c, v = imgui.slider_float(
                label, getattr(controls, key), -200.0, 200.0
            )
            setattr(controls, key, v)
            cam_changed = cam_changed or c
        c, controls.rot_x = imgui.slider_float(
            "Rot X", controls.rot_x, -math.pi, math.pi
        )
        cam_changed = cam_changed or c
        c, controls.rot_y = imgui.slider_float(
            "Rot Y", controls.rot_y, -math.pi, math.pi
        )
        cam_changed = cam_changed or c
        if cam_changed:
            controls.apply()
        imgui.separator()
        cayley_gl.menu_action("Forward (-Z cam)", "W", _cam_forward)
        cayley_gl.menu_action("Back (+Z cam)", "S", _cam_back)
        cayley_gl.menu_action("Left (-X cam)", "A", _cam_left)
        cayley_gl.menu_action("Right (+X cam)", "D", _cam_right)
        imgui.separator()
        fr_changed: bool = False
        fr: cayley_gl.Frustum | None = standard_objects.frustum
        assert fr is not None  # this scene always has a perspective frustum
        c, fr.field_of_view = imgui.slider_float(
            "Frustum FOV", fr.field_of_view, 5.0, 120.0
        )
        fr_changed = fr_changed or c
        # Frustum aspect is DERIVED from the framebuffer pixel W/H (see the
        # Framebuffer menu), not set here -- it is one number everywhere.
        c, fr.near_z = imgui.slider_float(
            "Frustum near_z", fr.near_z, -200.0, -1.0
        )
        fr_changed = fr_changed or c
        c, fr.far_z = imgui.slider_float(
            "Frustum far_z",
            fr.far_z,
            fr.near_z,
            fr.near_z - 500.0,
        )
        fr_changed = fr_changed or c
        if fr_changed:
            standard_objects.rebuild_frustum()
        imgui.end_menu()
    if imgui.begin_menu("Framebuffer", True):
        fb_changed: bool = False
        c, w_px = imgui.input_int("Width (px)", state["fb_w"])
        if c:
            state["fb_w"] = max(4, min(40, w_px))
            fb_changed = True
        c, h_px = imgui.input_int("Height (px)", state["fb_h"])
        if c:
            state["fb_h"] = max(4, min(40, h_px))
            fb_changed = True
        if fb_changed:
            rebuild_framebuffer()
        imgui.separator()
        # Read-only, and spelled out: which way round the ratio goes is easy to
        # forget, so show it as width/height, both fraction and value.
        aspect: float = state["fb_w"] / state["fb_h"]
        imgui.menu_item("aspect = width / height", "", False, False)
        imgui.menu_item(
            f"       = {state['fb_w']} / {state['fb_h']} = {aspect:.3f}",
            "",
            False,
            False,
        )
        imgui.end_menu()
    if imgui.begin_menu("View From", True):
        for label, node in FOCUS:
            cayley_gl.menu_action(
                label,
                "",
                lambda node=node: _focus(node),
                selected=(state["center_on"] == node),
            )
        # "Framebuffer" is only selectable once the framebuffer has settled back
        # at its original bottom-left space -- after the epilogue warp AND
        # translate finish.  Derived from the phase durations, so it still
        # means "after the framebuffer is home" if more steps are added later.
        fb_settled: bool = state["time"] >= (
            PROLOGUE_DUR + DEMO_DUR + EPILOGUE_WARP + EPILOGUE_TRANSLATE
        )
        cayley_gl.menu_action(
            "Framebuffer",
            "",
            lambda: _focus(FB_FOCUS),
            selected=(state["center_on"] == FB_FOCUS),
            enabled=fb_settled,
        )
        imgui.end_menu()
    if imgui.begin_menu("View", True):
        cayley_gl.menu_action(
            "Fullscreen",
            "F11",
            lambda: cayley_gl.toggle_fullscreen(window, win_state),
            selected=win_state.fullscreen,
        )
        cayley_gl.menu_action(
            "Show Graph", "G", _toggle_graph, selected=win_state.show_graph
        )
        _, state["line_width"] = imgui.slider_float(
            "Line Width", state["line_width"], 1.0, 10.0
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def on_key(
    window: "GLFWWindow", key: int, scancode: int, action: int, mods: int
) -> None:
    cayley_gl.common_key(window, win_state, key, action)
    if action not in (glfw.PRESS, glfw.REPEAT):
        return
    if key == glfw.KEY_W:
        _cam_forward()
    elif key == glfw.KEY_S:
        _cam_back()
    elif key == glfw.KEY_A:
        _cam_left()
    elif key == glfw.KEY_D:
        _cam_right()
    elif action == glfw.PRESS:
        if key == glfw.KEY_SPACE:
            _toggle_pause()
        elif key == glfw.KEY_R:
            _restart()
        elif key == glfw.KEY_G:
            _toggle_graph()


def _bracket_button(
    label: str, start: float, dur: float, t: float
) -> cayleyscene.GuiButton:
    """A graph-panel jump-button for a prologue/epilogue warp step.  ``start``
    is in GLOBAL time, so its jump target needs no offset (unlike the scene's
    own steps, which live in demo-local time)."""
    return cayleyscene.GuiButton(label, start, start <= t < start + dur)


def prologue_group(t: float) -> cayleyscene.GuiGroup:
    return cayleyscene.GuiGroup(
        "Framebuffer -> NDC (prologue)",
        [
            _bracket_button("Translate to center", PROLOGUE_HOLD, MORPH_DUR, t),
            _bracket_button(
                "Warp to NDC square (/W /H)",
                PROLOGUE_HOLD + MORPH_DUR,
                MORPH_DUR,
                t,
            ),
            _bracket_button(
                "Extrude in Z (+-1)",
                PROLOGUE_HOLD + 2.0 * MORPH_DUR,
                MORPH_DUR,
                t,
            ),
        ],
    )


def epilogue_group(t: float) -> cayleyscene.GuiGroup:
    start: float = PROLOGUE_DUR + DEMO_DUR
    return cayleyscene.GuiGroup(
        "NDC -> Framebuffer (epilogue)",
        [
            _bracket_button("NDC -> Prism (*W *H)", start, EPILOGUE_WARP, t),
            _bracket_button(
                "Center -> bottom-left",
                start + EPILOGUE_WARP,
                EPILOGUE_TRANSLATE,
                t,
            ),
        ],
    )


def graph_panel(t: float) -> None:
    if not win_state.show_graph:
        return
    demo_t: float = max(0.0, min(DEMO_DUR, t - PROLOGUE_DUR))

    # The scene's timeline is demo-local; the panel runs in global time, so a
    # scene button's jump target is shifted back into global time here.
    def jump_demo(start: float) -> None:
        jump(start + PROLOGUE_DUR)

    imgui.set_next_window_size(
        imgui.ImVec2(470, 480), imgui.Cond_.first_use_ever
    )
    imgui.set_next_window_bg_alpha(0.7)
    imgui.begin("Cayley Graph", True)
    # The framebuffer<->NDC narration is kept at the TOP of the panel, above the
    # scene's own two trees (its jumps are already in global time).
    cayley_gl.render_tree(prologue_group(t), jump)
    cayley_gl.render_tree(epilogue_group(t), jump)
    imgui.set_next_item_open(True, imgui.Cond_.once)
    if imgui.tree_node("From World Space, Against Arrows, Read Bottom Up"):
        for grp in animation.frame_tree(demo_t):
            cayley_gl.render_tree(grp, jump_demo)
        imgui.tree_pop()
    imgui.set_next_item_open(True, imgui.Cond_.once)
    if imgui.tree_node("Towards NDC, With Arrows, Top Down Reading"):
        for grp in animation.ndc_tree(demo_t):
            cayley_gl.render_tree(grp, jump_demo)
        imgui.tree_pop()
    imgui.end()


def frame(w: int, h: int) -> None:
    if not state["paused"]:
        state["time"] = min(TOTAL_DUR, state["time"] + state["speed"] / 60.0)
    t: float = state["time"]
    # The existing demo is driven by demo-local time; the prologue plays before
    # it (demo frozen at 0) and the epilogue after it (frozen at its end).
    demo_t: float = max(0.0, min(DEMO_DUR, t - PROLOGUE_DUR))
    graph_panel(t)

    # Drive the perspective squash from the timeline, not hardcoded shader
    # times: one progress value per squash step (Animation.gpu_progress) ->
    # the shader `squash_ratios`.  Set on the mesh + frustum pipelines; the
    # axis pipeline is left at 0 so axes never squash.  Change a dwell or add
    # a step and this follows -- no absolute times anywhere.
    prog: list[float] = [r for _label, r in animation.gpu_progress(demo_t)]
    sx: float = prog[0]
    sy: float = prog[1]
    tz: float = prog[2]
    sc: float = prog[3]
    p: _p.Pipeline | None
    for p in (
        standard_objects.triangle_pipeline,
        standard_objects.volume_pipeline,
    ):
        if p is not None and p.u_squash != -1:
            GL.glUseProgram(p.program)
            GL.glUniform4f(p.u_squash, sx, sy, tz, sc)

    state["mouse"] = cayley_gl.orbit_input(
        window, imguiio, camera, state["mouse"]
    )
    cayley_gl.setup_orbit_view(camera, w, h)

    inv: np.ndarray = cayleyscene.to_matrix(animation.inverse_transform(demo_t))

    # Center AND ORIENT the view on the entity's drawn frame (inv @ placement):
    # view = orbit @ inverse(frame), so the entity sits at the orbit center
    # axis-aligned (for the camera, you see from its orientation) and you orbit
    # around its own frame -- not just translate to its position.
    if state["center_on"] == FB_FOCUS:
        # Orbit around the framebuffer's current centre (its display-space
        # position -- the translation column of its model matrix).  Only
        # selectable once it has settled at the bottom-left prism, so this
        # centres on that; it stays axis-aligned (the framebuffer has no
        # rotation), so translating the view by -centre is enough.
        fb_m: np.ndarray = grid_matrix(t)[0]
        centre: Vector = Vector(
            float(fb_m[0, 3]), float(fb_m[1, 3]), float(fb_m[2, 3])
        )
        ms.multiply(
            ms.MatrixStack.view,
            cayleyscene.to_matrix(inverse(translate(centre))),
        )
    elif state["center_on"]:
        # gacalc inverse of the entity's frame (the world->camera inverse
        # composed with its placement), realized to a matrix for the view stack
        # -- not np.linalg.inv (CLAUDE.md: express transforms with gacalc).
        frame_fn: InvertibleFunction = compose(
            [
                animation.inverse_transform(demo_t),
                animation.transform(state["center_on"], demo_t),
            ]
        )
        ms.multiply(
            ms.MatrixStack.view, cayleyscene.to_matrix(inverse(frame_fn))
        )

    # world reference (un-morphed), with layered depth clears
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_ground()
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_cube()
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    # the camera, drawn as an object (with its own ground/frustum/axis/cube)
    if demo_t >= animation.timeline.arrival_time(Space.camera):
        cam_frame: np.ndarray = inv @ cayleyscene.to_matrix(
            animation.transform(Space.camera, demo_t)
        )
        ms.set_current_matrix(ms.MatrixStack.model, cam_frame)
        standard_objects.draw_ground()
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        ry: float = (
            animation.timeline.arrival_time(Space.camera) + scene.step_duration
        )
        if demo_t >= ry:
            standard_objects.draw_frustum(demo_t, state["line_width"], w, h)
        standard_objects.draw_axis()
        standard_objects.draw_cube()
        # A4: the camera's own NDC cube carries the framebuffer pixel grid too
        # (held at the NDC form -- the cube with pixels -- in the camera frame).
        cam_hw: float = state["fb_w"] / 2.0
        cam_hh: float = state["fb_h"] / 2.0
        draw_grid(cam_frame @ cayleyscene.to_matrix(_warp(cam_hw, cam_hh)))

    # world axis: bright before paddle1 builds, grayed after
    ms.set_current_matrix(ms.MatrixStack.model, inv)
    standard_objects.draw_axis(
        grayed=demo_t >= animation.timeline.arrival_time(Space.paddle1)
    )

    # the object-placement tree (camera skipped -- drawn above).  In the
    # epilogue the whole placed scene, squashed into NDC, scales back out to the
    # framebuffer prism -- injected into the view so it applies AFTER the shader
    # squash (which outputs NDC); the reference cube above stays at +-1.
    epi: np.ndarray | None = scene_epilogue_transform(t)
    with ms.push_matrix(ms.MatrixStack.view):
        if epi is not None:
            ms.multiply(ms.MatrixStack.view, epi)
        for space, mesh in DRAW.items():
            m: np.ndarray = inv @ cayleyscene.to_matrix(
                animation.transform(space, demo_t)
            )
            ms.set_current_matrix(ms.MatrixStack.model, m)
            if animation.axis_visible(space, demo_t):
                standard_objects.draw_axis()
            if animation.geometry_visible(space, demo_t):
                ms.set_current_matrix(ms.MatrixStack.model, m)
                standard_objects.draw_mesh(mesh, demo_t)

    # the framebuffer pixel grid: on top, warping in the prologue/epilogue and
    # held at the NDC cube during the demo (A3 -- always visible now).
    grid_m, grid_visible = grid_matrix(t)
    if grid_visible:
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        draw_grid(grid_m)


cayley_gl.run_loop(window, impl, frame, imgui_menubar, on_key)
