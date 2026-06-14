# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""Cross product ``a x b``, derived the way the book's proof derives it -- rotate
``a`` and ``b`` to align, read off the perpendicular, rotate back -- but with
gacalc **rotors** instead of rotation matrices.

Ported from ``multivariate-math/proofs/crossproduct.tex`` (the rotation-matrix
proof) into rotor form.  The geometry/pedagogy is unchanged; only the
representation moved to rotors.  The worked symbolic derivation lives in the
companion notebook ``notebooksrc/crossproduct.py`` (jupytext).

  * ``f_a^{zx}`` then ``f_{a'}^x`` (rotate ``a`` onto the x axis) collapse into a
    single rotor ``R1 = rotor_from_vectors(a -> e_1)``.
  * ``f_{b''}^{xy}`` (rotate ``b''`` into the x-y plane) is ``R2``, a rotor that
    carries the part of ``b''`` perpendicular to ``a`` onto ``e_2``.
  * in the aligned frame ``a'' = |a| e_1`` and ``b'''`` lies in the x-y plane, so
    ``a'' x b''' = |a| c e_3`` with ``c = |b| sin(theta)``.
  * rotate that back to the original frame with the reverse rotors.

``cross_product`` is the closed rotor form (used by the symbolic proof/test).
``build_alignment_graph`` expresses the same derivation as a **Cayley graph of
rotor edges** (one rotation per coordinate plane) -- interpolable, so the
``main()`` demo animates it step by step by walking the graph.  No OpenGL at
module level -- pure gacalc, unit-testable headless; the demo's GL imports are
local to ``main()``.
"""

from __future__ import annotations

import math

from modelviewprojection.cayley import cayleygraph, cayleyscene
from modelviewprojection.mathutils import (
    Vector3,
    compose,
    inverse,
    rotate_x,
    rotate_y,
    rotor_rotation,
    scale_non_uniform,
    translate,
)


def cross_product(a: Vector3, b: Vector3) -> Vector3:
    """``a x b`` via the rotor port of the book's proof.

    Pure gacalc: coefficients may be Python numbers *or* sympy expressions, so
    this is the same routine the symbolic proof (and the test) exercises.  It
    assumes ``a`` is non-zero and ``b`` is not parallel to ``a`` (otherwise the
    alignment rotors are undefined -- the perpendicular has no direction); the
    interactive demo guards those degenerate inputs before calling.
    """
    e_1, e_2, e_3 = Vector3.e_1, Vector3.e_2, Vector3.e_3
    mag_a = a.magnitude()

    # R1: rotate a onto the +x axis (proof's f_{a'}^x . f_a^{zx}, as one rotor).
    r1 = Vector3.rotor_from_vectors(from_vector=a, to_vector=e_1).normalize()
    b_aligned = r1.sandwich(b)  # b''

    # the part of b'' perpendicular to a (a is now on x), i.e. in the y-z plane.
    # gacalc's reject(away_from=...) is an operator (a function); apply it.
    b_perp = Vector3.reject(away_from=e_1)(b_aligned)
    c = b_perp.magnitude()  # |b| sin(theta)

    # R2: rotate that perpendicular part onto +y (a rotation in the y-z plane,
    # so a-on-x is left fixed) -- the proof's f_{b''}^{xy}.
    r2 = Vector3.rotor_from_vectors(
        from_vector=b_perp, to_vector=e_2
    ).normalize()

    # in the fully-aligned frame a'' = |a| e_1 and b''' lies in the x-y plane,
    # so a'' x b''' = |a| * c * e_3.
    c_aligned = (mag_a * c) * e_3

    # rotate the result back to the original frame: undo R2, then R1.
    return r1.reverse().sandwich(r2.reverse().sandwich(c_aligned))


def _rotor_edge(from_vector, to_vector, label="R"):
    """An interpolable ROTOR carrying ``from_vector``'s direction onto
    ``to_vector``'s -- a ``rotor_from_vectors``-style ``InvertibleFunction`` whose
    ``.at(t)`` is a smooth partial rotation.  The rotor replacement for the axis
    ``rotate_*`` edges, suitable as a Cayley-graph edge.

    **No trigonometry.**  The rotor itself is ``rotor_from_vectors`` (a geometric
    product ``R = |u||v| + v*u`` -- no angle).  The partial rotation just linearly
    blends (nlerp) the start and target *directions* and re-builds the rotor;
    ``rotor_rotation`` needs only the target direction, never ``sin``/``acos``.
    """
    fu = from_vector.normalize()
    fv = to_vector.normalize()

    def _partial(t):
        target = (
            1.0 - t
        ) * fu + t * fv  # nlerp of directions -- no sin/cos/atan
        return rotor_rotation(from_vector, target)

    return rotor_rotation(
        from_vector, to_vector, latex_repr=label, interpolate=_partial
    )


def build_alignment_graph(a: Vector3, b: Vector3):
    """The cross-product alignment as a Cayley graph of ROTOR edges, built the way
    the proof / animation does it -- **project onto a coordinate plane, then make a
    rotor from that projection to an axis** (each edge a rotation confined to a
    plane).  No trigonometry: only ``reject`` (projection) + ``rotor_from_vectors``.

        world --R_z--> a_in_xz --R_y--> a_on_x --R_x--> b_in_xy

    * ``R_z`` carries a's projection on the e1-e2 plane onto +x (rotation about z),
      leaving a in the x-z plane;
    * ``R_y`` carries that onto the +x axis (rotation about y);
    * ``R_x`` carries the part of b perpendicular to a (its projection on the e2-e3
      plane, in the aligned frame) onto +y, putting b in the x-y plane.

    The edges depend on the vectors' projections, so rebuild the graph whenever
    ``a`` / ``b`` change (e.g. once when the animation starts).  Returns
    ``(graph, cross_aligned)`` with ``cross_aligned = |a| |b_perp| e_3`` (the
    perpendicular in the fully aligned ``b_in_xy`` frame); tracing
    ``b_in_xy -> world`` carries it back to ``a x b``.
    """
    e_1, e_2, e_3 = Vector3.e_1, Vector3.e_2, Vector3.e_3
    onto_e1_e2 = Vector3.reject(away_from=e_3)  # project onto the e1-e2 plane
    onto_e2_e3 = Vector3.reject(away_from=e_1)  # project onto the e2-e3 plane

    # about z: a's e1-e2 shadow -> +x  (a then lies in the x-z plane)
    r_z = _rotor_edge(onto_e1_e2(a), e_1, label="R_z")
    # about y: that x-z vector -> +x axis
    r_y = _rotor_edge(r_z(a), e_1, label="R_y")
    # about x: b's part perpendicular to a -> +y  (b into the x-y plane)
    b_perp = onto_e2_e3(r_y(r_z(b)))
    r_x = _rotor_edge(b_perp, e_2, label="R_x")

    graph = cayleygraph.CayleyGraph(
        [
            cayleygraph.Edge(src="world", dst="a_in_xz", steps=[("R_z", r_z)]),
            cayleygraph.Edge(src="a_in_xz", dst="a_on_x", steps=[("R_y", r_y)]),
            cayleygraph.Edge(src="a_on_x", dst="b_in_xy", steps=[("R_x", r_x)]),
        ]
    )
    cross_aligned = (float(a.magnitude()) * float(b_perp.magnitude())) * e_3
    return graph, cross_aligned


def cross_product_via_graph(a: Vector3, b: Vector3) -> Vector3:
    """``a x b`` by tracing the alignment graph back to world -- the Cayley-graph
    form of the derivation (companion to the closed-form ``cross_product``)."""
    graph, cross_aligned = build_alignment_graph(a, b)
    return graph.path("b_in_xy", "world").function()(cross_aligned)


def cross_product_stepwise(a: Vector3, b: Vector3) -> Vector3:
    """``a x b`` computed the way the animation/proof does it: as **three rotations,
    each confined to a coordinate plane and built from a projection**, rather than
    the single ``a -> e_1`` rotor of :func:`cross_product`.  Same result -- this is
    the explicit, step-by-step companion (closed-form vs step-by-step), written out
    inline so the function body reads as the derivation.

    No trigonometry: each rotation is ``reject`` (project onto a coordinate plane)
    then ``rotor_from_vectors`` onto an axis -- the same three rotors the demo
    animation walks (the edges of :func:`build_alignment_graph`).  Pure gacalc, so
    it runs symbolically too.  Like :func:`cross_product` it assumes ``a`` non-zero
    and ``b`` not parallel to ``a``.
    """
    e_1, e_2, e_3 = Vector3.e_1, Vector3.e_2, Vector3.e_3

    # R_z: a's shadow on the e1-e2 plane -> +x  (a then lies in the x-z plane).
    a_xy = Vector3.reject(away_from=e_3)(a)
    r_z = Vector3.rotor_from_vectors(
        from_vector=a_xy, to_vector=e_1
    ).normalize()
    a1 = r_z.sandwich(a)

    # R_y: that x-z vector -> the +x axis  (a is now |a| e_1).
    r_y = Vector3.rotor_from_vectors(from_vector=a1, to_vector=e_1).normalize()

    # carry b through both rotations, take its part perpendicular to a (its
    # projection on the e2-e3 plane), and R_x: that perpendicular -> +y.
    b2 = r_y.sandwich(r_z.sandwich(b))
    b_perp = Vector3.reject(away_from=e_1)(b2)
    r_x = Vector3.rotor_from_vectors(
        from_vector=b_perp, to_vector=e_2
    ).normalize()

    # fully aligned: a = |a| e_1, b in the x-y plane, so the perpendicular is
    # |a| |b_perp| e_3.
    cross_aligned = (a.magnitude() * b_perp.magnitude()) * e_3

    # rotate the result back: undo R_x, then R_y, then R_z.
    return r_z.reverse().sandwich(
        r_y.reverse().sandwich(r_x.reverse().sandwich(cross_aligned))
    )


def _safe_cross(a_vals, b_vals):
    """cross_product on raw float triples, guarded: returns (0,0,0) for the
    degenerate (zero / parallel) inputs the core function doesn't define."""
    try:
        c = [
            float(x) for x in cross_product(Vector3(*a_vals), Vector3(*b_vals))
        ]
        if all(math.isfinite(x) for x in c):
            return c
    except Exception:
        pass
    return [0.0, 0.0, 0.0]


# ---------------------------------------------------------------------------
# Step-by-step animated demo (run by path).
#
# A faithful port of multivariate-math/src/crossproduct/crossproduct.py -- the
# original hand-rolled 12-step ``StepNumber`` state machine that animates the
# rotation-matrix proof of ``a x b``.  Step by step it: rotates ``a`` onto +x
# (about z, then y), rotates ``b`` into the x-y plane (about x), shows the
# triangle, projects ``b`` onto the y-z plane, rotates y->z / z->-y so the
# perpendicular points along the original a, undoes the three rotations to carry
# the perpendicular back to the world frame, and scales it by ``|a|`` to reveal
# the parallelogram / plane.
#
# It reuses mvp primitives instead of vendoring the source's renderer.py /
# pyMatrixStack.py, and draws EVERYTHING in the mvpvisualization solid style --
# no thin GL_LINES (which the source used, and which core-profile GL can't thicken
# without a geometry shader anyway):
#   * ``modelviewprojection.pyMatrixStack`` (same model/view/projection stack
#     API the source used),
#   * one solid ``_pipeline.build_pipeline("uniform_color.vert",
#     "passthrough.frag", color=True)`` drawing TRIANGLES, fed by ``_pipeline``'s
#     cylinder / arrow / sphere builders: the ground grid and unit circles are
#     ``build_cylinders_for_edges`` cylinders, the vectors and the x/y/z axes are
#     ``build_axis_arrow_solid`` cylinder-shaft-plus-cone arrows (oriented by the
#     source's ``angle_z`` / ``angle_y``), and the axis origin is a
#     ``build_origin_sphere_solid`` sphere.
#
# The billboard label images (``do_draw_image``) are commented out in the source,
# so they are skipped here too.
#
# GL imports are LOCAL to main() so importing this module stays headless (the
# math / test path imports it with no display).  Visuals are display-only; verify
# by running it.
# ---------------------------------------------------------------------------


def main() -> None:
    import math as _math
    import os
    from dataclasses import dataclass
    from enum import Enum, auto

    import glfw
    import numpy as np
    import OpenGL.GL as GL

    from modelviewprojection import pyMatrixStack as ms
    from modelviewprojection.mvpvisualization import _pipeline as _p
    from modelviewprojection.mvpvisualization import cayley_gl

    imgui = cayley_gl.imgui
    shader_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "mvpvisualization",
    )

    # -- window / context / imgui (mvp's setup; 3.3 core, depth test, esc-close)
    window, impl, imguiio = cayley_gl.setup("Cross Product Visualization")

    # -----------------------------------------------------------------------
    # ONE solid pipeline -- the mvpvisualization look: uniform-color TRIANGLES.
    # Everything (ground grid, unit circles, axes, vectors) is solid cylinder /
    # cone / sphere geometry from _pipeline, drawn through this pipeline, exactly
    # like the other mvpvisualization demos -- no thin GL_LINES anywhere.
    # -----------------------------------------------------------------------
    solid = _p.build_pipeline(
        "uniform_color.vert",
        "passthrough.frag",
        shader_dir=shader_dir,
        color=True,
    )

    AXIS_LEN = 1.0  # unit-length axes (match the unit circle)

    # -----------------------------------------------------------------------
    # Geometry generators (renderer.py + crossproduct.py).  These are static, so
    # build their VBO/VAO once; the model matrix is what changes per draw.
    # -----------------------------------------------------------------------
    def ground_cyl_mesh():
        # The ground as a grid of CYLINDERS on the z=0 (x-y) plane -- the
        # mvpvisualization ground look (build_cylinders_for_edges), instead of the
        # source's thin GL_LINES grid.
        edges = []
        for i in range(-10, 11):
            edges.append(((-10.0, float(i), 0.0), (10.0, float(i), 0.0)))
            edges.append(((float(i), -10.0, 0.0), (float(i), 10.0, 0.0)))
        return _p.build_cylinders_for_edges(edges, radius=0.025, slices=6)

    def unit_circle_cyl_mesh():
        # the unit circle on the z=0 (x-y) plane as a ring of thin cylinders.
        n = 64
        pts = [
            (
                _math.cos(2.0 * _math.pi * i / n),
                _math.sin(2.0 * _math.pi * i / n),
                0.0,
            )
            for i in range(n + 1)
        ]
        edges = [(pts[i], pts[i + 1]) for i in range(n)]
        return _p.build_cylinders_for_edges(edges, radius=0.02, slices=6)

    def arrow_mesh(magnitude):
        # A +Y cylinder-shaft-plus-cone arrow of total length ``magnitude`` -- the
        # mvpvisualization axis-arrow look (build_axis_arrow_solid), instead of the
        # source's thin two-line arrow.  Fixed vertex count for a given slices, so
        # the size is constant across magnitudes (one reusable dynamic VBO).
        cone = 0.18
        return _p.build_axis_arrow_solid(
            rod_radius=0.04,
            rod_length=max(0.05, float(magnitude) - cone),
            cone_radius=0.11,
            cone_length=cone,
            slices=16,
        )

    ground_vao, ground_n = _p.make_lines_vao(
        ground_cyl_mesh(), solid.attr_position
    )
    circle_vao, circle_n = _p.make_lines_vao(
        unit_circle_cyl_mesh(), solid.attr_position
    )
    axis_vao, axis_n = _p.make_lines_vao(
        arrow_mesh(AXIS_LEN), solid.attr_position
    )
    sphere_vao, sphere_n = _p.make_lines_vao(
        _p.build_origin_sphere_solid(radius=0.08), solid.attr_position
    )

    # One dynamic VBO/VAO reused for every vector arrow (mesh size is constant for
    # the fixed slice count; only the coordinates change per magnitude).
    _arrow_template = arrow_mesh(1.0)
    arrow_vbo = _p.make_vbo(
        np.zeros(_arrow_template.size, dtype=np.float32),
        usage=GL.GL_DYNAMIC_DRAW,
    )
    arrow_vao = _p.make_vao(
        [
            _p.AttribSpec(
                vbo=arrow_vbo,
                location=solid.attr_position,
                size=3,
                layout=(0, 0),
            )
        ]
    )

    # -----------------------------------------------------------------------
    # The renderer.py draw helpers, transcribed onto the mvp pipeline.
    # -----------------------------------------------------------------------
    def _draw_solid(vao, n, color):
        GL.glBindVertexArray(vao)
        GL.glUniform3f(solid.u_color, *color)
        _p.set_uniforms(solid.u_m, solid.u_v, solid.u_p)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, n)

    def _draw_on_planes(vao, n, color, xy, yz, zx):
        # draw a z=0-plane mesh on the requested plane(s), like the source did.
        GL.glUseProgram(solid.program)
        GL.glEnable(GL.GL_DEPTH_TEST)
        for enabled, axis in ((xy, None), (yz, "y"), (zx, "x")):
            if not enabled:
                continue
            with ms.push_matrix(ms.MatrixStack.model):
                if axis == "y":
                    ms.rotate_y(ms.MatrixStack.model, _math.radians(90.0))
                elif axis == "x":
                    ms.rotate_x(ms.MatrixStack.model, _math.radians(90.0))
                _draw_solid(vao, n, color)

    def draw_ground(
        width, height, xy=True, yz=False, zx=False, color=(0.3, 0.3, 0.3)
    ):
        _draw_on_planes(ground_vao, ground_n, color, xy, yz, zx)

    def draw_unit_circle(width, height, xy=True, yz=False, zx=False):
        _draw_on_planes(circle_vao, circle_n, (0.5, 0.5, 0.5), xy, yz, zx)

    def draw_vector(v, width, height):
        # solid cylinder + cone arrow (mvpvisualization style).  The mesh is a +Y
        # arrow; a single rotor carries +Y onto v's direction
        # (rotor_from_vectors, no trig) -- replacing the source's angle_z/angle_y
        # axis rotations.
        magnitude = _math.sqrt(v.x**2 + v.y**2 + v.z**2)
        if magnitude < 1e-9:
            return  # nothing to orient/draw for a zero-length vector
        mesh = arrow_mesh(magnitude)
        GL.glUseProgram(solid.program)
        GL.glBindVertexArray(arrow_vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, arrow_vbo)
        GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, mesh.nbytes, mesh)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        with ms.push_matrix(ms.MatrixStack.model):
            ms.multiply(
                ms.MatrixStack.model,
                cayleyscene.to_matrix(
                    rotor_rotation(
                        Vector3(0.0, 1.0, 0.0), Vector3(v.x, v.y, v.z)
                    )
                ),
            )
            if v.highlight:
                GL.glUniform3f(solid.u_color, 1.0, 1.0, 1.0)
            else:
                GL.glUniform3f(solid.u_color, v.r, v.g, v.b)
            _p.set_uniforms(solid.u_m, solid.u_v, solid.u_p)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, mesh.size // 3)

    def draw_axis(
        width, height, highlight_x=False, highlight_y=False, highlight_z=False
    ):
        # solid cylinder + cone axis arrows (mvpvisualization draw_axis look) plus
        # a small origin sphere; the +Y unit arrow reused, turned to x / y / z.
        GL.glUseProgram(solid.program)
        GL.glEnable(GL.GL_DEPTH_TEST)
        with ms.push_matrix(ms.MatrixStack.model):
            with ms.push_matrix(ms.MatrixStack.model):  # x (red)
                ms.rotate_z(ms.MatrixStack.model, _math.radians(-90.0))
                _draw_solid(
                    axis_vao,
                    axis_n,
                    (1.0, 1.0, 1.0) if highlight_x else (1.0, 0.0, 0.0),
                )
            with ms.push_matrix(ms.MatrixStack.model):  # z (blue)
                ms.rotate_y(ms.MatrixStack.model, _math.radians(90.0))
                ms.rotate_z(ms.MatrixStack.model, _math.radians(90.0))
                _draw_solid(
                    axis_vao,
                    axis_n,
                    (1.0, 1.0, 1.0) if highlight_z else (0.0, 0.0, 1.0),
                )
            # y (green)
            _draw_solid(
                axis_vao,
                axis_n,
                (1.0, 1.0, 1.0) if highlight_y else (0.0, 1.0, 0.0),
            )
            _draw_solid(sphere_vao, sphere_n, (1.0, 1.0, 1.0))  # origin

    # -----------------------------------------------------------------------
    # The animated vector type (renderer.Vector).  Just the raw components +
    # color now -- orientation is a rotor (see draw_vector), no stored angles.
    # -----------------------------------------------------------------------
    @dataclass
    class Vector:
        x: float
        y: float
        z: float
        r: float
        g: float
        b: float
        highlight: bool = False
        translate_amount: float = 0.0

    @dataclass
    class Camera:
        r: float = 0.0
        rot_y: float = 0.0
        rot_x: float = 0.0

    # -----------------------------------------------------------------------
    # The 12-step state machine (StepNumber) and globals, ported verbatim.
    # -----------------------------------------------------------------------
    class StepNumber(Enum):
        beginning = auto()  # 0
        rotate_z = auto()  # 1
        rotate_y = auto()  # 2
        rotate_x = auto()  # 3
        show_triangle = auto()  # 4
        project_onto_y = auto()  # 5
        rotate_to_z = auto()  # 6
        undo_rotate_x = auto()  # 7
        undo_rotate_y = auto()  # 8
        undo_rotate_z = auto()  # 9
        scale_by_mag_a = auto()  # 10
        show_plane = auto()  # 11

    @dataclass
    class Globals:
        vec1: object = None
        vec2: object = None
        vec3: object = None
        swap: bool = False
        camera: object = None
        use_ortho: bool = False
        # half-height of the orthographic view volume (the ortho "zoom").  Kept
        # SEPARATE from the perspective zoom (camera.r) so each view remembers its
        # own zoom; the mouse wheel drives whichever view is active.
        ortho_extent: float = 10.0
        animation_time: float = 0.0
        current_animation_start_time: float = 0.0
        animation_time_multiplier: float = 1.0
        animation_paused: bool = False
        # The per-step "do_*" latches and the old "rotate_yz_90 / do_scale /
        # do_remove_ground" gates are gone: each is now derived from step_number
        # via reached()/step_progress() (the lightweight timeline).  Only the
        # user-toggled relative-coordinate reveals remain as state.
        draw_first_relative_coordinates: bool = False
        draw_second_relative_coordinates: bool = False
        draw_third_relative_coordinates: bool = False
        new_b: object = None
        # The alignment Cayley graph + its three rotor edges (and inverses),
        # rebuilt from the vectors whenever they change (rebuild_alignment).  The
        # animation walks these instead of accumulating atan2-derived rotate_*.
        graph: object = None
        cross_aligned: object = None
        r_z: object = None
        r_y: object = None
        r_x: object = None
        r_z_inv: object = None
        r_y_inv: object = None
        r_x_inv: object = None
        # cache of realized 4x4 matrices for the STATIC transform pieces (the
        # -90 coords, each completed rotor edge at full).  Reset when the vectors
        # change (rebuild_alignment); only the actively-animating edge is realized
        # fresh each frame.  Keeps later stages from recomputing the whole chain.
        mcache: object = None
        draw_coordinate_system_of_natural_basis: bool = True
        step_number: object = StepNumber.beginning
        draw_undo_rotate_x_relative_coordinates: bool = False
        draw_undo_rotate_y_relative_coordinates: bool = False
        draw_undo_rotate_z_relative_coordinates: bool = False
        auto_rotate_camera: bool = False
        seconds_per_operation: float = 2.0
        auto_play: bool = False
        vec3_after_rotate: object = None
        highlight_x: bool = False
        highlight_y: bool = False
        highlight_z: bool = False
        highlight_relative_x: bool = False
        highlight_relative_y: bool = False
        highlight_relative_z: bool = False

    g = Globals()

    def initialize_vecs():
        if not g.swap:
            g.vec1 = Vector(3.0, 4.0, 5.0, 1.0, 0.5, 0.0, highlight=False)
            g.vec2 = Vector(-1.0, 2.0, 2.0, 0.5, 0.0, 1.0, highlight=False)
        else:
            g.vec1 = Vector(-1.0, 2.0, 2.0, 1.0, 0.5, 0.0, highlight=False)
            g.vec2 = Vector(3.0, 4.0, 5.0, 0.5, 0.0, 1.0, highlight=False)
        g.vec3 = None

    initialize_vecs()
    g.camera = Camera(
        r=22.0, rot_y=_math.radians(45.0), rot_x=_math.radians(35.264)
    )

    def rebuild_alignment():
        # Build the alignment Cayley graph from the current vectors (fixed for the
        # run) and cache its three rotor edges + their inverses.  The animation
        # walks these; the edges are rotor_from_vectors on projections -- no trig
        # (see build_alignment_graph).  Rebuild whenever the vectors change.
        a3 = Vector3(g.vec1.x, g.vec1.y, g.vec1.z)
        b3 = Vector3(g.vec2.x, g.vec2.y, g.vec2.z)
        g.graph, g.cross_aligned = build_alignment_graph(a3, b3)
        e = g.graph.edges  # world--R_z-->a_in_xz--R_y-->a_on_x--R_x-->b_in_xy
        g.r_z, g.r_y, g.r_x = e[0].function(), e[1].function(), e[2].function()
        g.r_z_inv, g.r_y_inv, g.r_x_inv = (
            inverse(g.r_z),
            inverse(g.r_y),
            inverse(g.r_x),
        )
        # drop cached realized matrices -- the edges (and |a|) just changed.
        g.mcache = {}

    def restart():
        # Reset the animation/step state, keeping the current vectors + camera
        # (matches the source's restart()).
        vec1, vec2, vec3, camera = g.vec1, g.vec2, g.vec3, g.camera
        for f in Globals.__dataclass_fields__:
            setattr(g, f, getattr(Globals(), f))
        g.vec1, g.vec2, g.vec3, g.camera = vec1, vec2, vec3, camera
        g.swap = False
        g.draw_coordinate_system_of_natural_basis = True
        rebuild_alignment()  # vectors fixed for the run -> build the rotor graph

    restart()

    def current_animation_ratio():
        if g.step_number == StepNumber.beginning:
            return 0.0
        return min(
            1.0,
            (g.animation_time - g.current_animation_start_time)
            / g.seconds_per_operation,
        )

    # --- the timeline surface: two queries over the ordered StepNumber list,
    # replacing the per-step do_*/draw_* latch flags and the repeated ratio
    # ladders that used to drive draw_scene. -----------------------------------
    def reached(step):
        """True once the timeline has advanced to or past ``step`` -- i.e. that
        step's operation has been triggered (replaces the old ``do_*`` flags)."""
        return g.step_number.value >= step.value

    def step_progress(step):
        """The animation fraction of ``step``: 0 before it, ramping 0->1 while it
        is the current step, 1 after.  Replaces the ``ratio = ... if step == X
        else 0.0 if ... else 1.0`` ladders."""
        if g.step_number.value < step.value:
            return 0.0
        if g.step_number.value > step.value:
            return 1.0
        return current_animation_ratio()

    # -----------------------------------------------------------------------
    # Camera input (mouse drag + arrow keys), source's handle_inputs.
    # -----------------------------------------------------------------------
    def handle_inputs(previous_mouse_position):
        if imguiio.want_capture_mouse:
            # Don't orbit while the cursor is over an imgui panel.
            if glfw.PRESS != glfw.get_mouse_button(
                window, glfw.MOUSE_BUTTON_LEFT
            ):
                return None
            return previous_mouse_position
        if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
            g.camera.rot_y -= _math.radians(1.0)
            g.use_ortho = False
        if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
            g.camera.rot_y += _math.radians(1.0)
            g.use_ortho = False
        if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
            g.camera.rot_x -= _math.radians(1.0)
            g.use_ortho = False
        if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
            g.camera.rot_x += _math.radians(1.0)
            g.use_ortho = False

        new_mouse_position = glfw.get_cursor_pos(window)
        return_none = False
        if glfw.PRESS == glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT):
            if previous_mouse_position:
                g.camera.rot_y -= 0.2 * _math.radians(
                    new_mouse_position[0] - previous_mouse_position[0]
                )
                g.camera.rot_x += 0.2 * _math.radians(
                    new_mouse_position[1] - previous_mouse_position[1]
                )
                g.use_ortho = False
        else:
            return_none = True

        g.camera.rot_x = max(
            -_math.pi / 2.0, min(_math.pi / 2.0, g.camera.rot_x)
        )
        return None if return_none else new_mouse_position

    # Scroll zoom (source's scroll_callback), only when not over imgui.
    def scroll_callback(win, xoffset, yoffset):
        if imguiio.want_capture_mouse:
            return
        if g.use_ortho:
            # zoom the ortho volume (wider/taller = zoomed out).  Same log feel as
            # the perspective zoom, but on its OWN state so the two don't interfere.
            g.ortho_extent += -1 * (yoffset * _math.log(g.ortho_extent))
            if g.ortho_extent < 2.0:
                g.ortho_extent = 2.0
        else:
            g.camera.r = g.camera.r + -1 * (yoffset * _math.log(g.camera.r))
            if g.camera.r < 3.0:
                g.camera.r = 3.0

    glfw.set_scroll_callback(window, scroll_callback)

    win_state = cayley_gl.WindowState()

    def on_key(win, key, scancode, action, mods):
        cayley_gl.common_key(win, win_state, key, action)
        if action != glfw.PRESS:
            return
        if key == glfw.KEY_SPACE:  # spacebar advances one step
            advance_step()
        elif key == glfw.KEY_R:  # restart the derivation
            restart()
        elif key == glfw.KEY_P:  # toggle autoplay
            g.auto_play = not g.auto_play

    glfw.set_key_callback(window, on_key)

    # -----------------------------------------------------------------------
    # The imgui control panel: the source's giant "Cross Product" window, with
    # the per-step advance buttons / relative-coordinate checkboxes / highlight
    # buttons.  Translated to imgui_bundle signatures.
    # -----------------------------------------------------------------------
    # --- step machine: one consolidated "advance", labels, and the
    # current-step relative-coordinate flag -- so the per-step controls live in
    # the menubar (like the other mvp demos) instead of a floating panel.
    _STEP_NEXT_LABEL = {
        StepNumber.beginning: "Rotate Z (a into x-z plane)",
        StepNumber.rotate_z: "Rotate Y (a onto x axis)",
        StepNumber.rotate_y: "Rotate X (b into x-y plane)",
        StepNumber.rotate_x: "Show Triangle",
        StepNumber.show_triangle: "Project b onto y-z plane",
        StepNumber.project_onto_y: "Rotate Y->Z, Z->-Y",
        StepNumber.rotate_to_z: "Undo Rotate X",
        StepNumber.undo_rotate_x: "Undo Rotate Y",
        StepNumber.undo_rotate_y: "Undo Rotate Z",
        StepNumber.undo_rotate_z: "Scale by |a|",
        StepNumber.scale_by_mag_a: "Show Plane (a x b)",
        StepNumber.show_plane: None,
    }
    _REL_FLAG = {
        StepNumber.beginning: "draw_first_relative_coordinates",
        StepNumber.rotate_z: "draw_second_relative_coordinates",
        StepNumber.rotate_y: "draw_third_relative_coordinates",
        StepNumber.rotate_to_z: "draw_undo_rotate_x_relative_coordinates",
        StepNumber.undo_rotate_x: "draw_undo_rotate_y_relative_coordinates",
        StepNumber.undo_rotate_y: "draw_undo_rotate_z_relative_coordinates",
    }
    # the ordered timeline of steps (StepNumber in declaration order).
    _STEP_SEQUENCE = list(StepNumber)

    def step_ready():
        # the first move is available at once; later ones wait for the current
        # animation to finish (the source gated on current_animation_ratio()).
        return (
            g.step_number == StepNumber.beginning
            or current_animation_ratio() >= 0.999999
        )

    # Steps entered WITHOUT restarting the animation clock -- the source's
    # "instant reveal" steps (the triangle / the final plane appear at once and
    # don't gate the next press).  Every other step animates over
    # ``seconds_per_operation`` from when it is entered.
    _INSTANT_STEPS = (StepNumber.show_triangle, StepNumber.show_plane)

    def advance_step():
        if not step_ready():
            return
        sn = g.step_number
        if sn == StepNumber.show_plane:  # last step on the timeline
            return
        # The one genuine side effect: on leaving "rotate_x" (a is on +x, b is in
        # the x-y plane), read the now-aligned b out of the model matrix to build
        # the perpendicular / cross vector ``vec3``.
        if sn == StepNumber.rotate_x:
            g.vec3_after_rotate = np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.model), dtype=np.float32
            ) @ np.array([g.vec2.x, g.vec2.y, g.vec2.z, 1.0], dtype=np.float32)
            g.vec3 = Vector(
                x=0.0,
                y=-g.vec3_after_rotate[2],
                z=g.vec3_after_rotate[1],
                r=0.0,
                g=1.0,
                b=0.0,
            )
            g.vec3.translate_amount = g.vec3_after_rotate[0]
        # advance to the next step on the timeline; (re)start its animation unless
        # it is an instant-reveal step.
        g.step_number = _STEP_SEQUENCE[_STEP_SEQUENCE.index(sn) + 1]
        if g.step_number not in _INSTANT_STEPS:
            g.current_animation_start_time = g.animation_time

    # -----------------------------------------------------------------------
    # The scene draw.  Transforms are gacalc InvertibleFunctions, realized to 4x4s
    # (to_matrix = the function's action on the basis) and multiplied in numpy --
    # to_matrix(compose([A, B])) == to_matrix(A) @ to_matrix(B), verified.  The
    # STATIC pieces (the -90 coords, each completed rotor edge at full) are cached
    # in g.mcache and reused; only the one actively-animating edge is realized
    # fresh each frame, so per-frame cost stays ~constant instead of growing with
    # the stages.  (The realize cost lives in to_matrix, not in compose, because
    # the demo's rotors route through gacalc's slow Gn path -- see tasks doc.)
    # -----------------------------------------------------------------------
    _I4 = np.eye(4, dtype=float)
    # axis (unit-vector) colors.  The relative basis is drawn in the two colors of
    # the plane it rotates in: x-y -> red+green, z-x -> red+blue, y-z -> green+blue.
    _RED = (1.0, 0.0, 0.0)
    _GREEN = (0.0, 1.0, 0.0)
    _BLUE = (0.0, 0.0, 1.0)
    # relative-frame graph paper: lighter than the world ground (0.3) so it reads
    # as a distinct plane even when it starts coincident with a world grid.
    _REL_GROUND = (0.55, 0.55, 0.55)

    def draw_scene(width, height):
        def set_model_M(m):
            # Upload a realized 4x4 to the model matrix; copy so a cached matrix is
            # never mutated by a later push_matrix / rotate in a draw helper.
            ms.set_current_matrix(ms.MatrixStack.model, m.copy())

        def edge_M(edge, r):
            # Realized 4x4 of a rotor edge at fraction r: identity at r<=0 (free),
            # the CACHED full rotation at r>=1 (realized once per stage), and a
            # fresh realize only for the actively-animating edge (0 < r < 1).
            if r <= 0.0:
                return _I4
            if r >= 1.0:
                m = g.mcache.get(id(edge))
                if m is None:
                    m = cayleyscene.to_matrix(edge.at(1.0))
                    g.mcache[id(edge)] = m
                return m
            return cayleyscene.to_matrix(edge.at(r))

        def const_M(key, build):
            # Realized 4x4 of a CONSTANT gacalc transform, cached by a stable key.
            m = g.mcache.get(key)
            if m is None:
                m = cayleyscene.to_matrix(build())
                g.mcache[key] = m
            return m

        def relative_axes():
            draw_axis(
                width,
                height,
                highlight_x=g.highlight_relative_x,
                highlight_y=g.highlight_relative_y,
                highlight_z=g.highlight_relative_z,
            )

        def draw_relative_ground(model_M, *, xy=False, yz=False, zx=False):
            # the relative plane's graph paper, in a distinct color, drawn with a
            # polygon offset toward the viewer so it WINS the depth tie with the
            # world ground when the two are coincident (at the start of a phase) --
            # otherwise GL_LESS hides it behind the world grid until it rotates off.
            set_model_M(model_M)
            GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
            GL.glPolygonOffset(-1.0, -1.0)
            draw_ground(width, height, xy=xy, yz=yz, zx=zx, color=_REL_GROUND)
            GL.glPolygonOffset(0.0, 0.0)
            GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)

        def draw_relative_basis(model_M, drop, c_first, c_second):
            # The relative frame's in-plane 2-D basis: the two MODEL-space unit axes
            # of this phase's plane of rotation (the third, ``drop``, axis is the
            # plane normal: 0/1/2 = x/y/z), drawn UNDER ``model_M`` so they rotate
            # with the animation -- exactly the original demo's draw_axis approach.
            #
            # ``model_M`` is built from the input vector's projection (its x-axis IS
            # that projection, made unit -- see the o = ... @ r_*_inv expressions
            # below), so the first in-plane axis lands ON the projected input vector
            # and the second is it turned 90 deg in the plane.  Colors are the two
            # axis colors of the plane (c_first, c_second).
            #
            # NB: draw the MODEL axes under model_M, NOT the input vector projected
            # into world space -- the latter is already rotated, so drawing it under
            # model_M rotates it a SECOND time (the old bug: basis off by the phase
            # angle / flung out of the plane).
            set_model_M(model_M)
            axes = [i for i in range(3) if i != drop]  # the two in-plane axes
            for axis, color in zip(axes, (c_first, c_second)):
                comps = [0.0, 0.0, 0.0]
                comps[axis] = 1.0
                draw_vector(
                    Vector(comps[0], comps[1], comps[2], *color), width, height
                )

        ms.set_to_identity_matrix(ms.MatrixStack.model)
        ms.set_to_identity_matrix(ms.MatrixStack.view)
        ms.set_to_identity_matrix(ms.MatrixStack.projection)

        # Projection stays a real GL matrix -- the perspective/ortho squash is not
        # an affine InvertibleFunction (cayleyscene decision #4).  The view is
        # realized fresh each frame (constant cost, doesn't grow with stages).
        if g.use_ortho:
            ext = g.ortho_extent  # half-height of the volume (the ortho zoom)
            ms.ortho(
                left=-ext * float(width) / float(height),
                right=ext * float(width) / float(height),
                bottom=-ext,
                top=ext,
                near=10.0,
                far=-10.0,
            )
            view_fn = compose(
                [rotate_x(g.camera.rot_x), rotate_y(-g.camera.rot_y)]
            )
        else:
            ms.perspective(
                field_of_view=45.0,
                aspect_ratio=float(width) / float(height),
                near_z=0.1,
                far_z=10000.0,
            )
            view_fn = compose(
                [
                    translate(Vector3(0.0, 0.0, -g.camera.r)),
                    rotate_x(g.camera.rot_x),
                    rotate_y(-g.camera.rot_y),
                ]
            )
        ms.set_current_matrix(
            ms.MatrixStack.view, cayleyscene.to_matrix(view_fn)
        )

        # "math coordinate system": everything is drawn under a -90deg x-rotation
        # (cached).  Model = coords @ (rotor edges), each realized + cached.
        coords_M = const_M("coords", lambda: rotate_x(_math.radians(-90.0)))
        set_model_M(coords_M)

        if g.draw_coordinate_system_of_natural_basis:
            if not reached(StepNumber.show_plane):
                draw_ground(width, height)
                draw_ground(width, height, xy=False, zx=True)
                draw_unit_circle(width, height, xy=True, yz=True, zx=True)

        draw_axis(
            width,
            height,
            highlight_x=g.highlight_x,
            highlight_y=g.highlight_y,
            highlight_z=g.highlight_z,
        )

        # --- the rotation accumulation, third -> second -> first rotate.  Each
        # rotor's matrix is post-multiplied onto model_M (== the old stack); the
        # forward edge plays during its step, the inverse during the undo. ---
        model_M = coords_M
        if reached(StepNumber.rotate_x):
            if step_progress(StepNumber.rotate_x) > 0.9999:
                g.draw_third_relative_coordinates = False
            model_M = (
                model_M
                @ edge_M(g.r_x, step_progress(StepNumber.rotate_x))
                @ edge_M(g.r_x_inv, step_progress(StepNumber.undo_rotate_x))
            )
            set_model_M(model_M)
            if g.draw_undo_rotate_x_relative_coordinates and not reached(
                StepNumber.show_plane
            ):
                draw_ground(width, height, xy=False, yz=True)
                relative_axes()

        if g.draw_third_relative_coordinates and not reached(
            StepNumber.show_triangle
        ):
            # rotate_x: y-z plane (green + blue).  Same uniform form as every forward
            # phase: o = coords @ r_x(t) @ r_x_inv(full).  Starts tilted in the
            # relative frame (t=0 -> coords @ r_x_inv, basis along b's perpendicular
            # part) and rotates onto the WORLD y-z plane (t=1 -> coords).  NB: it
            # does NOT bake in the prior R_y / R_z -- the original's draw_third runs
            # before do_second/do_first, so it never sees them; baking them in (the
            # old special case) over-rotated the plane out of y-z.
            o = (
                coords_M
                @ edge_M(g.r_x, step_progress(StepNumber.rotate_x))
                @ edge_M(g.r_x_inv, 1.0)
            )
            draw_relative_ground(o, yz=True)
            draw_relative_basis(o, 0, _GREEN, _BLUE)

        if reached(StepNumber.rotate_y):
            if step_progress(StepNumber.rotate_y) > 0.99:
                g.draw_second_relative_coordinates = False
            model_M = (
                model_M
                @ edge_M(g.r_y, step_progress(StepNumber.rotate_y))
                @ edge_M(g.r_y_inv, step_progress(StepNumber.undo_rotate_y))
            )
            set_model_M(model_M)
            if g.draw_undo_rotate_y_relative_coordinates and not reached(
                StepNumber.show_plane
            ):
                draw_ground(width, height, xy=False, zx=True)
                relative_axes()

        if g.draw_second_relative_coordinates and not reached(
            StepNumber.rotate_x
        ):
            # rotate_y: z-x plane (red + blue).  Same uniform form: o = coords @
            # r_y(t) @ r_y_inv(full).  Starts tilted in the relative frame (t=0 ->
            # coords @ r_y_inv, red along a-after-R_z) and rotates onto the WORLD z-x
            # plane (t=1 -> coords).  NB: it does NOT bake in the prior R_z -- a is
            # already in the z-x plane once R_z has run, so the original's draw_second
            # (which executes before do_first) never applies R_z here; baking it in
            # (the old special case) rotated the plane/basis out of z-x.
            o = (
                coords_M
                @ edge_M(g.r_y, step_progress(StepNumber.rotate_y))
                @ edge_M(g.r_y_inv, 1.0)
            )
            draw_relative_ground(o, zx=True)
            draw_relative_basis(o, 1, _RED, _BLUE)

        if reached(StepNumber.rotate_z):
            if step_progress(StepNumber.rotate_z) > 0.99:
                g.draw_first_relative_coordinates = False
            model_M = (
                model_M
                @ edge_M(g.r_z, step_progress(StepNumber.rotate_z))
                @ edge_M(g.r_z_inv, step_progress(StepNumber.undo_rotate_z))
            )
            set_model_M(model_M)
            if g.draw_undo_rotate_z_relative_coordinates and not reached(
                StepNumber.show_plane
            ):
                draw_ground(width, height)
                relative_axes()

        if g.draw_first_relative_coordinates and not reached(
            StepNumber.rotate_y
        ):
            # rotate_z: x-y plane (red + green).  The uniform forward form: o =
            # coords @ r_z(t) @ r_z_inv(full).  At beginning (t=0) the graph paper
            # sits in the tilted relative frame (x' along a's x-y shadow), and as R_z
            # animates it rotates down onto the WORLD x-y plane (t=1 -> coords), then
            # disappears.  No prior rotation to bake in (this is the first phase).
            o = (
                coords_M
                @ edge_M(g.r_z, step_progress(StepNumber.rotate_z))
                @ edge_M(g.r_z_inv, 1.0)
            )
            draw_relative_ground(o, xy=True)
            draw_relative_basis(o, 2, _RED, _GREEN)

        # --- the vec3 (cross) chain: project -> rotate y->z -> undo -> scale,
        # built fresh from the (cached) math frame. ---
        if g.vec3 and reached(StepNumber.show_triangle):
            chain_M = coords_M
            if reached(StepNumber.undo_rotate_z):
                chain_M = chain_M @ edge_M(
                    g.r_z_inv, step_progress(StepNumber.undo_rotate_z)
                )
            if reached(StepNumber.undo_rotate_y):
                chain_M = chain_M @ edge_M(
                    g.r_y_inv, step_progress(StepNumber.undo_rotate_y)
                )
            if reached(StepNumber.undo_rotate_x):
                chain_M = chain_M @ edge_M(
                    g.r_x_inv, step_progress(StepNumber.undo_rotate_x)
                )

            if reached(StepNumber.scale_by_mag_a):
                if reached(StepNumber.show_plane):
                    set_model_M(chain_M)
                    draw_ground(width, height)
                magnitude = _math.sqrt(g.vec1.x**2 + g.vec1.y**2 + g.vec1.z**2)
                chain_M = chain_M @ const_M(
                    "scale",
                    lambda: scale_non_uniform(1.0, 1.0, magnitude),
                )

            ratio = step_progress(StepNumber.project_onto_y)
            chain_M = chain_M @ cayleyscene.to_matrix(
                translate(
                    Vector3(g.vec3.translate_amount * (1.0 - ratio), 0.0, 0.0)
                )
            )

            GL.glDisable(GL.GL_DEPTH_TEST)
            if reached(StepNumber.rotate_to_z):
                ratio = step_progress(StepNumber.rotate_to_z)
                g.vec3.r, g.vec3.g, g.vec3.b = (
                    0.0 * (1.0 - ratio),
                    1.0 * (1.0 - ratio),
                    1.0 * ratio,
                )
                set_model_M(
                    chain_M
                    @ cayleyscene.to_matrix(
                        rotate_x(_math.radians(90.0 * ratio))
                    )
                )
                draw_vector(g.vec3, width, height)
            else:
                set_model_M(chain_M)
                draw_vector(g.vec3, width, height)
            GL.glEnable(GL.GL_DEPTH_TEST)

        GL.glDisable(GL.GL_DEPTH_TEST)
        set_model_M(model_M)
        draw_vector(g.vec1, width, height)
        draw_vector(g.vec2, width, height)
        GL.glEnable(GL.GL_DEPTH_TEST)

    # -----------------------------------------------------------------------
    # Per-frame entry point for cayley_gl.run_loop.  run_loop clears + sets the
    # full-window viewport and brackets imgui.new_frame()/render() for us.
    # -----------------------------------------------------------------------
    previous_mouse_position = [None]
    _last_clock = [None]

    def frame(w, h):
        # Advance the animation by REAL elapsed time, not a fixed 1/60 per frame,
        # so a stage takes its seconds_per_operation in wall-clock seconds
        # regardless of frame rate.  dt is clamped so a hitch/pause can't jump the
        # animation.
        now = glfw.get_time()
        dt = 0.0 if _last_clock[0] is None else min(now - _last_clock[0], 0.1)
        _last_clock[0] = now
        if not g.animation_paused:
            g.animation_time += dt * g.animation_time_multiplier
        if g.auto_rotate_camera:
            g.camera.rot_y += (
                _math.radians(6.0) * dt
            )  # ~6 deg/sec, fps-independent
        if g.auto_play:
            advance_step()
        previous_mouse_position[0] = handle_inputs(previous_mouse_position[0])
        draw_scene(w, h)

    def _toggle(attr):
        setattr(g, attr, not getattr(g, attr))

    def _view_down(rot_x, rot_y):
        g.camera.rot_x = rot_x
        g.camera.rot_y = rot_y
        g.use_ortho = True

    def menubar():
        if not imgui.begin_main_menu_bar():
            return
        if imgui.begin_menu("File", True):
            cayley_gl.menu_action(
                "Quit",
                "Esc",
                lambda: glfw.set_window_should_close(window, True),
            )
            imgui.end_menu()
        if imgui.begin_menu("Animation", True):
            nxt = _STEP_NEXT_LABEL[g.step_number]
            if nxt is None:
                imgui.menu_item("(final step)", "", False, False)
            else:
                cayley_gl.menu_action("Next: " + nxt, "Space", advance_step)
            cayley_gl.menu_action("Restart", "R", restart)
            cayley_gl.menu_action(
                "AutoPlay",
                "P",
                lambda: _toggle("auto_play"),
                selected=g.auto_play,
            )
            _, g.seconds_per_operation = imgui.slider_float(
                "Seconds / step", g.seconds_per_operation, 0.25, 5.0
            )
            flag = _REL_FLAG.get(g.step_number)
            if flag is not None:
                cayley_gl.menu_action(
                    "Draw Relative Coordinates",
                    "",
                    lambda f=flag: _toggle(f),
                    selected=getattr(g, flag),
                )
            imgui.end_menu()
        if imgui.begin_menu("Camera", True):
            cayley_gl.menu_action(
                "Auto-Rotate",
                "",
                lambda: _toggle("auto_rotate_camera"),
                selected=g.auto_rotate_camera,
            )
            if not g.use_ortho:
                _, g.camera.r = imgui.slider_float(
                    "Camera Radius", g.camera.r, 3.0, 130.0
                )
            cayley_gl.menu_action(
                "View Down X Axis", "", lambda: _view_down(0.0, _math.pi / 2.0)
            )
            cayley_gl.menu_action(
                "View Down -Y Axis", "", lambda: _view_down(0.0, 0.0)
            )
            cayley_gl.menu_action(
                "View Down Z Axis", "", lambda: _view_down(_math.pi / 2.0, 0.0)
            )
            imgui.end_menu()
        if imgui.begin_menu("Vectors", True):
            ca, (g.vec1.x, g.vec1.y, g.vec1.z) = imgui.input_float3(
                "a", [g.vec1.x, g.vec1.y, g.vec1.z]
            )
            cb, (g.vec2.x, g.vec2.y, g.vec2.z) = imgui.input_float3(
                "b", [g.vec2.x, g.vec2.y, g.vec2.z]
            )
            if ca or cb:  # editing the inputs restarts the derivation
                g.animation_time = 0.0
                g.step_number = StepNumber.beginning
                rebuild_alignment()  # vectors changed -> rebuild the rotor graph
            cayley_gl.menu_action(
                "Swap a and b",
                "",
                lambda: (_toggle("swap"), initialize_vecs(), restart()),
            )
            cayley_gl.menu_action(
                "Highlight a",
                "",
                lambda: (
                    setattr(g.vec1, "highlight", not g.vec1.highlight),
                    setattr(g.vec2, "highlight", False),
                ),
                selected=g.vec1.highlight,
            )
            cayley_gl.menu_action(
                "Highlight b",
                "",
                lambda: (
                    setattr(g.vec2, "highlight", not g.vec2.highlight),
                    setattr(g.vec1, "highlight", False),
                ),
                selected=g.vec2.highlight,
            )
            imgui.end_menu()
        if imgui.begin_menu("Highlight", True):
            for name, attr in (
                ("x", "highlight_x"),
                ("y", "highlight_y"),
                ("z", "highlight_z"),
                ("x'", "highlight_relative_x"),
                ("y'", "highlight_relative_y"),
                ("z'", "highlight_relative_z"),
            ):
                cayley_gl.menu_action(
                    name,
                    "",
                    lambda a=attr: _toggle(a),
                    selected=getattr(g, attr),
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
                "Draw Natural Basis",
                "",
                lambda: _toggle("draw_coordinate_system_of_natural_basis"),
                selected=g.draw_coordinate_system_of_natural_basis,
            )
            imgui.end_menu()
        imgui.end_main_menu_bar()

    cayley_gl.run_loop(window, impl, frame, menubar, on_key)


if __name__ == "__main__":
    main()
