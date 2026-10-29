# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

"""demo22's scene *data*, round-tripped through a glTF 2.0 ``.glb`` file.

This module has no GL and no window: it builds the five demo22 meshes, the
four textures and the directional light, writes them to a ``.glb`` with
:func:`write_glb`, and reads them back with :func:`read_glb`.  ``demo22b.py``
calls both at startup, then uploads what comes back and renders it with
demo22's pipeline unchanged -- so a real asset format carries exactly the
*data drawn* (geometry, textures, light) and nothing else (shaders, the two
shadow algorithms, the stage toggles, the camera all stay in app code).

Because it is context-free it is also a self-contained inspection tool and is
unit-tested without a GPU::

    python export_scene.py scene.glb      # write + print a summary

Standalone by design.  The accessor-decode approach below is a self-contained
copy so the course demos do not depend on any ports tree.  It needs only
numpy, pygltflib and imageio -- not the rest of the modelviewprojection
package -- so it round-trips in isolation.

The five meshes keep demo22's 8-float interleaved vertex layout (3 position,
3 normal, 2 uv).  On the way out each mesh is de-interleaved into three glTF
accessors (POSITION / NORMAL / TEXCOORD_0); on the way back they are
re-interleaved into the exact same float32 array demo22's ``_build_*``
functions produce, so the whole downstream pipeline is byte-for-byte
unchanged (proven by tests/test_demo22b_gltf_roundtrip.py).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import imageio.v3 as iio
import numpy as np
from pygltflib import (
    ARRAY_BUFFER,
    FLOAT,
    GLTF2,
    SCALAR,
    VEC2,
    VEC3,
    VEC4,
    Accessor,
    Asset,
    Attributes,
    Buffer,
    BufferView,
    Image,
    Material,
    Mesh,
    Node,
    PbrMetallicRoughness,
    Primitive,
    Sampler,
    Scene,
    Texture,
    TextureInfo,
)

# glTF primitive mode integers; these equal the GL draw-mode enums, so the
# value read back drives glDrawArrays directly (GL_LINES == 1, GL_TRIANGLES
# == 4).
MODE_LINES: int = 1
MODE_TRIANGLES: int = 4

# glTF sampler filter / wrap enums (also the GL enum values).
_LINEAR: int = 9729
_REPEAT: int = 10497

# glTF component count per accessor type, for decode.
_TYPE_COUNT: dict[str, int] = {SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4}

# demo22's interleaved layout: 3 position + 3 normal + 2 uv.
FLOATS_PER_VERTEX: int = 8

# --- scene constants (kept identical to demo22) ------------------------------
# The marker colours and the floor plane live in demo22's app code (they are
# stage- and interaction-dependent), so they are not re-read from the glb; the
# material factors written below record them honestly all the same.
FLOOR_Y: float = -25.3
DEFAULT_LIGHT_AZ_DEG: float = 60.0
DEFAULT_LIGHT_EL_DEG: float = 30.0

# The four textures demo22 binds, by the name they are stored under in the
# glb.  demo22b looks them up by these names (not by material), because the
# cube is one 36-vertex primitive textured across three images by an app-side
# offset table -- parity-first keeps that table in the app (see demo22b).
_TEXTURE_FILES: tuple[tuple[str, str], ...] = (
    ("floor", "floor.tga"),
    ("Block4", "Block4.tga"),
    ("Block5", "Block5.tga"),
    ("Block6", "Block6.tga"),
)


# ---------------------------------------------------------------------------
# Geometry builders -- copied verbatim from demo22's _build_* (the parity
# source of truth).  They must stay identical to demo22's: the round-trip is
# only "the same pixels" because these produce the same vertices.  If demo22's
# geometry ever changes, change it here too (tests/test_demo22b_gltf_roundtrip
# only proves the glb round-trips what it is given, not that it matches
# demo22).
# ---------------------------------------------------------------------------


def build_cube_solid() -> np.ndarray:
    s: float = 25.0
    faces: list[tuple[Any, ...]] = [
        # +Z
        (
            [(-s, -s, +s), (+s, -s, +s), (+s, +s, +s), (-s, +s, +s)],
            (0.0, 0.0, 1.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # -Z
        (
            [(+s, -s, -s), (-s, -s, -s), (-s, +s, -s), (+s, +s, -s)],
            (0.0, 0.0, -1.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # +Y
        (
            [(-s, +s, +s), (+s, +s, +s), (+s, +s, -s), (-s, +s, -s)],
            (0.0, 1.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # -Y
        (
            [(-s, -s, -s), (+s, -s, -s), (+s, -s, +s), (-s, -s, +s)],
            (0.0, -1.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # +X
        (
            [(+s, -s, +s), (+s, -s, -s), (+s, +s, -s), (+s, +s, +s)],
            (1.0, 0.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # -X
        (
            [(-s, -s, -s), (-s, -s, +s), (-s, +s, +s), (-s, +s, -s)],
            (-1.0, 0.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
    ]

    out: list[float] = []
    for corners, normal, uvs in faces:
        for i in (0, 1, 2, 0, 2, 3):
            out.extend(corners[i])
            out.extend(normal)
            out.extend(uvs[i])
    return np.array(out, dtype=np.float32)


def build_cube_wire_full() -> np.ndarray:
    s: float = 25.0
    corners: list[tuple[float, float, float]] = [
        (-s, -s, -s),
        (+s, -s, -s),
        (+s, +s, -s),
        (-s, +s, -s),  # back face
        (-s, -s, +s),
        (+s, -s, +s),
        (+s, +s, +s),
        (-s, +s, +s),  # front face
    ]
    edges: list[tuple[int, int]] = [
        # back face
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        # front face
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        # connecting edges
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]
    out: list[float] = []
    for a, b in edges:
        for ci in (a, b):
            out.extend(corners[ci])
            out.extend((0.0, 0.0, 0.0))  # unused normal
            out.extend((0.0, 0.0))  # unused uv
    return np.array(out, dtype=np.float32)


def build_floor() -> np.ndarray:
    e: float = 100.0
    y: float = FLOOR_Y
    corners: list[tuple[float, float, float]] = [
        (-e, y, -e),
        (-e, y, +e),
        (+e, y, +e),
        (+e, y, -e),
    ]
    uvs: list[tuple[float, float]] = [
        (0.0, 0.0),
        (0.0, 1.0),
        (1.0, 1.0),
        (1.0, 0.0),
    ]
    n: tuple[float, float, float] = (0.0, 1.0, 0.0)
    out: list[float] = []
    for i in (0, 1, 2, 0, 2, 3):
        out.extend(corners[i])
        out.extend(n)
        out.extend(uvs[i])
    return np.array(out, dtype=np.float32)


def build_marker_cone(radius: float, height: float, slices: int) -> np.ndarray:
    out: list[float] = []
    base_pts: list[tuple[float, float, float]] = []
    for i in range(slices + 1):
        t: float = i / slices * 2.0 * math.pi
        base_pts.append((radius * math.cos(t), radius * math.sin(t), 0.0))
    apex: tuple[float, float, float] = (0.0, 0.0, height)
    base_center: tuple[float, float, float] = (0.0, 0.0, 0.0)
    for i in range(slices):
        for v in (apex, base_pts[i], base_pts[i + 1]):
            out.extend(v)
            out.extend((0.0, 0.0, 0.0))
            out.extend((0.0, 0.0))
    for i in range(slices):
        for v in (base_center, base_pts[i + 1], base_pts[i]):
            out.extend(v)
            out.extend((0.0, 0.0, 0.0))
            out.extend((0.0, 0.0))
    return np.array(out, dtype=np.float32)


def build_marker_sphere(radius: float, slices: int, stacks: int) -> np.ndarray:
    out: list[float] = []
    for i in range(stacks):
        phi0: float = math.pi * (i / stacks) - math.pi / 2.0
        phi1: float = math.pi * ((i + 1) / stacks) - math.pi / 2.0
        cphi0, sphi0 = math.cos(phi0), math.sin(phi0)
        cphi1, sphi1 = math.cos(phi1), math.sin(phi1)
        for j in range(slices):
            t0: float = 2.0 * math.pi * (j / slices)
            t1: float = 2.0 * math.pi * ((j + 1) / slices)
            ct0, st0 = math.cos(t0), math.sin(t0)
            ct1, st1 = math.cos(t1), math.sin(t1)
            p00: tuple[float, float, float] = (cphi0 * st0, sphi0, cphi0 * ct0)
            p10: tuple[float, float, float] = (cphi0 * st1, sphi0, cphi0 * ct1)
            p01: tuple[float, float, float] = (cphi1 * st0, sphi1, cphi1 * ct0)
            p11: tuple[float, float, float] = (cphi1 * st1, sphi1, cphi1 * ct1)
            for v in (p00, p10, p01, p10, p11, p01):
                out.extend(p * radius for p in v)
                out.extend((0.0, 0.0, 0.0))
                out.extend((0.0, 0.0))
    return np.array(out, dtype=np.float32)


# ---------------------------------------------------------------------------
# Scene description -- the ordered list that both the writer and the reader
# agree on.  The marker meshes match demo22's _build_marker_* call arguments.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MeshSpec:
    """One drawable mesh: its name, GL draw mode, and interleaved vertices."""

    name: str
    mode: int  # MODE_TRIANGLES or MODE_LINES
    vertex_data: np.ndarray  # (vertex_count * 8,) float32, demo22 layout
    # The honest base colour for this mesh (written as the material's
    # baseColorFactor).  demo22's per-stage colours are app state, so demo22b
    # does not read this back; it is here so the glb is a complete asset.
    base_color: tuple[float, float, float, float]
    unlit: bool  # KHR_materials_unlit material (the wireframe + marker)


def scene_meshes() -> list[MeshSpec]:
    """The five demo22 meshes, in the fixed order the glb stores them in."""
    return [
        MeshSpec(
            name="cube_solid",
            mode=MODE_TRIANGLES,
            vertex_data=build_cube_solid(),
            base_color=(0.8, 0.0, 0.0, 1.0),
            unlit=False,
        ),
        MeshSpec(
            name="cube_wire",
            mode=MODE_LINES,
            vertex_data=build_cube_wire_full(),
            base_color=(1.0, 0.0, 0.0, 1.0),
            unlit=True,
        ),
        MeshSpec(
            name="floor",
            mode=MODE_TRIANGLES,
            vertex_data=build_floor(),
            base_color=(0.0, 0.0, 0.9, 1.0),
            unlit=False,
        ),
        MeshSpec(
            name="marker_cone",
            mode=MODE_TRIANGLES,
            vertex_data=build_marker_cone(radius=5.0, height=12.0, slices=20),
            base_color=(0.85, 0.15, 0.15, 1.0),
            unlit=True,
        ),
        MeshSpec(
            name="marker_bulb",
            mode=MODE_TRIANGLES,
            vertex_data=build_marker_sphere(radius=4.0, slices=16, stacks=10),
            base_color=(1.0, 1.0, 0.0, 1.0),
            unlit=True,
        ),
    ]


def _light_direction(az_deg: float, el_deg: float) -> np.ndarray:
    """Unit direction *toward* the light (mirrors util.shading.light_dir_ws).

    Inlined so this module depends only on numpy/pygltflib/imageio.  Azimuth
    sweeps x -> z, elevation lifts toward +y.
    """
    az: float = math.radians(az_deg)
    el: float = math.radians(el_deg)
    return np.array(
        [
            math.cos(el) * math.cos(az),
            math.sin(el),
            math.cos(el) * math.sin(az),
        ],
        dtype=np.float32,
    )


def _light_node_matrix(direction: np.ndarray) -> list[float]:
    """A node matrix whose +Z axis is ``direction`` (column-major 16-tuple).

    glTF directional lights shine along the node's local -Z, so a light that
    shines *from* ``direction`` (demo22's "direction toward the light") has
    the node's +Z pointing that way.  An orthonormal basis is built with Z =
    direction; reading the +Z column back recovers the direction exactly.
    """
    z: np.ndarray = direction / np.linalg.norm(direction)
    up: np.ndarray = (
        np.array([0.0, 1.0, 0.0], dtype=np.float32)
        if abs(float(z[1])) < 0.9999
        else np.array([0.0, 0.0, 1.0], dtype=np.float32)
    )
    x: np.ndarray = np.cross(up, z)
    x = x / np.linalg.norm(x)
    y: np.ndarray = np.cross(z, x)
    matrix: np.ndarray = np.identity(4, dtype=np.float32)
    matrix[:3, 0] = x
    matrix[:3, 1] = y
    matrix[:3, 2] = z
    # glTF matrices are column-major 16-tuples.
    return [float(v) for v in matrix.flatten(order="F")]


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------


class _BufferBuilder:
    """Accumulates the glb binary buffer, 4-byte aligning each segment."""

    def __init__(self) -> None:
        self._chunks: list[bytes] = []
        self._offset: int = 0

    def add(self, data: bytes) -> tuple[int, int]:
        """Pad to a 4-byte boundary, append ``data``; return offset, length."""
        pad: int = (-self._offset) % 4
        if pad:
            self._chunks.append(b"\x00" * pad)
            self._offset += pad
        start: int = self._offset
        self._chunks.append(data)
        self._offset += len(data)
        return start, len(data)

    def blob(self) -> bytes:
        return b"".join(self._chunks)


def _png_bytes(pixels: np.ndarray) -> bytes:
    """Encode an image array as PNG bytes (lossless, so pixels survive)."""
    return bytes(iio.imwrite("<bytes>", pixels, extension=".png"))


def _demo22_texture_dir() -> Path:
    """demo22's directory, the source of the four ``.tga`` textures."""
    return Path(__file__).resolve().parent.parent / "demo22"


def write_glb(
    path: str | Path,
    *,
    az_deg: float = DEFAULT_LIGHT_AZ_DEG,
    el_deg: float = DEFAULT_LIGHT_EL_DEG,
) -> None:
    """Build the demo22 scene and write it to ``path`` as a ``.glb``.

    The glb carries the five meshes, the four textures (PNG-encoded from
    demo22's ``.tga`` files, embedded) and a KHR_lights_punctual directional
    light at ``az_deg`` / ``el_deg``.  glTF only permits PNG/JPEG images, so
    the TGA textures are converted; the conversion is lossless.
    """
    meshes: list[MeshSpec] = scene_meshes()
    buffer: _BufferBuilder = _BufferBuilder()

    accessors: list[Accessor] = []
    buffer_views: list[BufferView] = []
    gltf_meshes: list[Mesh] = []
    materials: list[Material] = []

    def add_stream(values: np.ndarray, kind: str, want_bounds: bool) -> int:
        """Add a vertex stream as a bufferView + accessor; return its index."""
        packed: np.ndarray = np.ascontiguousarray(values, dtype="<f4")
        offset, length = buffer.add(packed.tobytes())
        buffer_views.append(
            BufferView(
                buffer=0,
                byteOffset=offset,
                byteLength=length,
                target=ARRAY_BUFFER,
            )
        )
        accessor: Accessor = Accessor(
            bufferView=len(buffer_views) - 1,
            componentType=FLOAT,
            count=int(values.shape[0]),
            type=kind,
        )
        if want_bounds:
            accessor.min = [float(v) for v in values.min(axis=0)]
            accessor.max = [float(v) for v in values.max(axis=0)]
        accessors.append(accessor)
        return len(accessors) - 1

    for index, spec in enumerate(meshes):
        rows: np.ndarray = spec.vertex_data.reshape(-1, FLOATS_PER_VERTEX)
        positions: np.ndarray = rows[:, 0:3]
        normals: np.ndarray = rows[:, 3:6]
        texcoords: np.ndarray = rows[:, 6:8]
        pos_accessor: int = add_stream(positions, VEC3, want_bounds=True)
        nrm_accessor: int = add_stream(normals, VEC3, want_bounds=False)
        uv_accessor: int = add_stream(texcoords, VEC2, want_bounds=False)
        gltf_meshes.append(
            Mesh(
                name=spec.name,
                primitives=[
                    Primitive(
                        attributes=Attributes(
                            POSITION=pos_accessor,
                            NORMAL=nrm_accessor,
                            TEXCOORD_0=uv_accessor,
                        ),
                        material=index,
                        mode=spec.mode,
                    )
                ],
            )
        )
        material: Material = Material(
            name=spec.name,
            pbrMetallicRoughness=PbrMetallicRoughness(
                baseColorFactor=list(spec.base_color),
                metallicFactor=0.0,
                roughnessFactor=1.0,
            ),
        )
        if spec.unlit:
            material.extensions = {"KHR_materials_unlit": {}}
        materials.append(material)

    # Textures: convert demo22's TGA files to embedded PNG images.  The cube
    # and floor materials reference Block4 / floor so those two are "used";
    # Block5 and Block6 are carried for demo22b to load by name (the cube's
    # per-face texturing is an app-side offset table, not glTF material state,
    # so one primitive cannot reference all three block textures -- see the
    # demo22b task doc).  glTF-Validator reports the two as UNUSED_OBJECT
    # (INFO severity, still spec-conformant).
    images: list[Image] = []
    textures: list[Texture] = []
    texture_dir: Path = _demo22_texture_dir()
    for name, filename in _TEXTURE_FILES:
        pixels: np.ndarray = np.asarray(iio.imread(texture_dir / filename))
        offset, length = buffer.add(_png_bytes(pixels))
        buffer_views.append(
            BufferView(buffer=0, byteOffset=offset, byteLength=length)
        )
        images.append(
            Image(
                name=name,
                mimeType="image/png",
                bufferView=len(buffer_views) - 1,
            )
        )
        textures.append(Texture(name=name, source=len(images) - 1, sampler=0))

    image_index: dict[str, int] = {
        name: i for i, (name, _) in enumerate(_TEXTURE_FILES)
    }
    # The cube (Block4, representative) and floor materials reference a
    # texture; every material above was built with a pbrMetallicRoughness, so
    # the guards only reassure the type checker.
    cube_pbr: PbrMetallicRoughness | None = materials[0].pbrMetallicRoughness
    floor_pbr: PbrMetallicRoughness | None = materials[2].pbrMetallicRoughness
    if cube_pbr is not None:
        cube_pbr.baseColorTexture = TextureInfo(index=image_index["Block4"])
    if floor_pbr is not None:
        floor_pbr.baseColorTexture = TextureInfo(index=image_index["floor"])

    # Nodes: one per mesh (identity transform -- demo22 keeps the cube's
    # translate(-10, 0, 10) in app code, so baking it here too would
    # double-apply it), plus the light node carrying the direction.
    nodes: list[Node] = [
        Node(name=spec.name, mesh=i) for i, spec in enumerate(meshes)
    ]
    light_direction: np.ndarray = _light_direction(az_deg, el_deg)
    light_node: Node = Node(
        name="light",
        matrix=_light_node_matrix(light_direction),
        extensions={"KHR_lights_punctual": {"light": 0}},
    )
    nodes.append(light_node)

    gltf: GLTF2 = GLTF2(
        asset=Asset(
            version="2.0", generator="modelviewprojection demo22b export_scene"
        ),
        scene=0,
        scenes=[Scene(name="demo22", nodes=list(range(len(nodes))))],
        nodes=nodes,
        meshes=gltf_meshes,
        accessors=accessors,
        bufferViews=buffer_views,
        buffers=[Buffer(byteLength=0)],
        materials=materials,
        images=images,
        textures=textures,
        samplers=[
            Sampler(
                magFilter=_LINEAR,
                minFilter=_LINEAR,
                wrapS=_REPEAT,
                wrapT=_REPEAT,
            )
        ],
        extensionsUsed=["KHR_lights_punctual", "KHR_materials_unlit"],
        extensions={
            "KHR_lights_punctual": {
                "lights": [
                    {
                        "type": "directional",
                        "color": [1.0, 1.0, 1.0],
                        "intensity": 1.0,
                        "name": "sun",
                    }
                ]
            }
        },
    )
    blob: bytes = buffer.blob()
    gltf.buffers[0].byteLength = len(blob)
    gltf.set_binary_blob(blob)
    gltf.save_binary(str(path))


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LoadedScene:
    """What :func:`read_glb` decodes back out of the ``.glb``."""

    # mesh name -> (GL draw mode, interleaved float32 vertex array)
    meshes: dict[str, tuple[int, np.ndarray]] = field(default_factory=dict)
    # image name -> HxWx(3|4) uint8 pixels
    images: dict[str, np.ndarray] = field(default_factory=dict)
    light_az_deg: float = DEFAULT_LIGHT_AZ_DEG
    light_el_deg: float = DEFAULT_LIGHT_EL_DEG


def _decode_accessor(
    gltf: GLTF2, blob: bytes, accessor_index: int
) -> np.ndarray:
    """Decode a FLOAT accessor into a ``(count, ncomp)`` float32 array.

    Honours the bufferView byteStride and the accessor byteOffset, so it reads
    both tightly packed and interleaved data (this writer packs tightly).
    """
    accessor: Any = gltf.accessors[accessor_index]
    ncomp: int = _TYPE_COUNT[accessor.type]
    view: Any = gltf.bufferViews[accessor.bufferView]
    dtype: np.dtype = np.dtype("<f4")
    start: int = (view.byteOffset or 0) + (accessor.byteOffset or 0)
    stride: int = view.byteStride or (dtype.itemsize * ncomp)
    if stride == dtype.itemsize * ncomp:
        flat: np.ndarray = np.frombuffer(
            blob, dtype=dtype, count=accessor.count * ncomp, offset=start
        )
        return flat.reshape(accessor.count, ncomp).astype(np.float32)
    rows: list[np.ndarray] = [
        np.frombuffer(blob, dtype=dtype, count=ncomp, offset=start + i * stride)
        for i in range(accessor.count)
    ]
    return np.vstack(rows).astype(np.float32)


def _direction_to_az_el(direction: np.ndarray) -> tuple[float, float]:
    """Inverse of :func:`_light_direction`: a unit direction -> (az, el) deg."""
    x, y, z = (float(c) for c in direction)
    elevation: float = math.degrees(math.asin(max(-1.0, min(1.0, y))))
    azimuth: float = math.degrees(math.atan2(z, x)) % 360.0
    return azimuth, elevation


def read_glb(path: str | Path) -> LoadedScene:
    """Load a ``.glb`` written by :func:`write_glb` back into a LoadedScene."""
    gltf: GLTF2 = GLTF2().load(str(path))
    blob: bytes = gltf.binary_blob()

    meshes: dict[str, tuple[int, np.ndarray]] = {}
    for mesh_index, mesh in enumerate(gltf.meshes):
        mesh_name: str = mesh.name or f"mesh_{mesh_index}"
        primitive: Any = mesh.primitives[0]
        positions: np.ndarray = _decode_accessor(
            gltf, blob, primitive.attributes.POSITION
        )
        normals: np.ndarray = _decode_accessor(
            gltf, blob, primitive.attributes.NORMAL
        )
        texcoords: np.ndarray = _decode_accessor(
            gltf, blob, primitive.attributes.TEXCOORD_0
        )
        interleaved: np.ndarray = (
            np.hstack([positions, normals, texcoords])
            .astype(np.float32)
            .reshape(-1)
        )
        mode: int = (
            primitive.mode if primitive.mode is not None else MODE_TRIANGLES
        )
        meshes[mesh_name] = (mode, interleaved)

    images: dict[str, np.ndarray] = {}
    for image_index, image in enumerate(gltf.images):
        image_name: str = image.name or f"image_{image_index}"
        view: Any = gltf.bufferViews[image.bufferView]
        start: int = view.byteOffset or 0
        png: bytes = blob[start : start + view.byteLength]
        images[image_name] = np.asarray(iio.imread(png, extension=".png"))

    light_az: float = DEFAULT_LIGHT_AZ_DEG
    light_el: float = DEFAULT_LIGHT_EL_DEG
    for node in gltf.nodes:
        if node.name == "light" and node.matrix is not None:
            matrix: np.ndarray = np.array(
                node.matrix, dtype=np.float32
            ).reshape(4, 4, order="F")
            light_az, light_el = _direction_to_az_el(matrix[:3, 2])
            break

    return LoadedScene(
        meshes=meshes,
        images=images,
        light_az_deg=light_az,
        light_el_deg=light_el,
    )


def _summarize(path: str) -> None:
    """Write the scene to ``path`` and print what round-trips back (no GL)."""
    write_glb(path)
    loaded: LoadedScene = read_glb(path)
    print(f"wrote {path}")
    for name, (mode, data) in loaded.meshes.items():
        kind: str = "LINES" if mode == MODE_LINES else "TRIANGLES"
        verts: int = data.size // FLOATS_PER_VERTEX
        print(f"  mesh {name:<12} {kind:<10} {verts:>5} verts")
    for name, pixels in loaded.images.items():
        print(f"  image {name:<8} {pixels.shape}")
    print(
        f"  light az {loaded.light_az_deg:.2f} deg  el "
        f"{loaded.light_el_deg:.2f} deg"
    )


if __name__ == "__main__":
    import sys

    _summarize(sys.argv[1] if len(sys.argv) > 1 else "scene.glb")
