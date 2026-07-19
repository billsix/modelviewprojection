# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""model, on the Cayley-graph engine.  The demo OWNS its choreography + imgui
panel; ``cayley_gl`` supplies only the generic mechanisms.  Object-placement
(paddle1 -> square nested -> paddle2), static perspective, one tree."""

import math
import os
import typing
from enum import Enum, auto

import glfw

from modelviewprojection import matrix_stack as ms
from modelviewprojection.cayley import (
    cayleygraph,
    cayleyscene,
)
from modelviewprojection.mathutils import (
    Vector3,
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


# imgui via cayley_gl so glfw + OpenGL.GL import BEFORE imgui_bundle (its own GL
# loader must come after, or PyOpenGL's context tracking breaks at window
# setup).
imgui = cayley_gl.imgui


# --- the scene, declared -- spaces are enum members, the whole (immutable,
# acyclic) graph is passed at once.
class Space(Enum):
    world = auto()
    paddle1 = auto()
    square = auto()
    paddle2 = auto()


graph = cayleygraph.CayleyGraph(
    [
        cayleygraph.Edge(
            src=Space.paddle1,
            dst=Space.world,
            steps=[
                ("T", translate(Vector3(-9.0, 1.0, 0.0))),
                ("R_z", rotate_z(math.radians(45.0))),
            ],
        ),
        cayleygraph.Edge(
            src=Space.square,
            dst=Space.paddle1,
            steps=[
                ("T_-Z", translate(Vector3(0.0, 0.0, -5.0))),
                ("R_Z", rotate_z(math.radians(30.0))),
                ("T_X", translate(Vector3(1.5, 0.0, 0.0))),
                ("R2_Z", rotate_z(math.radians(90.0))),
            ],
        ),
        cayleygraph.Edge(
            src=Space.paddle2,
            dst=Space.world,
            steps=[
                ("T", translate(Vector3(9.0, 0.5, 0.0))),
                ("R_z", rotate_z(math.radians(-20.0))),
            ],
        ),
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
            space=Space.square, parent=Space.paddle1, geometry="square"
        ),
        cayleyscene.CoordinateFrame(
            space=Space.paddle2, parent=Space.world, geometry="paddle2"
        ),
    ],
)
animation = cayleyscene.Animation(scene)
# node -> mesh name
DRAW = {
    Space.paddle1: "paddle1",
    Space.square: "square",
    Space.paddle2: "paddle2",
}

# --- GL setup --------------------------------------------------------------

window, impl, imguiio = cayley_gl.setup("Model (Cayley)")
camera = cayley_gl.make_camera()
cayley_gl.install_scroll(window, imguiio, camera)
pwd = os.path.dirname(os.path.abspath(__file__))
standard_objects = cayley_gl.build_standard(shader_dir=pwd, animated=False)

state: dict[str, typing.Any] = {
    "time": 0.0,
    "speed": 1.0,
    "paused": False,
    "mouse": None,
}
win_state = cayley_gl.WindowState()


def jump(start: float) -> None:
    state["time"] = start


def _toggle_pause() -> None:
    state["paused"] = not state["paused"]


def _restart() -> None:
    state["time"] = 0.0


def _toggle_graph() -> None:
    win_state.show_graph = not win_state.show_graph


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
    if imgui.begin_menu("Camera", True):
        _, camera.r = imgui.slider_float(
            "Camera Radius", camera.r, 10.0, 1000.0
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
        imgui.end_menu()
    imgui.end_main_menu_bar()


def on_key(
    window: "GLFWWindow", key: int, scancode: int, action: int, mods: int
) -> None:
    cayley_gl.common_key(window, win_state, key, action)
    if action != glfw.PRESS:
        return
    if key == glfw.KEY_SPACE:
        _toggle_pause()
    elif key == glfw.KEY_R:
        _restart()
    elif key == glfw.KEY_G:
        _toggle_graph()


def graph_panel(t: float) -> None:
    if not win_state.show_graph:
        return
    imgui.set_next_window_size(
        imgui.ImVec2(460, 360), imgui.Cond_.first_use_ever
    )
    imgui.set_next_window_bg_alpha(0.7)
    imgui.begin("Cayley Graph", True)
    imgui.set_next_item_open(True, imgui.Cond_.once)
    if imgui.tree_node("From World Space, Against Arrows, Read Bottom Up"):
        for grp in animation.frame_tree(t):
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

    # --- input + view ---
    state["mouse"] = cayley_gl.orbit_input(
        window, imguiio, camera, state["mouse"]
    )
    cayley_gl.setup_orbit_view(camera, w, h)

    # --- draw choreography (this demo's policy, incl. graying) ---
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_cube()
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_ground()
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_axis(
        grayed=t >= animation.timeline.arrival_time(Space.paddle1)
    )

    for space, mesh in DRAW.items():
        m = cayleyscene.to_matrix(animation.transform(space, t))
        ms.set_current_matrix(ms.MatrixStack.model, m)
        if animation.axis_visible(space, t):
            standard_objects.draw_axis()
        if animation.geometry_visible(space, t):
            ms.set_current_matrix(ms.MatrixStack.model, m)
            standard_objects.draw_mesh(mesh)


cayley_gl.run_loop(window, impl, frame, imgui_menubar, on_key)
