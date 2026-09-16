"""Dump the perspective visualization's timeline (placement steps, world->camera
inverse, GPU squash steps, duration) so the graph-panel button start times can
be checked against project_perspective.glsl's HARDCODED squash times.

The demo module sys.exit()s on import (it is a program), so the scene is
reconstructed here verbatim from modelviewperspectiveprojection.py.

Run:
    make shell-exec CMD='python tasks/adhoc/framebuffer-in-perspective/dump_timeline.py'
"""

import math
from enum import Enum, auto

from gacalc.g3 import Vector
from gacalc.transforms import translate

from modelviewprojection.cayley import cayleygraph, cayleyscene
from modelviewprojection.mathutils import rotate_x, rotate_y, rotate_z


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
        ("T", translate(Vector(-1.5, 0.0, 8.5))),
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
            # mirrors the demo (dwell 10 -> squash at 87); the shader hardcodes
            # 90, which is the original 3s drift this diagnostic surfaced.
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

tl = cayleyscene.Timeline(scene)
print("=== placement steps (label: start..end) ===")
for ts in tl.steps:
    print(f"  {ts.label:6} {ts.start:6.1f}..{ts.start + ts.dur:.1f}")
print("=== world->camera inverse ===")
for tr in tl.inverse_tracks:
    for s, start, dur in tr.timed:
        print(f"  {s.label:6} {start:6.1f}..{start + dur:.1f}")
print("=== GPU squash steps ===")
for g in tl.gpu_steps:
    print(f"  {g.label:12} start={g.start:6.1f}  dur={g.dur}")
print("=== per-space reveal (demo-local; +17 = global with PROLOGUE_DUR) ===")
for cf in scene.coordinate_frames:
    sp = cf.space
    a = tl.arrival_time(sp)
    b = tl.built_time(sp)
    print(f"  {sp.name:8} axis[{a:.0f}..{b:.0f})  mesh appears >= {b:.0f}")
anim = cayleyscene.Animation(scene)
print("=== visibility + inverse_transform at sample demo-local times ===")
for dt in (12.0, 20.0, 42.0, 50.0, 62.0, 70.0, 90.0):
    p1: bool = anim.geometry_visible(Space.paddle1, dt)
    p2: bool = anim.geometry_visible(Space.paddle2, dt)
    invf = anim.inverse_transform(dt)
    moved = invf(Vector(9.0, 0.0, 0.0)) - Vector(9.0, 0.0, 0.0)
    inv_active: bool = (
        abs(float(moved.coeff_e_1)) + abs(float(moved.coeff_e_3)) > 1e-6
    )
    print(
        f"  demo_t={dt:5.0f}  paddle1_mesh={p1}  paddle2_mesh={p2}  "
        f"inverse_active={inv_active}"
    )
print(f"=== duration = {tl.duration} ===")
print(
    "shader project_perspective.glsl hardcodes: Squash X 90, Squash Y 95, "
    "T-Center(translate) 100, Scale(to NDC) 105"
)
