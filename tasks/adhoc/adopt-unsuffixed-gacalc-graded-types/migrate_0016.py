#!/usr/bin/env python
"""Codemod: adopt gacalc 0.0.16's unsuffixed graded types across mvp's .py code.

gacalc 0.0.16 dropped the dimension suffix from its generated types
(``Vector2``/``Vector3`` -> ``Vector``, ``Bivector3`` -> ``Bivector``, ...) and moved the
dimension into the *module* -- so imports become module-qualified. mvp adopts the
**direct-import / module-qualify** approach (no aliasing): a file that touches a single
dimension imports the bare ``Vector`` from that dimension's module; a file that mixes
dimensions (the name would clash) imports the modules and qualifies each use.

Three file groups, each a literal list below (from the 2026-08-13 dimension-mix scan):

- DIRECT_FROM_GACALC -- single-dimension files that already ``from gacalc.gN import VectorN``.
  Drop the suffix everywhere (import line + body): VectorN -> Vector, BivectorN -> Bivector,
  etc.  No clash: only one dimension is present.

- FACADE_PORTS -- the 12 OpenGL-SuperBible ports that pull ``Vector3`` through mvp's
  ``mathutils`` facade (``from modelviewprojection.mathutils import Vector3, <helper>``).
  Split that import: source ``Vector`` straight from ``gacalc.g3`` and keep only the real
  mathutils helper on the original line.  This finishes the de-facade
  (tasks/defacade-mathutils-gacalc-reexports.md).  Then drop the suffix in the body.

- QUALIFY -- files that mix >1 dimension, so a bare ``Vector`` would collide.  Rewrite each
  ``from gacalc.gN import VectorN`` to ``import gacalc.gN as gN`` and prefix every use:
  Vector2 -> g2.Vector, Vector3 -> g3.Vector, Bivector3 -> g3.Bivector, Vector1 -> g1.Vector.

``mathutils.py`` is a QUALIFY file too, but it ALSO carries executed doctests whose imports
use the direct form and whose expected output shows the module-qualified repr -- it is
migrated **by hand**, not here (deliberately absent from QUALIFY below).

Run from the repo root:
    python tasks/adhoc/adopt-unsuffixed-gacalc-graded-types/migrate_0016.py [--dry-run]

If the script needs changing mid-task: ``git checkout`` the touched files, edit the script,
and re-run the FINAL script once (per the adhoc-script convention) so it faithfully
reproduces its own diff.
"""

from __future__ import annotations

import pathlib
import re
import sys

# --- the suffix-drop map, applied as whole-word substitutions -----------------------------
# every graded type mvp could touch -> its unsuffixed 0.0.16 name.
_SUFFIX_DROP: dict[str, str] = {
    "Vector1": "Vector", "Vector2": "Vector", "Vector3": "Vector",
    "Bivector1": "Bivector", "Bivector2": "Bivector", "Bivector3": "Bivector",
    "Trivector3": "Trivector",
    "Rotor2": "Rotor", "Rotor3": "Rotor",
}
_SUFFIXED = re.compile(r"\b(" + "|".join(_SUFFIX_DROP) + r")\b")


def _drop_suffix(text: str) -> str:
    """VectorN -> Vector, BivectorN -> Bivector, ... everywhere in ``text``."""
    return _SUFFIXED.sub(lambda m: _SUFFIX_DROP[m.group(1)], text)


# --- DIRECT_FROM_GACALC: single-dimension files importing straight from gacalc.gN ---------
DIRECT_FROM_GACALC: list[str] = [
    # ctc games (all g2)
    "ports/codetheclassics/vol1/boing/boing.py",
    "ports/codetheclassics/vol1/cavern/cavern.py",
    "ports/codetheclassics/vol1/myriapod/myriapod.py",
    "ports/codetheclassics/vol1/soccer/soccer.py",
    "ports/codetheclassics/vol2/avenger/avenger.py",
    "ports/codetheclassics/vol2/beatstreets/beatstreets.py",
    "ports/codetheclassics/vol2/eggzy/eggzy.py",
    "ports/codetheclassics/vol2/kinetix/kinetix.py",
    # demos 05-13 (g2), 14-18 (g3)
    "src/modelviewprojection/demos/demo05.py",
    "src/modelviewprojection/demos/demo06.py",
    "src/modelviewprojection/demos/demo07.py",
    "src/modelviewprojection/demos/demo08.py",
    "src/modelviewprojection/demos/demo09.py",
    "src/modelviewprojection/demos/demo10.py",
    "src/modelviewprojection/demos/demo11.py",
    "src/modelviewprojection/demos/demo12.py",
    "src/modelviewprojection/demos/demo13.py",
    "src/modelviewprojection/demos/demo14.py",
    "src/modelviewprojection/demos/demo15.py",
    "src/modelviewprojection/demos/demo16.py",
    "src/modelviewprojection/demos/demo17.py",
    "src/modelviewprojection/demos/demo18.py",
    # single-dimension src modules
    "src/modelviewprojection/cayley/cayleyscene.py",
    "src/modelviewprojection/framebuffer/softwarerendering.py",
    "src/modelviewprojection/notebooksrc/ndc.py",
    "src/modelviewprojection/pgzero_gl/_types.py",
    "src/modelviewprojection/pgzero_gl/actor.py",
    "src/modelviewprojection/pgzero_gl/screen.py",
    "src/modelviewprojection/plotsforbook/generate_plots.py",
    "src/modelviewprojection/util/nbplotutils.py",
    "src/modelviewprojection/util/shading.py",
    "src/modelviewprojection/mvpvisualization/coordinatesystems.py",
    "src/modelviewprojection/mvpvisualization/model.py",
    "src/modelviewprojection/mvpvisualization/modelview.py",
    "src/modelviewprojection/mvpvisualization/modelview2d.py",
    "src/modelviewprojection/mvpvisualization/modelvieworthoprojection.py",
    "src/modelviewprojection/mvpvisualization/modelviewperspectiveprojection.py",
    "src/modelviewprojection/mvpvisualization/pushmatrix.py",
    # tests (single-dimension)
    "tests/test_cayley_graph.py",
    "tests/test_cayley_scene.py",
    "tests/test_focus_to_matrix.py",
]

# --- FACADE_PORTS: 12 SuperBible ports pulling Vector3 through mathutils -------------------
FACADE_PORTS: list[str] = [
    "ports/openglsuperbiblev4/chapt01/block/Block.py",
    "ports/openglsuperbiblev4/chapt05/litjet/litjet.py",
    "ports/openglsuperbiblev4/chapt05/shadow/shadow.py",
    "ports/openglsuperbiblev4/chapt05/shinyjet/shinyjet.py",
    "ports/openglsuperbiblev4/chapt05/sphereworld/sphereworld.py",
    "ports/openglsuperbiblev4/chapt06/fogged/fogged.py",
    "ports/openglsuperbiblev4/chapt06/multisample/multisample.py",
    "ports/openglsuperbiblev4/chapt06/sphereworld/sphereworld.py",
    "ports/openglsuperbiblev4/chapt08/pyramid/pyramid.py",
    "ports/openglsuperbiblev4/chapt08/sphereworld/sphereworld.py",
    "ports/openglsuperbiblev4/chapt09/sphereworld/sphereworld.py",
    "ports/openglsuperbiblev4/chapt11/sphereworld/sphereworld.py",
    "ports/openglsuperbiblev4/chapt19/SphereWorld32/SphereWorld32.py",
]

# --- QUALIFY: multi-dimension files (mathutils.py excluded -- hand-migrated) ---------------
# each entry maps its needed dimensions to the module alias.
QUALIFY: list[str] = [
    "ports/codetheclassics/vol2/leadingedge/leadingedge.py",  # g2 + g3
    "src/modelviewprojection/notebooksrc/plot2d.py",           # g1 + g2 + g3
    "tests/test_gl_vector_unpacking.py",                       # g2 + g3
    "tests/test_mathutils.py",                                 # g2 + g3
]

# in QUALIFY mode the suffixed name maps to the module-qualified unsuffixed name.
_QUALIFY_MAP: dict[str, str] = {
    "Vector1": "g1.Vector", "Vector2": "g2.Vector", "Vector3": "g3.Vector",
    "Bivector3": "g3.Bivector",
}
_QUALIFY_NAME = re.compile(r"\b(" + "|".join(_QUALIFY_MAP) + r")\b")

# `from gacalc.gN import <names>` -> `import gacalc.gN as gN` (drops the whole import list;
# the QUALIFY files import only VectorN/BivectorN from these modules -- verified, no
# constants -- so nothing is lost).
_GACALC_FROM_IMPORT = re.compile(r"^(\s*)from gacalc\.(g[123]) import .*$", re.MULTILINE)


def _split_facade_import(text: str) -> str:
    """In a SuperBible port, move ``Vector3`` off the mathutils import onto a gacalc one.

    Handles both the single-line form and the parenthesised multi-line form.  The gacalc
    import is inserted just before the mathutils line so import order stays alphabetical-ish
    (``gacalc`` < ``modelviewprojection``); ruff's isort pass fixes any residue anyway.
    """
    # single-line: from modelviewprojection.mathutils import Vector3, helper[, ...]
    def _single(m: re.Match[str]) -> str:
        indent, names = m.group(1), [n.strip() for n in m.group(2).split(",")]
        if "Vector3" not in names:  # nothing to split off -> leave the line untouched
            return m.group(0)
        kept = [n for n in names if n != "Vector3"]
        gacalc = f"{indent}from gacalc.g3 import Vector\n"
        if kept:
            return gacalc + f"{indent}from modelviewprojection.mathutils import {', '.join(kept)}"
        return gacalc.rstrip("\n")

    text = re.sub(
        r"^(\s*)from modelviewprojection\.mathutils import ([^\n(]+)$",
        _single,
        text,
        flags=re.MULTILINE,
    )

    # multi-line: from modelviewprojection.mathutils import (\n Vector3,\n helper,\n)
    def _multi(m: re.Match[str]) -> str:
        indent, body = m.group(1), m.group(2)
        names = [n.strip() for n in body.replace("\n", "").split(",") if n.strip()]
        if "Vector3" not in names:  # nothing to split off -> leave the block untouched
            return m.group(0)
        kept = [n for n in names if n != "Vector3"]
        gacalc = f"{indent}from gacalc.g3 import Vector\n"
        if kept:
            inner = "".join(f"{indent}    {n},\n" for n in kept)
            return gacalc + f"{indent}from modelviewprojection.mathutils import (\n{inner}{indent})"
        return gacalc.rstrip("\n")

    text = re.sub(
        r"^(\s*)from modelviewprojection\.mathutils import \(\n((?:.*\n)*?)\s*\)$",
        _multi,
        text,
        flags=re.MULTILINE,
    )
    return text


def _qualify(text: str) -> str:
    """Rewrite gacalc from-imports to ``import gacalc.gN as gN`` and prefix every use."""
    text = _GACALC_FROM_IMPORT.sub(lambda m: f"{m.group(1)}import gacalc.{m.group(2)} as {m.group(2)}", text)
    text = _QUALIFY_NAME.sub(lambda m: _QUALIFY_MAP[m.group(1)], text)
    return text


def _apply(rel: str, fn) -> bool:
    path = pathlib.Path(rel)
    old = path.read_text()
    new = fn(old)
    if new != old:
        path.write_text(new)
    return new != old


def main(dry_run: bool) -> None:
    def report(rel: str, changed: bool) -> None:
        sys.stdout.write(f"{'changed ' if changed else 'no-op   '} {rel}\n")

    for rel in DIRECT_FROM_GACALC:
        report(rel, False if dry_run else _apply(rel, _drop_suffix))
    for rel in FACADE_PORTS:
        # split the facade import first, THEN drop the Vector3 suffix in the body.
        report(rel, False if dry_run else _apply(rel, lambda t: _drop_suffix(_split_facade_import(t))))
    for rel in QUALIFY:
        report(rel, False if dry_run else _apply(rel, _qualify))


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv[1:])
