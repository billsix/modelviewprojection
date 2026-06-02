# Copyright (c) 2018-2026 William Emerison Six
#
# Unit tests for mvpVisualization/cayleygraph.py (Phase 2 of
# tasks/cayley-graph-datastructure.md).  Pure math, no display.

from __future__ import annotations

import math

import cayleygraph  # importable via tests/conftest.py sys.path setup
import pytest

from modelviewprojection.mathutils import (
    Vector3D,
    compose,
    inverse,
    rotate_x,
    rotate_y,
    rotate_z,
    translate,
)

# --- a small demo-like scene: square -> paddle1 -> world, and camera -> world -

PADDLE1_POS = Vector3D(-9.0, 1.0, 0.0)
PADDLE1_ROT = math.radians(45.0)
SQUARE_ROT = math.radians(90.0)
ROT_AROUND_P1 = math.radians(30.0)
CAM_POS = Vector3D(-1.5, 0.0, 8.5)
CAM_ROT_Y = math.radians(25.0)
CAM_ROT_X = math.radians(15.0)

SAMPLES = [
    Vector3D(0.0, 0.0, 0.0),
    Vector3D(1.0, 1.0, 0.0),
    Vector3D(-1.0, -1.0, 0.0),
    Vector3D(0.3, -0.7, 0.2),
]


def build_graph() -> cayleygraph.CayleyGraph:
    return cayleygraph.CayleyGraph(
        [
            cayleygraph.Edge(
                "paddle1",
                "world",
                [("T", translate(PADDLE1_POS)), ("R_z", rotate_z(PADDLE1_ROT))],
            ),
            cayleygraph.Edge(
                "square",
                "paddle1",
                [
                    ("T_-Z", translate(Vector3D(0.0, 0.0, -5.0))),
                    ("R_Z", rotate_z(ROT_AROUND_P1)),
                    ("T_X", translate(Vector3D(1.5, 0.0, 0.0))),
                    ("R2_Z", rotate_z(SQUARE_ROT)),
                ],
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


def assert_same_fn(fa, fb):
    for p in SAMPLES:
        assert fa(p).isclose(fb(p))


# --- forward edge ----------------------------------------------------------


def test_forward_single_edge_equals_compose_of_steps():
    g = build_graph()
    got = g.path("paddle1", "world").function()
    want = compose([translate(PADDLE1_POS), rotate_z(PADDLE1_ROT)])
    assert_same_fn(got.func, want.func)


# --- against-arrow edge auto-inverts ---------------------------------------


def test_backward_single_edge_is_the_inverse():
    g = build_graph()
    cam_to_world = g.path("camera", "world").function()
    world_to_cam = g.path("world", "camera").function()
    # world->camera is exactly the inverse of camera->world
    assert_same_fn(world_to_cam.func, inverse(cam_to_world).func)
    # and they round-trip to the identity
    for p in SAMPLES:
        assert world_to_cam(cam_to_world(p)).isclose(p)


def test_round_trip_is_identity_multi_hop():
    g = build_graph()
    there = g.path("square", "camera").function()
    back = g.path("camera", "square").function()
    for p in SAMPLES:
        assert back(there(p)).isclose(p)


# --- multi-hop composition (with and without an against-arrow edge) ---------


def test_multi_hop_all_forward():
    g = build_graph()
    got = g.path("square", "world").function()
    # square->paddle1 applied first (innermost), then paddle1->world
    a = compose(
        [
            translate(Vector3D(0.0, 0.0, -5.0)),
            rotate_z(ROT_AROUND_P1),
            translate(Vector3D(1.5, 0.0, 0.0)),
            rotate_z(SQUARE_ROT),
        ]
    )
    b = compose([translate(PADDLE1_POS), rotate_z(PADDLE1_ROT)])
    want = compose([b, a])
    assert_same_fn(got.func, want.func)


def test_multi_hop_crosses_root_with_one_inverse():
    g = build_graph()
    # square -> paddle1 -> world -> camera : last hop is against camera->world
    got = g.path("square", "camera").function()
    a = compose(
        [
            translate(Vector3D(0.0, 0.0, -5.0)),
            rotate_z(ROT_AROUND_P1),
            translate(Vector3D(1.5, 0.0, 0.0)),
            rotate_z(SQUARE_ROT),
        ]
    )
    b = compose([translate(PADDLE1_POS), rotate_z(PADDLE1_ROT)])
    cam_to_world = compose(
        [translate(CAM_POS), rotate_y(CAM_ROT_Y), rotate_x(CAM_ROT_X)]
    )
    want = compose([inverse(cam_to_world), b, a])  # world->camera outermost
    assert_same_fn(got.func, want.func)


# --- oriented_steps: labels + orientation + order --------------------------


def test_oriented_steps_forward():
    g = build_graph()
    steps = g.path("paddle1", "world").oriented_steps()
    assert [s.label for s in steps] == ["T", "R_z"]
    assert all(s.forward for s in steps)


def test_oriented_steps_backward_inverts_and_relabels_in_reading_order():
    g = build_graph()
    steps = g.path("world", "camera").oriented_steps()
    # reading order: T^{-1} first (matches the demo's camera-inverse animation)
    assert [s.label for s in steps] == ["T^{-1}", "R_y^{-1}", "R_x^{-1}"]
    assert all(not s.forward for s in steps)
    # each oriented fn is the inverse of the forward primitive
    fwd = [translate(CAM_POS), rotate_y(CAM_ROT_Y), rotate_x(CAM_ROT_X)]
    for s, f in zip(steps, fwd):
        for p in SAMPLES:
            assert s.fn(p).isclose(inverse(f)(p))


# --- Phase 1 integration: a path is itself interpolable / iterable ----------


def test_path_function_is_interpolable():
    g = build_graph()
    f = g.path("square", "camera").function()
    # at(0) is identity, at(1) is the full transform
    for p in SAMPLES:
        assert f.at(0.0)(p).isclose(p)
        assert f.at(1.0)(p).isclose(f(p))


def test_path_function_steps_count_matches_total_substeps():
    g = build_graph()
    f = g.path("square", "camera").function()
    # 4 (square->paddle1) + 2 (paddle1->world) + 3 (world->camera) = 9 leaves
    assert len(list(f.steps())) == 9


# --- errors ----------------------------------------------------------------


def test_no_path_raises():
    g = cayleygraph.CayleyGraph(
        [
            cayleygraph.Edge(
                "paddle1", "world", [("T", translate(PADDLE1_POS))]
            ),
            cayleygraph.Edge(
                "island", "island2", [("T", translate(Vector3D(1, 0, 0)))]
            ),  # disconnected
        ]
    )
    with pytest.raises(ValueError):
        g.path("world", "island")


def test_cyclic_graph_rejected():
    with pytest.raises(ValueError):
        cayleygraph.CayleyGraph(
            [
                cayleygraph.Edge(
                    "a", "b", [("T", translate(Vector3D(1, 0, 0)))]
                ),
                cayleygraph.Edge(
                    "b", "a", [("T", translate(Vector3D(0, 1, 0)))]
                ),
            ]
        )


def test_constructed_all_at_once_is_immutable():
    g = build_graph()
    assert not hasattr(g, "add_edge")  # no mutation API
    assert len(g.edges) == 3  # edges is an immutable tuple
    assert isinstance(g.edges, tuple)


def test_enum_node_identifiers():
    from enum import Enum, auto

    class Space(Enum):
        world = auto()
        paddle = auto()

    g = cayleygraph.CayleyGraph(
        [
            cayleygraph.Edge(
                Space.paddle,
                Space.world,
                [("T", translate(Vector3D(3.0, 0.0, 0.0)))],
            ),
        ]
    )
    f = g.path(Space.paddle, Space.world).function()
    assert f(Vector3D(0.0, 0.0, 0.0)).isclose(Vector3D(3.0, 0.0, 0.0))
    assert cayleygraph.node_label(Space.paddle) == "paddle"
    assert cayleygraph.node_label("world") == "world"  # strings still work too


def test_same_space_is_empty_identity_path():
    g = build_graph()
    f = g.path("world", "world").function()
    for p in SAMPLES:
        assert f(p).isclose(p)
