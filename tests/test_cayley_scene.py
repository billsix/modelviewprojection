# Copyright (c) 2018-2026 William Emerison Six
#
# Tests for modelviewprojection.cayley.cayleyscene (Phase 3 engine core of
# tasks/cayley-graph-datastructure.md).  Headless parity: the engine's derived
# timeline + live transforms must match modelviewperspectiveprojection's
# hand-coded arithmetic.  No display.

from __future__ import annotations

import math

import numpy as np

from modelviewprojection.cayley import cayleygraph, cayleyscene
from modelviewprojection.mathutils import (
    Vector3,
    compose,
    inverse,
    rotate_x,
    rotate_y,
    rotate_z,
    translate,
    uniform_scale,
)

# demo constants (verbatim from modelviewperspectiveprojection.py)
P1_POS = Vector3(-9.0, 1.0, 0.0)
P1_ROT = math.radians(45.0)
SQ_ROT = math.radians(90.0)
ROT_AROUND_P1 = math.radians(30.0)
P2_POS = Vector3(9.0, 0.5, 0.0)
P2_ROT = math.radians(-20.0)
CAM_POS = Vector3(-1.5, 0.0, 8.5)
CAM_ROT_Y = math.radians(25.0)
CAM_ROT_X = math.radians(15.0)

SAMPLES = [
    Vector3(0.0, 0.0, 0.0),
    Vector3(1.0, 1.0, 0.0),
    Vector3(-1.0, -1.0, 0.0),
    Vector3(0.3, -0.7, 0.2),
]


def build_scene() -> cayleyscene.Scene:
    g = cayleygraph.CayleyGraph(
        [
            cayleygraph.Edge(
                "paddle1",
                "world",
                [("T", translate(P1_POS)), ("R_z", rotate_z(P1_ROT))],
            ),
            cayleygraph.Edge(
                "square",
                "paddle1",
                [
                    ("T_-Z", translate(Vector3(0.0, 0.0, -5.0))),
                    ("R_Z", rotate_z(ROT_AROUND_P1)),
                    ("T_X", translate(Vector3(1.5, 0.0, 0.0))),
                    ("R2_Z", rotate_z(SQ_ROT)),
                ],
            ),
            cayleygraph.Edge(
                "paddle2",
                "world",
                [("T", translate(P2_POS)), ("R_z", rotate_z(P2_ROT))],
            ),
            cayleygraph.Edge(
                "camera",
                "world",
                [
                    ("T", translate(CAM_POS)),
                    ("R_y", rotate_y(CAM_ROT_Y)),
                    ("R_x", rotate_x(CAM_ROT_X)),
                ],
            ),
        ]
    )
    return cayleyscene.Scene(
        graph=g,
        root="world",
        coordinate_frames=[
            cayleyscene.CoordinateFrame(
                "paddle1", "world", geometry="paddle1", dwell_before=2.0
            ),
            cayleyscene.CoordinateFrame("square", "paddle1", geometry="square"),
            cayleyscene.CoordinateFrame("paddle2", "world", geometry="paddle2"),
            cayleyscene.CoordinateFrame(
                "camera", "world", geometry="camera", dwell_before=5.0
            ),
        ],
    )


def build_full_scene() -> cayleyscene.Scene:
    """build_scene plus the toward-NDC tail (world->camera inverse + GPU)."""
    scene = build_scene()
    scene.to_ndc = [
        cayleyscene.InverseOperations("world", "camera", "World->Camera"),
        cayleyscene.NonInvertibleTransformation(
            "Frustum->Rectangular Prism",
            ["Squash X", "Squash Y"],
            dwell_before=10.0,
        ),
        cayleyscene.NonInvertibleTransformation(
            "Ortho, Rectangular Prism->NDC", ["T - Center", "Scale"]
        ),
    ]
    scene.end_dwell = 5.0
    return scene


def i(t, start):  # the demo's interp with 5.0s duration
    return cayleyscene.interp(t, start, 5.0)


def assert_same_fn(fa, fb):
    for p in SAMPLES:
        assert fa(p).is_close(fb(p))


# --- timeline derivation ---------------------------------------------------


def test_timeline_start_times_match_demo():
    tl = cayleyscene.Timeline(build_scene())
    starts = [ts.start for ts in tl.steps]
    # paddle1 (dwell 2): 2,7 ; square: 12,17,22,27 ; paddle2: 32,37 ;
    # camera (dwell 5 after paddle2 ends at 42): 47,52,57
    assert starts == [2, 7, 12, 17, 22, 27, 32, 37, 47, 52, 57]
    assert [ts.label for ts in tl.steps[:2]] == ["T", "R_z"]
    assert tl.duration == 62.0


# --- live transforms reproduce the demo arithmetic -------------------------


def test_transform_paddle1_matches_demo():
    animation = cayleyscene.Animation(build_scene())
    for k in range(0, 200):
        t = k * 0.1
        want = compose(
            [translate(P1_POS * i(t, 2)), rotate_z(P1_ROT * i(t, 7))]
        )
        assert_same_fn(animation.transform("paddle1", t).func, want.func)


def test_transform_square_nested_matches_demo():
    animation = cayleyscene.Animation(build_scene())
    for k in range(0, 350):
        t = k * 0.1
        want = compose(
            [
                translate(P1_POS * i(t, 2)),
                rotate_z(P1_ROT * i(t, 7)),
                translate(Vector3(0.0, 0.0, -5.0) * i(t, 12)),
                rotate_z(ROT_AROUND_P1 * i(t, 17)),
                translate(Vector3(1.5, 0.0, 0.0) * i(t, 22)),
                rotate_z(SQ_ROT * i(t, 27)),
            ]
        )
        assert_same_fn(animation.transform("square", t).func, want.func)


def test_transform_paddle2_and_camera_match_demo():
    animation = cayleyscene.Animation(build_scene())
    for k in range(0, 600):
        t = k * 0.1
        p2 = compose(
            [translate(P2_POS * i(t, 32)), rotate_z(P2_ROT * i(t, 37))]
        )
        assert_same_fn(animation.transform("paddle2", t).func, p2.func)
        cam = compose(
            [
                translate(CAM_POS * i(t, 47)),
                rotate_y(CAM_ROT_Y * i(t, 52)),
                rotate_x(CAM_ROT_X * i(t, 57)),
            ]
        )
        assert_same_fn(animation.transform("camera", t).func, cam.func)


# --- node lifecycle (default geometry-reveal policy) -----------------------


def test_axis_and_geometry_visibility_lifecycle():
    animation = cayleyscene.Animation(build_scene())
    # paddle1 built window [2, 12): axis while building, geometry after
    assert animation.axis_visible("paddle1", 5.0)
    assert not animation.geometry_visible("paddle1", 5.0)
    assert not animation.axis_visible("paddle1", 15.0)
    assert animation.geometry_visible("paddle1", 15.0)
    # square built at 32
    assert not animation.geometry_visible("square", 31.0)
    assert animation.geometry_visible("square", 33.0)
    # camera built at 62
    assert animation.axis_visible("camera", 50.0)
    assert animation.geometry_visible("camera", 62.0)


def test_active_label_tracks_animating_substep():
    animation = cayleyscene.Animation(build_scene())
    assert animation.active_label(0.5) is None  # in the leading dwell
    assert animation.active_label(3.0) == "T"  # paddle1 translate
    assert animation.active_label(8.0) == "R_z"  # paddle1 rotate


# --- to_matrix realization for GL ------------------------------------------


def test_camera_controls_edit_edge_steps_in_place():
    # CameraControls rewrites the camera edge Steps' fn in place: the Step
    # identities (and timeline slots) stay valid, and transform + morph follow.
    scene = build_full_scene()
    animation = cayleyscene.Animation(scene)
    cam_edge = scene.graph.path("camera", "world").route[0][0]
    controls = cayleyscene.CameraControls(
        cam_edge.steps[0],
        cam_edge.steps[1],
        cam_edge.steps[2],
        px=-1.5,
        py=0.0,
        pz=8.5,
        rot_y=math.radians(25.0),
        rot_x=math.radians(15.0),
    )
    tstep = cam_edge.steps[0]
    slot_before = animation.timeline.slot(tstep)
    cam_before = animation.transform("camera", 60.0)(Vector3(0.0, 0.0, 0.0))
    morph_before = animation.inverse_transform(80.0)(Vector3(1.0, 1.0, 1.0))

    controls.px, controls.py, controls.pz = 5.0, 2.0, -3.0
    controls.apply()

    assert animation.timeline.slot(tstep) == slot_before  # id(step) unchanged
    assert not animation.transform("camera", 60.0)(Vector3(0, 0, 0)).is_close(
        cam_before
    )
    assert not animation.inverse_transform(80.0)(Vector3(1, 1, 1)).is_close(
        morph_before
    )


def test_to_matrix_realizes_affine_function():
    f = compose(
        [
            translate(Vector3(3.0, 4.0, 5.0)),
            rotate_z(math.radians(30.0)),
            uniform_scale(2.0),
        ]
    )
    transform_matrix = cayleyscene.to_matrix(f)
    for p in SAMPLES:
        got = transform_matrix @ np.array(
            [p.coeff_e_1, p.coeff_e_2, p.coeff_e_3, 1.0]
        )
        want = f(p)
        # float(): want's coefficients can be sympy (rotor rotations go through
        # gacalc magnitude()/sympy.sqrt); np.allclose can't handle an object
        # array.
        assert np.allclose(
            got,
            [
                float(want.coeff_e_1),
                float(want.coeff_e_2),
                float(want.coeff_e_3),
                1.0,
            ],
        )


def test_to_matrix_of_engine_transform_matches_point_application():
    animation = cayleyscene.Animation(build_scene())
    f = animation.transform("square", 20.0)
    transform_matrix = cayleyscene.to_matrix(f)
    for p in SAMPLES:
        got = transform_matrix @ np.array(
            [p.coeff_e_1, p.coeff_e_2, p.coeff_e_3, 1.0]
        )
        want = f(p)
        # float(): want's coefficients can be sympy (rotor rotations go through
        # gacalc magnitude()/sympy.sqrt); np.allclose can't handle an object
        # array.
        assert np.allclose(
            got,
            [
                float(want.coeff_e_1),
                float(want.coeff_e_2),
                float(want.coeff_e_3),
                1.0,
            ],
        )


# --- projection tail: timeline, world->camera morph, GPU steps -------------


def test_full_timeline_including_morph_and_gpu():
    tl = cayleyscene.Timeline(build_full_scene())
    placement_starts = [ts.start for ts in tl.steps]
    assert placement_starts == [2, 7, 12, 17, 22, 27, 32, 37, 47, 52, 57]
    # world->camera inverse substeps (camera edge T, R_y, R_x) at 62, 67, 72
    ((track),) = tl.inverse_tracks
    assert [start for _s, start, _d in track.timed] == [62, 67, 72]
    assert track.forward is False
    # GPU squash/ortho: frustum_pause(10) then 87, 92, 97, 102
    assert [g.start for g in tl.gpu_steps] == [87, 92, 97, 102]
    assert tl.duration == 112.0


def test_morph_transform_matches_demo_inverse():
    animation = cayleyscene.Animation(build_full_scene())
    for k in range(550, 800):  # sweep across the morph window (55..80)
        t = k * 0.1
        want = inverse(
            compose(
                [
                    translate(CAM_POS * i(t, 62)),
                    rotate_y(CAM_ROT_Y * i(t, 67)),
                    rotate_x(CAM_ROT_X * i(t, 72)),
                ]
            )
        )
        assert_same_fn(animation.inverse_transform(t).func, want.func)


def test_morph_transform_identity_before_it_starts():
    animation = cayleyscene.Animation(build_full_scene())
    for p in SAMPLES:
        assert animation.inverse_transform(30.0)(p).is_close(p)


def test_gpu_progress():
    animation = cayleyscene.Animation(build_full_scene())
    prog = dict(animation.gpu_progress(89.0))  # squash_x in [87,92]
    assert math.isclose(prog["Squash X"], 0.4)
    assert prog["Squash Y"] == 0.0
    prog = dict(animation.gpu_progress(100.0))  # T-Center in [97,102]
    assert prog["Squash X"] == 1.0
    assert math.isclose(prog["T - Center"], 0.6)
    assert prog["Scale"] == 0.0


# --- imgui-tree data -------------------------------------------------------


def test_placement_tree_structure_and_nesting():
    animation = cayleyscene.Animation(build_full_scene())
    tops = animation.frame_tree(3.0)
    assert [g.title for g in tops] == [
        "paddle1->world",
        "paddle2->world",
        "camera->world",
    ]
    paddle1 = tops[0]
    assert [b.label for b in paddle1.buttons] == ["T", "R_z"]
    assert [b.start for b in paddle1.buttons] == [2, 7]
    # square nests under paddle1
    assert [c.title for c in paddle1.children] == ["square->paddle1"]
    # at t=3, paddle1's T is the active substep
    assert paddle1.buttons[0].active
    assert not paddle1.buttons[1].active


def test_ndc_tree_structure_and_reverse_order():
    animation = cayleyscene.Animation(build_full_scene())
    groups = animation.ndc_tree(64.0)  # T^{-1} active (62..67)
    assert [g.title for g in groups] == [
        "World->Camera",
        "Frustum->Rectangular Prism",
        "Ortho, Rectangular Prism->NDC",
    ]
    # outermost-first (reverse of time order), inverse-labeled
    w2c = groups[0]
    assert [b.label for b in w2c.buttons] == ["R_x^{-1}", "R_y^{-1}", "T^{-1}"]
    assert [b.start for b in w2c.buttons] == [72, 67, 62]
    assert w2c.buttons[2].active  # T^{-1} at t=64
    # GPU groups also reverse-time order
    assert [b.label for b in groups[1].buttons] == ["Squash Y", "Squash X"]
    assert [b.label for b in groups[2].buttons] == ["Scale", "T - Center"]
