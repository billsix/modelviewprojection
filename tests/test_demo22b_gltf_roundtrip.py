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

"""Headless proof that demo22b's glTF round-trip is lossless (no GPU needed).

demo22b draws the demo22 scene after writing it to a ``.glb`` and reading it
back.  The claim "same pixels as demo22" rests on the data surviving that
round-trip byte-for-byte; this test proves exactly that part -- the geometry,
the textures and the light -- without a display.  demo22b's render loop
(shaders, shadow algorithms, stages) is demo22's unchanged, so it is out of
scope here and is what the maintainer verifies on-screen.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import imageio.v3 as iio
import numpy as np
import pytest

# export_scene lives in the demo22b directory, which is not a package (demos
# are run by path).  Put that directory on sys.path, exactly as running
# demo22b.py by path would, then import it.
_DEMO22B_DIR: Path = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "modelviewprojection"
    / "demos"
    / "demo22b"
)
sys.path.insert(0, str(_DEMO22B_DIR))

import export_scene as es  # ty: ignore[unresolved-import]  # noqa: E402

_DEMO22_DIR: Path = _DEMO22B_DIR.parent / "demo22"


def _builder_outputs() -> dict[str, tuple[int, np.ndarray]]:
    """The five meshes straight from the builders (the parity reference)."""
    return {
        "cube_solid": (es.MODE_TRIANGLES, es.build_cube_solid()),
        "cube_wire": (es.MODE_LINES, es.build_cube_wire_full()),
        "floor": (es.MODE_TRIANGLES, es.build_floor()),
        "marker_cone": (
            es.MODE_TRIANGLES,
            es.build_marker_cone(radius=5.0, height=12.0, slices=20),
        ),
        "marker_bulb": (
            es.MODE_TRIANGLES,
            es.build_marker_sphere(radius=4.0, slices=16, stacks=10),
        ),
    }


def test_geometry_round_trips_byte_identical(tmp_path: Path) -> None:
    glb: Path = tmp_path / "scene.glb"
    es.write_glb(glb)
    loaded: Any = es.read_glb(glb)
    expected: dict[str, tuple[int, np.ndarray]] = _builder_outputs()
    assert set(loaded.meshes) == set(expected)
    for name, (mode, vertices) in expected.items():
        got_mode: int
        got_vertices: np.ndarray
        got_mode, got_vertices = loaded.meshes[name]
        assert got_mode == mode, f"{name}: draw mode changed"
        assert got_vertices.dtype == np.float32
        assert np.array_equal(got_vertices, vertices), (
            f"{name}: decoded vertices are not byte-identical"
        )


def test_textures_round_trip_pixel_identical(tmp_path: Path) -> None:
    glb: Path = tmp_path / "scene.glb"
    es.write_glb(glb)
    loaded: Any = es.read_glb(glb)
    for name, filename in es._TEXTURE_FILES:
        source: np.ndarray = np.asarray(iio.imread(_DEMO22_DIR / filename))
        decoded: np.ndarray = loaded.images[name]
        assert decoded.shape[:2] == source.shape[:2]
        # demo22 uploads RGB8; compare the three colour channels that survive
        # the documented TGA -> PNG conversion.
        source_rgb: np.ndarray = (
            source[..., :3]
            if source.ndim == 3
            else np.stack([source] * 3, axis=-1)
        )
        decoded_rgb: np.ndarray = (
            decoded[..., :3]
            if decoded.ndim == 3
            else np.stack([decoded] * 3, axis=-1)
        )
        assert np.array_equal(decoded_rgb, source_rgb), (
            f"{name}: pixels differ after the PNG round-trip"
        )


def test_light_defaults_round_trip(tmp_path: Path) -> None:
    glb: Path = tmp_path / "scene.glb"
    es.write_glb(glb)
    loaded: Any = es.read_glb(glb)
    assert loaded.light_az_deg == pytest.approx(
        es.DEFAULT_LIGHT_AZ_DEG, abs=1e-3
    )
    assert loaded.light_el_deg == pytest.approx(
        es.DEFAULT_LIGHT_EL_DEG, abs=1e-3
    )


@pytest.mark.parametrize(
    ("az_deg", "el_deg"),
    [(129.0, 43.0), (10.0, 80.0), (300.0, 15.0), (0.0, 5.0)],
)
def test_light_round_trips_at_several_angles(
    tmp_path: Path, az_deg: float, el_deg: float
) -> None:
    glb: Path = tmp_path / "scene.glb"
    es.write_glb(glb, az_deg=az_deg, el_deg=el_deg)
    loaded: Any = es.read_glb(glb)
    assert loaded.light_az_deg == pytest.approx(az_deg, abs=1e-2)
    assert loaded.light_el_deg == pytest.approx(el_deg, abs=1e-2)


def test_written_glb_reloads_as_valid_gltf(tmp_path: Path) -> None:
    """pygltflib reloading the file is a basic spec-conformance check."""
    from pygltflib import GLTF2

    glb: Path = tmp_path / "scene.glb"
    es.write_glb(glb)
    reloaded: Any = GLTF2().load(str(glb))
    assert reloaded.asset.version == "2.0"
    assert len(reloaded.meshes) == 5
    assert len(reloaded.images) == 4
    assert "KHR_lights_punctual" in reloaded.extensionsUsed
