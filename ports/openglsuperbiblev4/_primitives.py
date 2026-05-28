"""Precomputed procedural geometry for the SuperBible ports.

Several ports hand-rolled ``glutSolidSphere`` / ``gltDrawTorus`` style helpers
that re-ran their ``sin``/``cos`` tessellation inside the per-frame draw. The
geometry is identical every frame, so we run the trig **once** (at setup or
import) and just replay the stored vertices each frame.

Bill's constraint (2026-05-28): **no display lists or VBOs** unless the C++
source already used them. So rendering stays immediate-mode ``glBegin``/
``glEnd`` -- only *when* the trig runs changes, not *how* it draws.

A precomputed mesh is the pair ``(primitive_mode, bands)`` where ``bands`` is a
list of vertex bands (one ``glBegin``/``glEnd`` batch each) and every vertex is
the 8-tuple ``(nx, ny, nz, s, t, x, y, z)`` -- normal, texture coord, position.
Build with the ``build_*`` functions; ``draw_mesh()`` emits a mesh each frame.
Untextured demos leave ``textured=False`` (the default) so the stored ``s, t``
are simply not emitted.

This module deliberately depends only on ``math`` and ``OpenGL.GL`` (no glfw /
imgui), so the minimal immediate-mode demos can import it without pulling in the
window/UI machinery that lives in ``_common.py``.

Demos import it the same way as ``_common`` -- prepend the ports root to
``sys.path`` (two levels up from ``chaptNN/<demo>/<demo>.py``)::

    PWD = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
    import _primitives  # noqa: E402
"""

from __future__ import annotations

import math

import OpenGL.GL as GL

Vertex = tuple[float, float, float, float, float, float, float, float]
Mesh = tuple[int, list[list[Vertex]]]


def build_sphere(radius: float, slices: int, stacks: int, *,
                 swap_winding: bool = False) -> Mesh:
    """Precompute a solid sphere as a stack of ``GL_QUAD_STRIP`` bands (one per
    latitude band) -- the same vertices the hand-written ``draw_solid_sphere``
    used to emit every frame.

    ``swap_winding`` emits the two latitude rows in (lat1, lat0) order instead
    of (lat0, lat1); a few demos (e.g. chapt04/solar) need the swapped order so
    the camera-facing side winds CCW and isn't culled. Most use the default.
    """
    bands: list[list[Vertex]] = []
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        sin0, cos0 = math.sin(lat0), math.cos(lat0)
        sin1, cos1 = math.sin(lat1), math.cos(lat1)
        v0, v1 = float(i) / stacks, float(i + 1) / stacks
        band: list[Vertex] = []
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            u = float(j) / slices
            row0 = (cl * cos0, sl * cos0, sin0, u, v0,
                    radius * cl * cos0, radius * sl * cos0, radius * sin0)
            row1 = (cl * cos1, sl * cos1, sin1, u, v1,
                    radius * cl * cos1, radius * sl * cos1, radius * sin1)
            if swap_winding:
                band.append(row1)
                band.append(row0)
            else:
                band.append(row0)
                band.append(row1)
        bands.append(band)
    return (GL.GL_QUAD_STRIP, bands)


def draw_mesh(mesh: Mesh, *, textured: bool = False) -> None:
    """Emit a precomputed mesh via immediate mode -- one ``glBegin``/``glEnd``
    per band, ``glNormal3f`` + ``glVertex3f`` per vertex. Set ``textured=True``
    to also emit each vertex's stored ``(s, t)`` texture coordinate."""
    mode, bands = mesh
    for band in bands:
        GL.glBegin(mode)
        for v in band:
            GL.glNormal3f(v[0], v[1], v[2])
            if textured:
                GL.glTexCoord2f(v[3], v[4])
            GL.glVertex3f(v[5], v[6], v[7])
        GL.glEnd()
