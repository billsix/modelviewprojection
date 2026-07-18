# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""modelview2d, on the Cayley-graph engine.

The 2D demo.  The scene camera is FLAT 2D ORTHOGRAPHIC -- viewed head-on down
-z, no orbit/rotation (``setup_ortho_2d_view``); the "NDC" checkbox just zooms
the ortho extent (15 -> 1).  Everything lives in the XY plane, so:
  * the square has no z-translate (3 steps),
  * the virtual camera only translates (1 step, no rotation),
  * ``Camera->NDC`` is a single ``Scale`` (``project_modelview2d.glsl``).

As each coordinate frame is built it shows its own *graph paper* (the local grid
drawn flat in XY) plus its axis; once built, its geometry.  The virtual camera
is drawn with its *view volume* -- a ±10 rectangular prism (flat, in 2D) that
the squash scales by 1/10 down onto the ±1 NDC square."""

import math
import os
import typing
from enum import Enum, auto

import glfw
import OpenGL.GL as GL

from modelviewprojection import pyMatrixStack as ms
from modelviewprojection.cayley import (
    cayleygraph,
    cayleyscene,
)
from modelviewprojection.mathutils import (
    Vector3,
    rotate_y,
    rotate_z,
    translate,
)
from modelviewprojection.mvpvisualization import (
    cayley_gl,
)

if typing.TYPE_CHECKING:
    # glfw types every window parameter as `_GLFWwindowPointerT`; it is private
    # and absent at runtime, so alias it here for the annotations below.
    from glfw import _GLFWwindowPointerT

    GLFWWindow = _GLFWwindowPointerT


imgui = cayley_gl.imgui


class Space(Enum):
    world = auto()
    paddle1 = auto()
    square = auto()
    paddle2 = auto()
    camera = auto()


# 2D camera: a position only -- no rotation, so the edge has a single step.
camera_edge = cayleygraph.Edge(
    src=Space.camera,
    dst=Space.world,
    steps=[("T", translate(Vector3(-1.5, 2.0, 0.0)))],
)

graph = cayleygraph.CayleyGraph(
    [
        cayleygraph.Edge(
            src=Space.paddle1,
            dst=Space.world,
            steps=[
                ("T", translate(Vector3(-9.0, 1.0, 0.0))),
                ("R", rotate_z(math.radians(45.0))),
            ],
        ),
        # 2D square: no z-translate -- rotate-around, slide out, rotate.
        cayleygraph.Edge(
            src=Space.square,
            dst=Space.paddle1,
            steps=[
                ("R1", rotate_z(math.radians(30.0))),
                ("T_X", translate(Vector3(1.5, 0.0, 0.0))),
                ("R2", rotate_z(math.radians(90.0))),
            ],
        ),
        cayleygraph.Edge(
            src=Space.paddle2,
            dst=Space.world,
            steps=[
                ("T", translate(Vector3(9.0, 0.5, 0.0))),
                ("R", rotate_z(math.radians(-20.0))),
            ],
        ),
        camera_edge,
    ]
)

scene = cayleyscene.Scene(
    graph=graph,
    root=Space.world,
    coordinate_frames=[
        cayleyscene.CoordinateFrame(
            space=Space.paddle1,
            parent=Space.world,
            geometry="paddle1",
            dwell_before=5.0,
        ),
        cayleyscene.CoordinateFrame(
            space=Space.square,
            parent=Space.paddle1,
            geometry="square",
            dwell_before=5.0,
        ),
        cayleyscene.CoordinateFrame(
            space=Space.paddle2,
            parent=Space.world,
            geometry="paddle2",
            dwell_before=5.0,
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
            group_title="Camera->NDC", step_labels=["Scale"]
        ),
    ],
)
animation = cayleyscene.Animation(scene)
DRAW = {
    Space.paddle1: "paddle1",
    Space.square: "square",
    Space.paddle2: "paddle2",
}

window, impl, imguiio = cayley_gl.setup("Model View 2D (Cayley)")
# no camera/orbit: the 2D view is flat (setup_ortho_2d_view), zoomed by the
# NDC checkbox, not orbited.
# project_modelview2d squashes x/y by 1/10; the camera's view volume is a flat
# ±10 rectangular prism (near==far -> a square in 2D) that scales onto ±1 NDC.
pwd = os.path.dirname(os.path.abspath(__file__))
standard_objects = cayley_gl.build_standard(
    shader_dir=pwd,
    animated=True,
    project="project_modelview2d.glsl",
    rect_prism=cayley_gl.RectangularPrism(
        half_size=10.0, near_z=0.0, far_z=0.0
    ),
)

# the grid drawn flat in the XY plane (its default lies in XZ).
GROUND_ROT = cayleyscene.to_matrix(
    rotate_y(math.radians(90.0)) @ rotate_z(math.radians(90.0))
)
cam_pos = {"x": -1.5, "y": 2.0, "z": 0.0}
state: dict[str, typing.Any] = {
    "time": 0.0,
    "speed": 1.0,
    "paused": False,
    "ndc": False,
    "line_width": 2.0,
}
win_state = cayley_gl.WindowState()


def jump(start: float) -> None:
    state["time"] = start


def apply_camera() -> None:
    camera_edge.steps[0].fn = translate(
        Vector3(cam_pos["x"], cam_pos["y"], cam_pos["z"])
    )


def _toggle_pause() -> None:
    state["paused"] = not state["paused"]


def _restart() -> None:
    state["time"] = 0.0


def _toggle_graph() -> None:
    win_state.show_graph = not win_state.show_graph


def _toggle_ndc() -> None:
    state["ndc"] = not state["ndc"]


# 2D camera has no rotation, so cameraspace == worldspace: WASD nudge x/y.
def _cam_move(dx: float, dy: float) -> None:
    cam_pos["x"] += dx
    cam_pos["y"] += dy
    apply_camera()


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
            f"t = {state['time']:.1f}s / {animation.timeline.duration:.0f}s",
            "",
            False,
            False,
        )
        imgui.end_menu()
    if imgui.begin_menu("Camera", True):  # flat 2D: position only, no orbit
        changed = False
        for label, key in (
            ("X_Worldspace", "x"),
            ("Y_Worldspace", "y"),
            ("Z_Worldspace", "z"),
        ):
            c, cam_pos[key] = imgui.slider_float(
                label, cam_pos[key], -25.0, 25.0
            )
            changed = changed or c
        if changed:
            apply_camera()
        imgui.separator()
        cayley_gl.menu_action("Up (+Y)", "W", lambda: _cam_move(0.0, 1.0))
        cayley_gl.menu_action("Down (-Y)", "S", lambda: _cam_move(0.0, -1.0))
        cayley_gl.menu_action("Left (-X)", "A", lambda: _cam_move(-1.0, 0.0))
        cayley_gl.menu_action("Right (+X)", "D", lambda: _cam_move(1.0, 0.0))
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
        # zoom the ortho extent down to the NDC square (15 -> 1)
        cayley_gl.menu_action(
            "NDC (zoom)", "N", _toggle_ndc, selected=state["ndc"]
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
        _cam_move(0.0, 1.0)
    elif key == glfw.KEY_S:
        _cam_move(0.0, -1.0)
    elif key == glfw.KEY_A:
        _cam_move(-1.0, 0.0)
    elif key == glfw.KEY_D:
        _cam_move(1.0, 0.0)
    elif action == glfw.PRESS:
        if key == glfw.KEY_SPACE:
            _toggle_pause()
        elif key == glfw.KEY_R:
            _restart()
        elif key == glfw.KEY_G:
            _toggle_graph()
        elif key == glfw.KEY_N:
            _toggle_ndc()


def graph_panel(t: float) -> None:
    if not win_state.show_graph:
        return
    imgui.set_next_window_size(
        imgui.ImVec2(470, 480), imgui.Cond_.first_use_ever
    )
    imgui.set_next_window_bg_alpha(0.7)
    imgui.begin("Cayley Graph", True)
    imgui.set_next_item_open(True, imgui.Cond_.once)
    if imgui.tree_node("From World Space, Against Arrows, Read Bottom Up"):
        for grp in animation.frame_tree(t):
            cayley_gl.render_tree(grp, jump)
        imgui.tree_pop()
    imgui.set_next_item_open(True, imgui.Cond_.once)
    if imgui.tree_node("Towards NDC, With Arrows, Top Down Reading"):
        for grp in animation.ndc_tree(t):
            cayley_gl.render_tree(grp, jump)
        imgui.tree_pop()
    imgui.end()


def frame(w: int, h: int) -> None:
    if not state["paused"]:
        state["time"] = min(
            animation.timeline.duration, state["time"] + state["speed"] / 60.0
        )
    t = state["time"]
    graph_panel(t)

    cayley_gl.setup_ortho_2d_view(
        w, h, half_extent=1.0 if state["ndc"] else 15.0
    )
    GL.glDisable(GL.GL_DEPTH_TEST)  # flat 2D -> painter order
    lw = state["line_width"]
    morph = cayleyscene.to_matrix(animation.inverse_transform(t))

    # persistent reference: the ±1 NDC square + the world graph paper
    # (un-morphed)
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_cube()
    ms.set_current_matrix(ms.MatrixStack.model, GROUND_ROT)
    standard_objects.draw_ground()

    # the virtual camera, drawn as an object: its graph paper + axis + the view
    # volume (±10 prism), which the squash scales by 1/10 onto the NDC square.
    if t >= animation.timeline.arrival_time(Space.camera):
        base = morph @ cayleyscene.to_matrix(
            animation.transform(Space.camera, t)
        )
        ms.set_current_matrix(ms.MatrixStack.model, base @ GROUND_ROT)
        standard_objects.draw_ground()
        ms.set_current_matrix(ms.MatrixStack.model, base)
        standard_objects.draw_axis()
        ms.set_current_matrix(ms.MatrixStack.model, base)
        standard_objects.draw_rect_prism(t, lw, w, h)

    # world axis: bright before paddle1 builds, grayed after
    ms.set_current_matrix(ms.MatrixStack.model, morph)
    standard_objects.draw_axis(
        grayed=t >= animation.timeline.arrival_time(Space.paddle1)
    )

    # each frame: while building -> its local graph paper + axis; once built ->
    # its geometry (the mesh squashes with the animation).
    for space, mesh in DRAW.items():
        m = morph @ cayleyscene.to_matrix(animation.transform(space, t))
        if animation.axis_visible(space, t):
            ms.set_current_matrix(ms.MatrixStack.model, m @ GROUND_ROT)
            standard_objects.draw_ground()
            ms.set_current_matrix(ms.MatrixStack.model, m)
            standard_objects.draw_axis()
        if animation.geometry_visible(space, t):
            ms.set_current_matrix(ms.MatrixStack.model, m)
            standard_objects.draw_mesh(mesh, t)


cayley_gl.run_loop(window, impl, frame, imgui_menubar, on_key)
