# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""coordinatesystems, on the Cayley-graph engine.

Unlike the other ports this one has NO timeline/morph -- it is the interactive
coordinate-system explorer.  Every space is drawn at its FULL transform from the
live (slider-driven) parameters, and the focus buttons re-anchor the view by
walking the graph from world TO the chosen space (``path(world, space)`` -- i.e.
against the placement arrows, the inverse).  No camera object is drawn."""

import math
import os
import sys
from enum import Enum, auto

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PWD))
import cayley_gl  # noqa: E402
import cayleygraph  # noqa: E402
import cayleyscene  # noqa: E402
import glfw  # noqa: E402  (loaded by cayley_gl; needed here for key constants)

import modelviewprojection.pyMatrixStack as ms  # noqa: E402
from modelviewprojection.mathutils import (  # noqa: E402
    Vector3D,
    rotate_z,
    translate,
)

imgui = cayley_gl.imgui


class Space(Enum):
    world = auto()
    paddle1 = auto()
    square = auto()
    paddle2 = auto()


# live parameters -- all start at zero, like the original (keyboard-driven there,
# slider-driven here).
params = {
    "p1x": -9.0,
    "p1y": 1.0,
    "p1rot": 0.0,
    "p2x": 9.0,
    "p2y": 0.5,
    "p2rot": 0.0,
    "around": 0.0,
    "sqrot": 0.0,
}

paddle1_edge = cayleygraph.Edge(
    src=Space.paddle1,
    dst=Space.world,
    steps=[
        ("T", translate(Vector3D(params["p1x"], params["p1y"], 0.0))),
        ("R_z", rotate_z(params["p1rot"])),
    ],
)
# square sits behind paddle1 (z -0.5), rotates around it, slides out, spins.
square_edge = cayleygraph.Edge(
    src=Space.square,
    dst=Space.paddle1,
    steps=[
        ("T_-Z", translate(Vector3D(0.0, 0.0, -0.5))),
        ("R_around", rotate_z(params["around"])),
        ("T_X", translate(Vector3D(1.5, 0.0, 0.0))),
        ("R_sq", rotate_z(params["sqrot"])),
    ],
)
paddle2_edge = cayleygraph.Edge(
    src=Space.paddle2,
    dst=Space.world,
    steps=[
        ("T", translate(Vector3D(params["p2x"], params["p2y"], 0.0))),
        ("R_z", rotate_z(params["p2rot"])),
    ],
)
graph = cayleygraph.CayleyGraph([paddle1_edge, square_edge, paddle2_edge])

DRAW = [
    (Space.paddle1, "paddle1"),
    (Space.square, "square"),
    (Space.paddle2, "paddle2"),
]
FOCUS = [
    ("NDC", None),
    ("Paddle 1", Space.paddle1),
    ("Square", Space.square),
    ("Paddle 2", Space.paddle2),
]


def sync_steps():
    """Rewrite the mutable steps in place from the live ``params`` (structure
    stays immutable; only each step's function changes)."""
    paddle1_edge.steps[0].fn = translate(
        Vector3D(params["p1x"], params["p1y"], 0.0)
    )
    paddle1_edge.steps[1].fn = rotate_z(params["p1rot"])
    square_edge.steps[1].fn = rotate_z(params["around"])
    square_edge.steps[3].fn = rotate_z(params["sqrot"])
    paddle2_edge.steps[0].fn = translate(
        Vector3D(params["p2x"], params["p2y"], 0.0)
    )
    paddle2_edge.steps[1].fn = rotate_z(params["p2rot"])


def frame_of(space):
    """4x4 placing ``space``-local coords into world (along the arrows)."""
    return cayleyscene.to_matrix(graph.path(space, Space.world).function())


window, impl, imguiio = cayley_gl.setup("Coordinate Systems (Cayley)")
camera = cayley_gl.make_camera(r=85.0)
cayley_gl.install_scroll(window, imguiio, camera)
standard_objects = cayley_gl.build_standard(animated=False)

state = {"mouse": None, "line_width": 2.0, "center_on": None}
win_state = cayley_gl.WindowState()


def _focus(node):
    state["center_on"] = node


def imgui_menubar():
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        cayley_gl.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Camera", True):
        _, camera.r = imgui.slider_float(
            "Camera Radius", camera.r, 10.0, 1000.0
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
        imgui.end_menu()
    if imgui.begin_menu(
        "Scene", True
    ):  # live-tweak the coordinate-system params
        if imgui.begin_menu("Paddle 1", True):
            _, params["p1x"] = imgui.slider_float(
                "X", params["p1x"], -20.0, 20.0
            )
            _, params["p1y"] = imgui.slider_float(
                "Y", params["p1y"], -20.0, 20.0
            )
            _, params["p1rot"] = imgui.slider_float(
                "Rotation", params["p1rot"], -math.pi, math.pi
            )
            imgui.end_menu()
        if imgui.begin_menu("Square (rel. Paddle 1)", True):
            _, params["around"] = imgui.slider_float(
                "Rotate around Paddle 1", params["around"], -math.pi, math.pi
            )
            _, params["sqrot"] = imgui.slider_float(
                "Square Rotation", params["sqrot"], -math.pi, math.pi
            )
            imgui.end_menu()
        if imgui.begin_menu("Paddle 2", True):
            _, params["p2x"] = imgui.slider_float(
                "X", params["p2x"], -20.0, 20.0
            )
            _, params["p2y"] = imgui.slider_float(
                "Y", params["p2y"], -20.0, 20.0
            )
            _, params["p2rot"] = imgui.slider_float(
                "Rotation", params["p2rot"], -math.pi, math.pi
            )
            imgui.end_menu()
        imgui.end_menu()
    if imgui.begin_menu("View", True):
        cayley_gl.menu_action(
            "Fullscreen",
            "F11",
            lambda: cayley_gl.toggle_fullscreen(window, win_state),
            selected=win_state.fullscreen,
        )
        _, state["line_width"] = imgui.slider_float(
            "Line Width", state["line_width"], 1.0, 10.0
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def on_key(window, key, scancode, action, mods):
    cayley_gl.common_key(window, win_state, key, action)  # Esc, F11


def frame(w, h):
    sync_steps()

    state["mouse"] = cayley_gl.orbit_input(
        window, imguiio, camera, state["mouse"]
    )
    cayley_gl.setup_orbit_view(camera, w, h)
    # focus: walk world -> space (against the arrows) and post-multiply the view,
    # centering AND orienting on that space.
    if state["center_on"] is not None:
        ms.multiply(
            ms.MatrixStack.view,
            cayleyscene.to_matrix(
                graph.path(Space.world, state["center_on"]).function()
            ),
        )

    # world reference: NDC cube + ground + world axis
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_cube()
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_ground()
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_axis()

    for space, mesh in DRAW:
        ms.set_current_matrix(ms.MatrixStack.model, frame_of(space))
        standard_objects.draw_mesh(mesh)
        ms.set_current_matrix(ms.MatrixStack.model, frame_of(space))
        standard_objects.draw_axis()


cayley_gl.run_loop(window, impl, frame, imgui_menubar, on_key)
