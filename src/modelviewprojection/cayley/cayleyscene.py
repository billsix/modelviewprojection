# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""Turn a :class:`~cayleygraph.CayleyGraph` plus a declarative *scene* into an
animation: a timeline (when each edge-substep plays) and a :class:`Animation`
that,
for any frame time, gives the live transform of each placed object, the
world->camera inverse toward NDC, which geometry/axes are visible, and the two
imgui trees -- all derived from the one graph the author declares.

Three things come out of the scene, no hand-kept parallel structures:

* the object-placement tree (modelspace -> ... -> world): forward edges,
  animated in visit order, with the default geometry-reveal lifecycle;
* the toward-NDC tail: the world->camera **inverse** (affine, CPU -- the
  "camera placed forward, world transforms via inverse" lesson) plus the
  projective
  squash/ortho steps, which stay GPU/shader (``realization="gpu"``, decision
  #4);
* the two imgui trees, which are just two traversal views of the same graph.

No OpenGL here (only a 4x4 realization helper for the GL shell), so it is
unit-testable with no display.
"""

from __future__ import annotations

import dataclasses
import typing

import numpy as np

from modelviewprojection.cayley import cayleygraph
from modelviewprojection.mathutils import (
    InvertibleFunction,
    Vector3,
    compose,
    identity,
    inverse,
    rotate_x,
    rotate_y,
    translate,
)

#: node-id type for a scene's coordinate spaces (an Enum member, typically)
N = typing.TypeVar("N")

DEFAULT_STEP_DURATION = 5.0


@dataclasses.dataclass
class CameraControls:
    """Live-editable virtual-camera placement.  Holds the three edge Steps of a
    ``camera->world`` edge (``[T, R_y, R_x]``) plus the current position / yaw /
    pitch; :meth:`apply` rewrites those Steps' ``fn`` IN PLACE, so both the
    camera object and the world->camera inverse update together while the Step
    identities (and thus the timeline slots, keyed by ``id(step)``) stay valid.

    This is the general "editable edge" pattern: mutate a Step's ``fn``, not the
    graph structure.  Pure logic (no GL) -- a demo's imgui panel drives it.
    """

    translate_step: cayleygraph.Step
    rot_y_step: cayleygraph.Step
    rot_x_step: cayleygraph.Step
    px: float
    py: float
    pz: float
    rot_y: float
    rot_x: float

    def apply(self) -> None:
        self.translate_step.fn = translate(Vector3(self.px, self.py, self.pz))
        self.rot_y_step.fn = rotate_y(self.rot_y)
        self.rot_x_step.fn = rotate_x(self.rot_x)


def interp(time: float, start: float, dur: float) -> float:
    """The demos' parameter-scaling factor: 0 before ``start``, ramping to 1.0
    over ``dur``, clamped at 1.0 after.  ``dur <= 0`` is a step at ``start``.

    A ramp starting at t=1 over 2 seconds: flat 0 until it starts, linear
    across the middle, flat 1 once done.

    >>> interp(0.0, start=1.0, dur=2.0)   # before it starts
    0.0
    >>> interp(2.0, start=1.0, dur=2.0)   # halfway through the ramp
    0.5
    >>> interp(5.0, start=1.0, dur=2.0)   # long after -> clamped at 1
    1.0

    A non-positive duration degenerates to a step at ``start`` -- 0 before,
    1 from ``start`` on:

    >>> interp(0.9, start=1.0, dur=0.0)
    0.0
    >>> interp(1.0, start=1.0, dur=0.0)
    1.0
    """
    if dur <= 0.0:
        return 1.0 if time >= start else 0.0
    if time <= start:
        return 0.0
    return min(1.0, (time - start) / dur)


# --- scene declaration -----------------------------------------------------


@dataclasses.dataclass
class CoordinateFrame(typing.Generic[N]):
    """One node placed in the scene: which space, its parent, the geometry to
    draw there (an opaque handle the demo's draw code understands; ``None`` for
    a pure coordinate frame), and an optional pause before its edge animates."""

    space: N
    parent: N
    geometry: typing.Any = None
    dwell_before: float = 0.0
    #: keep a grayed-out axis at this node's frame after it is built (for a pure
    #: coordinate frame that should stay marked, e.g. the shared center of a fan
    #: of squares).  The bright axis still shows while it is being built.
    grayed_axis_after_built: bool = False


@dataclasses.dataclass
class InverseOperations(typing.Generic[N]):
    """A toward-NDC CPU segment: walk the path ``from_space -> to_space`` (e.g.
    world -> camera), animating each substep -- against-arrow edges invert
    automatically.  This is the world transforming into camera space."""

    from_space: N
    to_space: N
    group_title: str = ""
    dwell_before: float = 0.0


@dataclasses.dataclass
class NonInvertibleTransformation:
    """A toward-NDC GPU segment (the projective squash / ortho).  Its steps are
    NOT ``InvertibleFunction``s (decision #4) -- each is a label with a time
    slot the shell maps to the shader's ``time`` uniform."""

    group_title: str
    step_labels: typing.List[str]
    dwell_before: float = 0.0


@dataclasses.dataclass
class Scene(typing.Generic[N]):
    """A graph, an ordered list of coordinate_frames (the object-placement
    tree), and
    an ordered list of toward-NDC operations (CPU inverse + GPU)."""

    graph: cayleygraph.CayleyGraph[N]
    root: N
    coordinate_frames: typing.List[CoordinateFrame[N]]
    to_ndc: typing.List[InverseOperations[N] | NonInvertibleTransformation] = (
        dataclasses.field(default_factory=list)
    )
    step_duration: float = DEFAULT_STEP_DURATION
    end_dwell: float = 0.0


# --- derived timeline pieces -----------------------------------------------


@dataclasses.dataclass
class TimedStep:
    """A placement edge-substep with its assigned slot on the timeline."""

    label: str
    step: cayleygraph.Step
    start: float
    dur: float
    space: typing.Any


@dataclasses.dataclass
class InverseOpsTrack:
    """A CPU inverse-operations edge with per-substep slots (edge order)."""

    edge: cayleygraph.Edge
    forward: bool
    timed: typing.List[typing.Tuple[cayleygraph.Step, float, float]]
    group_title: str

    def live(self, time: float) -> InvertibleFunction:
        fwd = compose(
            [s.fn.at(interp(time, start, dur)) for s, start, dur in self.timed]
        )
        return fwd if self.forward else inverse(fwd)


@dataclasses.dataclass
class GpuStep:
    group_title: str
    label: str
    start: float
    dur: float


# --- imgui-tree data (rendered by the GL shell) ----------------------------


@dataclasses.dataclass
class GuiButton:
    label: str
    start: float
    active: bool


@dataclasses.dataclass
class GuiGroup:
    title: str
    buttons: typing.List[GuiButton]
    children: typing.List["GuiGroup"] = dataclasses.field(default_factory=list)


class Timeline(typing.Generic[N]):
    """Assigns every substep a ``(start, dur)`` slot by walking the
    coordinate_frames
    then the to_ndc operations in order (accumulating ``dwell_before`` + the
    step
    durations), and answers per-node lifecycle questions."""

    def __init__(self, scene: Scene[N]) -> None:
        self.scene = scene
        self.steps: typing.List[TimedStep] = []  # placement substeps
        self.inverse_tracks: typing.List[
            InverseOpsTrack
        ] = []  # CPU inverse operations
        self.gpu_steps: typing.List[GpuStep] = []
        self._slot: typing.Dict[int, typing.Tuple[float, float]] = {}
        self._window: typing.Dict[N, typing.Tuple[float, float]] = {}

        dur = scene.step_duration
        t = 0.0

        # 1) object-placement tree (forward edges, visit order)
        for placement in scene.coordinate_frames:
            t += placement.dwell_before
            ((edge_obj, _fwd),) = scene.graph.path(
                placement.space, placement.parent
            ).route
            first = t
            for s in edge_obj.steps:
                self.steps.append(
                    TimedStep(s.label, s, t, dur, placement.space)
                )
                self._slot[id(s)] = (t, dur)
                t += dur
            self._window[placement.space] = (first, t)

        # 2) toward-NDC operations (CPU inverse, then GPU squash/ortho)
        for op in scene.to_ndc:
            t += op.dwell_before
            if isinstance(op, InverseOperations):
                title = op.group_title or (
                    f"{cayleygraph.node_label(op.from_space)}->"
                    f"{cayleygraph.node_label(op.to_space)}"
                )
                for edge, forward in scene.graph.path(
                    op.from_space, op.to_space
                ).route:
                    timed = []
                    for s in edge.steps:
                        timed.append((s, t, dur))
                        t += dur
                    self.inverse_tracks.append(
                        InverseOpsTrack(edge, forward, timed, title)
                    )
            else:  # NonInvertibleTransformation
                for label in op.step_labels:
                    self.gpu_steps.append(
                        GpuStep(op.group_title, label, t, dur)
                    )
                    t += dur

        t += scene.end_dwell
        self.duration = t

    def slot(self, step: cayleygraph.Step) -> typing.Tuple[float, float]:
        """``(start, dur)`` of a placement substep; ``(0, 0)`` (fully applied)
        for one not on the timeline (an ancestor seen on a longer path)."""
        return self._slot.get(id(step), (0.0, 0.0))

    # --- node lifecycle (the default geometry-reveal policy) ----------------

    def built_time(self, space: N) -> float:
        return self._window.get(space, (0.0, 0.0))[1]

    def arrival_time(self, space: N) -> float:
        return self._window.get(space, (0.0, 0.0))[0]

    def axis_visible(self, space: N, time: float) -> bool:
        start, end = self._window.get(space, (0.0, 0.0))
        return start <= time < end

    def geometry_visible(self, space: N, time: float) -> bool:
        return time >= self.built_time(space)


class Animation(typing.Generic[N]):
    """Evaluates a :class:`Scene`/:class:`Timeline` at a given frame time."""

    def __init__(
        self,
        scene: Scene[N],
        timeline: typing.Optional[Timeline[N]] = None,
    ) -> None:
        self.scene = scene
        self.timeline = timeline or Timeline(scene)

    # --- object placement ---------------------------------------------------

    def transform(self, space: N, time: float) -> InvertibleFunction:
        """Live ``space``-modelspace -> root transform at ``time``.

        Composes edge-by-edge; each substep at its own local ``t``, so a nested
        child rides on its already-placed ancestors (theirs read ``at(1.0)``).
        """
        route = self.scene.graph.path(space, self.scene.root).route
        edge_fns: typing.List[InvertibleFunction] = []
        for edge, forward in route:
            live = compose(
                [
                    s.fn.at(interp(time, *self.timeline.slot(s)))
                    for s in edge.steps
                ]
            )
            edge_fns.append(live if forward else inverse(live))
        if not edge_fns:
            return identity()
        return compose(list(reversed(edge_fns)))

    def axis_visible(self, space: N, time: float) -> bool:
        return self.timeline.axis_visible(space, time)

    def geometry_visible(self, space: N, time: float) -> bool:
        return self.timeline.geometry_visible(space, time)

    # --- toward-NDC tail ----------------------------------------------------

    def inverse_transform(self, time: float) -> InvertibleFunction:
        """The accumulated world->camera inverse applied to world geometry at
        ``time`` (the inverse of the camera placement).  Identity until it
        begins."""
        tracks = self.timeline.inverse_tracks
        if not tracks:
            return identity()
        # first-declared track innermost -> reverse for compose (like edges)
        return compose([tr.live(time) for tr in reversed(tracks)])

    def gpu_progress(
        self, time: float
    ) -> typing.List[typing.Tuple[str, float]]:
        """``(label, progress in [0,1])`` for each GPU projection substep -- the
        shell feeds these (or their start times) to the shader ``time``
        uniform."""
        return [
            (g.label, interp(time, g.start, g.dur))
            for g in self.timeline.gpu_steps
        ]

    # --- imgui-tree data ----------------------------------------------------

    def active_label(self, time: float) -> typing.Optional[str]:
        """Label of the placement substep currently animating (imgui
        highlight)."""
        for ts in self.timeline.steps:
            if ts.start <= time < ts.start + ts.dur:
                return ts.label
        return None

    def _is_active(self, start: float, time: float) -> bool:
        return start <= time < start + self.scene.step_duration

    def frame_tree(self, time: float) -> typing.List[GuiGroup]:
        """Tree 1 ("From World Space, Against Arrows, Read Bottom Up"): a group
        per placement (``space->parent``) with its substeps as buttons in edge
        order, nested by parent.  Returns the top-level groups."""
        groups: typing.Dict[N, GuiGroup] = {}
        tops: typing.List[GuiGroup] = []
        for placement in self.scene.coordinate_frames:
            buttons = [
                GuiButton(ts.label, ts.start, self._is_active(ts.start, time))
                for ts in self.timeline.steps
                if ts.space == placement.space
            ]
            g = GuiGroup(
                f"{cayleygraph.node_label(placement.space)}->"
                f"{cayleygraph.node_label(placement.parent)}",
                buttons,
            )
            groups[placement.space] = g
            parent = groups.get(placement.parent)
            (parent.children if parent else tops).append(g)
        return tops

    def ndc_tree(self, time: float) -> typing.List[GuiGroup]:
        """Tree 2 ("Towards NDC, With Arrows, Top Down Reading"): one group per
        to_ndc segment, buttons in application / outermost-first order (reverse
        of
        time), inverse-marked for the CPU inverse segments."""
        out: typing.List[GuiGroup] = []
        for op in self.scene.to_ndc:
            if isinstance(op, InverseOperations):
                track = self._track_for(op)
                if track is None:
                    continue
                buttons = [
                    GuiButton(
                        s.label + "^{-1}",
                        start,
                        self._is_active(start, time),
                    )
                    for s, start, _dur in reversed(track.timed)
                ]
                out.append(GuiGroup(track.group_title, buttons))
            else:  # NonInvertibleTransformation
                steps = [
                    g
                    for g in self.timeline.gpu_steps
                    if g.group_title == op.group_title
                ]
                buttons = [
                    GuiButton(g.label, g.start, self._is_active(g.start, time))
                    for g in reversed(steps)
                ]
                out.append(GuiGroup(op.group_title, buttons))
        return out

    def _track_for(
        self, op: InverseOperations
    ) -> typing.Optional[InverseOpsTrack]:
        title = op.group_title or (
            f"{cayleygraph.node_label(op.from_space)}->"
            f"{cayleygraph.node_label(op.to_space)}"
        )
        for tr in self.timeline.inverse_tracks:
            if tr.group_title == title:
                return tr
        return None


def to_matrix(f: InvertibleFunction) -> np.ndarray:
    """Realize an **affine** ``InvertibleFunction`` on ``Vector3`` as a 4x4
    (row-major, ``M @ [x, y, z, 1]``) for upload as a GL model matrix.

    Columns come from ``f(e_i) - f(0)`` and the translation from ``f(0)`` -- so
    ``to_matrix(f) @ [p, 1] == f(p)`` for any affine ``f``.  Not valid for the
    projective squash (which stays a shader; see decision #4).

    A translation becomes a 4x4 whose last column is the offset:

    >>> import numpy as np
    >>> from modelviewprojection.mathutils import translate, Vector3
    >>> m = to_matrix(translate(Vector3(3.0, 4.0, 5.0)))
    >>> m[:, 3].tolist()
    [3.0, 4.0, 5.0, 1.0]

    The defining property -- applying the matrix to a point matches applying
    the function to it:

    >>> (m @ np.array([1.0, 2.0, 3.0, 1.0])).tolist()
    [4.0, 6.0, 8.0, 1.0]
    """
    o = f(Vector3(0.0, 0.0, 0.0))
    cx = f(Vector3(1.0, 0.0, 0.0)) - o
    cy = f(Vector3(0.0, 1.0, 0.0)) - o
    cz = f(Vector3(0.0, 0.0, 1.0)) - o
    # gacalc coefficients can be sympy expressions (magnitude() uses sympy.sqrt,
    # so rotor-based rotations yield sympy-typed components). Force float64
    # here: otherwise np.array infers dtype=object and downstream np.linalg.inv
    # / GL upload fail with a cast error. This boundary cast stays even once
    # gacalc returns plain numbers for numeric input -- numpy/GL want float64
    # regardless.
    return np.array(
        [
            [cx.coeff_e_1, cy.coeff_e_1, cz.coeff_e_1, o.coeff_e_1],
            [cx.coeff_e_2, cy.coeff_e_2, cz.coeff_e_2, o.coeff_e_2],
            [cx.coeff_e_3, cy.coeff_e_3, cz.coeff_e_3, o.coeff_e_3],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
