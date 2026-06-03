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
from enum import Enum, auto

import glfw
import numpy as np
import OpenGL.GL as GL

from modelviewprojection import pyMatrixStack as ms
from modelviewprojection.mathutils import (
    Vector3D,
    rotate_x,
    rotate_y,
    rotate_z,
    translate,
)
from modelviewprojection.mvpvisualization import (
    cayley_gl,
    cayleygraph,
    cayleyscene,
)

# imgui via cayley_gl so glfw + OpenGL.GL import BEFORE imgui_bundle (its own GL
# loader must come after, or PyOpenGL's context tracking breaks at window setup).
imgui = cayley_gl.imgui


# --- the scene, declared -- spaces are enum members; the whole (immutable,
# acyclic) graph is passed at once.  The camera edge is named so the editable
# virtual camera can rewrite its Steps' fn in place.
class Space(Enum):
    world = auto()
    paddle1 = auto()
    square = auto()
    paddle2 = auto()
    camera = auto()


camera_edge = cayleygraph.Edge(
    src=Space.camera,
    dst=Space.world,
    steps=[
        ("T", translate(Vector3D(-1.5, 0.0, 8.5))),
        ("R_y", rotate_y(math.radians(25.0))),
        ("R_x", rotate_x(math.radians(15.0))),
    ],
)

graph = cayleygraph.CayleyGraph(
    [
        cayleygraph.Edge(
            src=Space.paddle1,
            dst=Space.world,
            steps=[
                ("T", translate(Vector3D(-9.0, 1.0, 0.0))),
                ("R_z", rotate_z(math.radians(45.0))),
            ],
        ),
        cayleygraph.Edge(
            src=Space.square,
            dst=Space.paddle1,
            steps=[
                ("T_-Z", translate(Vector3D(0.0, 0.0, -5.0))),
                ("R_Z", rotate_z(math.radians(30.0))),
                ("T_X", translate(Vector3D(1.5, 0.0, 0.0))),
                ("R2_Z", rotate_z(math.radians(90.0))),
            ],
        ),
        cayleygraph.Edge(
            src=Space.paddle2,
            dst=Space.world,
            steps=[
                ("T", translate(Vector3D(9.0, 0.5, 0.0))),
                ("R_z", rotate_z(math.radians(-20.0))),
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
animation = cayleyscene.Animation(scene)
controls = cayleyscene.CameraControls(
    translate_step=camera_edge.steps[0],
    rot_y_step=camera_edge.steps[1],
    rot_x_step=camera_edge.steps[2],
    px=-1.5,
    py=0.0,
    pz=8.5,
    rot_y=math.radians(25.0),
    rot_x=math.radians(15.0),
)
DRAW = {
    Space.paddle1: "paddle1",
    Space.square: "square",
    Space.paddle2: "paddle2",
}
# (button label, node to center on; None centers on the origin / NDC)
FOCUS = [
    ("NDC", None),
    ("Paddle1", Space.paddle1),
    ("Square", Space.square),
    ("Paddle2", Space.paddle2),
    ("Camera", Space.camera),
]

# --- GL setup --------------------------------------------------------------

window, impl, imguiio = cayley_gl.setup(
    "Model View Perspective Projection (Cayley)"
)
camera = cayley_gl.make_camera()
cayley_gl.install_scroll(window, imguiio, camera)
pwd = os.path.dirname(os.path.abspath(__file__))
standard_objects = cayley_gl.build_standard(
    shader_dir=pwd,
    animated=True,
    project="project_perspective.glsl",
    frustum=cayley_gl.Frustum(),
)

state = {
    "time": 0.0,
    "speed": 1.0,
    "paused": False,
    "mouse": None,
    "line_width": 2.0,
    "center_on": None,
}
win_state = cayley_gl.WindowState()


def jump(start):
    state["time"] = start


def _toggle_pause():
    state["paused"] = not state["paused"]


def _restart():
    state["time"] = 0.0


def _toggle_graph():
    win_state.show_graph = not win_state.show_graph


def _focus(node):
    state["center_on"] = node


# camera moves in cameraspace (px/pz adjusted by the heading rot_y), shared by
# the Camera menu actions and the WASD keys.
def _cam_forward():  # -Z cameraspace
    controls.px -= math.sin(controls.rot_y)
    controls.pz -= math.cos(controls.rot_y)
    controls.apply()


def _cam_back():  # +Z cameraspace
    controls.px += math.sin(controls.rot_y)
    controls.pz += math.cos(controls.rot_y)
    controls.apply()


def _cam_left():  # -X cameraspace
    controls.px -= math.cos(controls.rot_y)
    controls.pz += math.sin(controls.rot_y)
    controls.apply()


def _cam_right():  # +X cameraspace
    controls.px += math.cos(controls.rot_y)
    controls.pz -= math.sin(controls.rot_y)
    controls.apply()


def imgui_menubar():
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
        imgui.separator()
        cam_changed = False
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
        fr_changed = False
        c, standard_objects.frustum.field_of_view = imgui.slider_float(
            "Frustum FOV", standard_objects.frustum.field_of_view, 5.0, 120.0
        )
        fr_changed = fr_changed or c
        c, standard_objects.frustum.aspect_ratio = imgui.slider_float(
            "Frustum Aspect", standard_objects.frustum.aspect_ratio, 0.1, 3.0
        )
        fr_changed = fr_changed or c
        c, standard_objects.frustum.near_z = imgui.slider_float(
            "Frustum near_z", standard_objects.frustum.near_z, -200.0, -1.0
        )
        fr_changed = fr_changed or c
        c, standard_objects.frustum.far_z = imgui.slider_float(
            "Frustum far_z",
            standard_objects.frustum.far_z,
            standard_objects.frustum.near_z,
            standard_objects.frustum.near_z - 500.0,
        )
        fr_changed = fr_changed or c
        if fr_changed:
            standard_objects.rebuild_frustum()
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


def on_key(window, key, scancode, action, mods):
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


def graph_panel(t):
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


def frame(w, h):
    if not state["paused"]:
        state["time"] = min(
            animation.timeline.duration, state["time"] + state["speed"] / 60.0
        )
    t = state["time"]
    graph_panel(t)

    state["mouse"] = cayley_gl.orbit_input(
        window, imguiio, camera, state["mouse"]
    )
    cayley_gl.setup_orbit_view(camera, w, h)

    inv = cayleyscene.to_matrix(animation.inverse_transform(t))

    # Center AND ORIENT the view on the entity's drawn frame (inv @ placement):
    # view = orbit @ inverse(frame), so the entity sits at the orbit center
    # axis-aligned (for the camera, you see from its orientation) and you orbit
    # around its own frame -- not just translate to its position.
    if state["center_on"]:
        frame = inv @ cayleyscene.to_matrix(
            animation.transform(state["center_on"], t)
        )
        ms.multiply(ms.MatrixStack.view, np.linalg.inv(frame))

    # world reference (un-morphed), with layered depth clears
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_ground()
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    standard_objects.draw_cube()
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    # the camera, drawn as an object (with its own ground/frustum/axis/cube)
    if t >= animation.timeline.arrival_time(Space.camera):
        ms.set_current_matrix(
            ms.MatrixStack.model,
            inv @ cayleyscene.to_matrix(animation.transform(Space.camera, t)),
        )
        standard_objects.draw_ground()
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        ry = animation.timeline.arrival_time(Space.camera) + scene.step_duration
        if t >= ry:
            standard_objects.draw_frustum(t, state["line_width"], w, h)
        standard_objects.draw_axis()
        standard_objects.draw_cube()

    # world axis: bright before paddle1 builds, grayed after
    ms.set_current_matrix(ms.MatrixStack.model, inv)
    standard_objects.draw_axis(
        grayed=t >= animation.timeline.arrival_time(Space.paddle1)
    )

    # the object-placement tree (camera skipped -- drawn above)
    for space, mesh in DRAW.items():
        m = inv @ cayleyscene.to_matrix(animation.transform(space, t))
        ms.set_current_matrix(ms.MatrixStack.model, m)
        if animation.axis_visible(space, t):
            standard_objects.draw_axis()
        if animation.geometry_visible(space, t):
            ms.set_current_matrix(ms.MatrixStack.model, m)
            standard_objects.draw_mesh(mesh, t)


cayley_gl.run_loop(window, impl, frame, imgui_menubar, on_key)
