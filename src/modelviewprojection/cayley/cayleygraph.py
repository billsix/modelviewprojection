# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""A Cayley graph as an IMMUTABLE, directed acyclic data structure, for the
``mvpvisualization`` demos.

Nodes are coordinate **spaces** (typically members of a per-demo ``Enum``);
directed **edges** are ordered sequences of *interpolable*
``InvertibleFunction``s -- the very ``compose`` / ``inverse`` machinery the book
teaches.  Trace a :meth:`CayleyGraph.path` between any two spaces and it
composes
the edge functions, auto-inverting any edge walked *against* its arrow --
exactly
the chapter-02 rule, executed instead of drawn.

Design (per Bill):

* the whole graph is passed at construction (``CayleyGraph([Edge(...), ...])``);
  there is no ``add_edge`` and the structure is immutable -- these graphs are
  not
  dynamically adjusted;
* the edges are directed and **acyclic** (validated at construction);
* node identifiers are opaque hashables -- use an ``Enum`` per demo (strings
  also
  work).  :func:`node_label` gives a readable name for either.

A ``Step``'s ``fn`` stays mutable on purpose: that is a transform *parameter*
(e.g. the editable virtual camera rewrites it in place), not the graph
structure.

No OpenGL here -- pure data + math, so it is unit-testable with no display.
"""

from __future__ import annotations

import dataclasses
import enum
import typing
from collections import deque

from modelviewprojection.mathutils import (
    InvertibleFunction,
    compose,
    identity,
    inverse,
)

N = typing.TypeVar("N")  # node-id type (an Enum member, typically)


def node_label(node: typing.Any) -> str:
    """A readable name for a node id (the ``Enum`` member name, or ``str``).

    An ``Enum`` node reads as its member name, not its ``repr``:

    >>> import enum
    >>> class Space(enum.Enum):
    ...     world = 1
    ...     camera = 2
    >>> node_label(Space.world)
    'world'

    Anything else falls back to ``str``, so plain string node ids work too:

    >>> node_label("ndc")
    'ndc'
    """
    return node.name if isinstance(node, enum.Enum) else str(node)


class _DfsColor(enum.IntEnum):
    """Node state during the acyclicity DFS (the classic 3-colouring).

    Was a bare ``WHITE, GRAY, BLACK = 0, 1, 2`` tuple of function-locals; naming
    them as an enum keeps the algorithm's vocabulary while making the values
    self-describing in a traceback.
    """

    WHITE = 0  #: not yet visited
    GRAY = 1  #: on the current DFS path -- reaching one again means a cycle
    BLACK = 2  #: fully explored, cannot be part of a cycle


@dataclasses.dataclass
class Step:
    """One labeled, interpolable transform along an edge.

    ``label`` is the short LaTeX-ish name shown on the imgui button (``"T"``,
    ``"R_z"``).  ``fn`` is an interpolable :class:`InvertibleFunction` -- use
    ``fn.at(t)`` to get it partway from identity (``t=0``) to full (``t=1``).
    NOT frozen: ``fn`` is an editable transform *parameter* (the structure of
    the
    graph is what's immutable, not the numbers in a transform).
    """

    label: str
    fn: InvertibleFunction


@dataclasses.dataclass(frozen=True)
class Edge(typing.Generic[N]):
    """An immutable directed edge ``src -> dst``: an ordered tuple of
    :class:`Step`.

    The edge's function (src coordinates -> dst coordinates) is
    ``compose([s.fn for s in steps])`` -- the *first* step is outermost,
    matching
    how the demos stack transforms (``translate`` then ``rotate``).
    ``realization`` flags CPU matrix stack (``"cpu"``) vs shader ``time``
    uniform
    (``"gpu"``, for the projective squash that is deliberately not an
    ``InvertibleFunction``).

    ``steps`` accepts :class:`Step` objects or ``(label, fn)`` pairs; both are
    coerced to a tuple of :class:`Step`.
    """

    src: N
    dst: N
    steps: typing.Tuple[Step, ...]
    realization: str = "cpu"

    def __init__(
        self,
        src: N,
        dst: N,
        steps: typing.Sequence[Step | typing.Tuple[str, InvertibleFunction]],
        realization: str = "cpu",
    ) -> None:
        # ``steps`` accepts Step objects or (label, fn) pairs; both coerce to a
        # tuple of Step.  A custom __init__ (rather than __post_init__) lets the
        # stored ``steps`` field stay typed tuple[Step, ...] for readers while
        # the constructor accepts the broader input.  (frozen ->
        # object.__setattr__.)
        object.__setattr__(self, "src", src)
        object.__setattr__(self, "dst", dst)
        object.__setattr__(
            self,
            "steps",
            tuple(s if isinstance(s, Step) else Step(*s) for s in steps),
        )
        object.__setattr__(self, "realization", realization)

    def function(self) -> InvertibleFunction:
        """The edge as a single src->dst :class:`InvertibleFunction`."""
        return compose([s.fn for s in self.steps]) if self.steps else identity()


@dataclasses.dataclass
class OrientedStep:
    """A :class:`Step` as encountered while walking a path.

    Walked with the arrow (``forward=True``) it is the step verbatim; walked
    against the arrow it is inverted and its label marked ``^{-1}``.  ``fn`` is
    still interpolable (``fn.at(t)``), so an against-arrow edge animates
    smoothly
    -- :func:`inverse` commutes with ``at``.
    """

    label: str
    fn: InvertibleFunction
    forward: bool
    edge: Edge


@dataclasses.dataclass
class Path:
    """A traced route ``src -> dst`` and the transform it represents."""

    src: typing.Any
    dst: typing.Any
    #: ``[(Edge, forward_bool), ...]`` from src to dst (src-incident edge
    #: first).
    route: typing.List[typing.Tuple[Edge, bool]]

    def oriented_steps(self) -> typing.List[OrientedStep]:
        """Substeps in reading / animation order: route order, and within each
        edge the steps as written -- each inverted and relabeled when the edge
        is
        walked against its arrow.

        For a ``camera->world`` edge ``[T, R_y, R_x]`` walked backward
        (``world->camera``) this yields ``[T^{-1}, R_y^{-1}, R_x^{-1}]``.
        """
        out: typing.List[OrientedStep] = []
        for edge, forward in self.route:
            for s in edge.steps:
                if forward:
                    out.append(OrientedStep(s.label, s.fn, True, edge))
                else:
                    out.append(
                        OrientedStep(
                            s.label + "^{-1}", inverse(s.fn), False, edge
                        )
                    )
        return out

    def function(self) -> InvertibleFunction:
        """The composed ``src``-coords -> ``dst``-coords transform, inverting
        any
        against-arrow edge automatically.  The src-incident edge is applied
        first
        (innermost), the dst-incident edge last (outermost)."""
        edge_fns: typing.List[InvertibleFunction] = []
        for edge, forward in self.route:
            efn = edge.function()
            edge_fns.append(efn if forward else inverse(efn))
        if not edge_fns:
            return identity()
        return compose(list(reversed(edge_fns)))


class CayleyGraph(typing.Generic[N]):
    """An immutable directed acyclic graph of spaces, built from all its edges
    at once: ``CayleyGraph([Edge(a, b, ...), Edge(c, b, ...), ...])``.

    Build one from a list of edges; every space mentioned becomes a node:

    >>> import enum
    >>> from modelviewprojection.mathutils import identity
    >>> class Space(enum.Enum):
    ...     world = 1
    ...     camera = 2
    ...     ndc = 3
    >>> graph = CayleyGraph([
    ...     Edge(Space.world, Space.camera, [("V", identity)]),
    ...     Edge(Space.camera, Space.ndc, [("P", identity)]),
    ... ])
    >>> len(graph.spaces)
    3

    The edges are directed and must be **acyclic** -- that is validated at
    construction, so a cycle is rejected up front rather than looping forever
    when a path is later traced:

    >>> CayleyGraph([
    ...     Edge(Space.world, Space.camera, [("V", identity)]),
    ...     Edge(Space.camera, Space.world, [("V_inv", identity)]),
    ... ])  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: Cayley graph must be acyclic; cycle through ...
    """

    def __init__(self, edges: typing.Iterable[Edge]) -> None:
        self._edges: typing.Tuple[Edge, ...] = tuple(edges)
        # undirected adjacency: space -> ((neighbor, edge, walked_forward), ...)
        adj: typing.Dict[N, list] = {}
        for e in self._edges:
            adj.setdefault(e.src, []).append((e.dst, e, True))
            adj.setdefault(e.dst, []).append((e.src, e, False))
        self._adj: typing.Dict[N, tuple] = {k: tuple(v) for k, v in adj.items()}
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        """Validate the DIRECTED edges have no cycle (DFS 3-coloring)."""
        directed: typing.Dict[N, list] = {}
        for e in self._edges:
            directed.setdefault(e.src, []).append(e.dst)
        color: typing.Dict[N, _DfsColor] = {}

        def visit(n: N) -> None:
            color[n] = _DfsColor.GRAY
            for m in directed.get(n, []):
                c = color.get(m, _DfsColor.WHITE)
                if c == _DfsColor.GRAY:
                    raise ValueError(
                        f"Cayley graph must be acyclic; cycle through "
                        f"{node_label(n)} -> {node_label(m)}"
                    )
                if c == _DfsColor.WHITE:
                    visit(m)
            color[n] = _DfsColor.BLACK

        for n in self._adj:
            if color.get(n, _DfsColor.WHITE) == _DfsColor.WHITE:
                visit(n)

    @property
    def spaces(self) -> typing.Tuple[N, ...]:
        return tuple(self._adj.keys())

    @property
    def edges(self) -> typing.Tuple[Edge, ...]:
        return self._edges

    def _route(self, a: N, b: N) -> typing.List[typing.Tuple[Edge, bool]]:
        """Shortest route a->b over the undirected graph (BFS).  Acyclicity is
        already guaranteed, so this always terminates."""

        # BFS bookkeeping: node -> (parent, edge, walked_forward), None at the
        # root.  A PEP 695 `type` statement, so it stays local to this function
        # -- a plain `Parents = ...` assignment would trip N806.
        type Parents = typing.Dict[
            N, typing.Optional[typing.Tuple[N, Edge, bool]]
        ]

        def breadth_first_parents() -> Parents:
            """Reachable node -> (parent, edge, forward), stopping at b.

            Raises if b is unreachable: the search is what discovers that, so
            it is what reports it.
            """
            prev: Parents = {a: None}
            q: typing.Deque[N] = deque([a])
            while q:
                n = q.popleft()
                if n == b:
                    break
                for neighbor, edge, forward in self._adj.get(n, ()):  # type: ignore[misc]
                    if neighbor not in prev:
                        prev[neighbor] = (n, edge, forward)
                        q.append(neighbor)
            if b not in prev:
                raise ValueError(
                    f"no path from {node_label(a)!r} to {node_label(b)!r}"
                )
            return prev

        def walk_back(
            prev: Parents,
        ) -> typing.List[typing.Tuple[Edge, bool]]:
            """Follow parents from b back to a, then reverse into a->b order."""
            route: typing.List[typing.Tuple[Edge, bool]] = []
            cur = b
            while prev[cur] is not None:
                step = prev[cur]
                assert step is not None
                parent, edge, forward = step
                route.append((edge, forward))
                cur = parent
            route.reverse()
            return route

        match (a, b):
            case (start, end) if start == end:
                return []
            case (start, end) if start not in self._adj or end not in self._adj:
                # Checked for BOTH endpoints on purpose. The search below would
                # also fail for an unknown node, but it would report "no path",
                # implying the space exists and is unreachable -- when the real
                # mistake is usually a typo'd Enum member.
                unknown = start if start not in self._adj else end
                raise ValueError(f"unknown space {node_label(unknown)!r}")
            case _:
                return walk_back(breadth_first_parents())

    def path(self, a: N, b: N) -> Path:
        """Trace a :class:`Path` from space ``a`` to space ``b``."""
        return Path(a, b, self._route(a, b))
