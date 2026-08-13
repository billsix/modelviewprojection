#!/usr/bin/env python
"""Codemod: migrate mathutils.py to gacalc 0.0.16 (the one multi-dimension file with doctests).

mathutils.py mixes g2 + g3, so it module-qualifies (``g2.Vector`` / ``g3.Vector`` /
``g3.Bivector``).  Because ``import gacalc.g2 as g2`` / ``import gacalc.g3 as g3`` are module
globals, every doctest can reach them too -- so the whole file, code and doctests alike, uses
one uniform module-qualified idiom.  Three context-free passes (no docstring/doctest tracking):

1. Import EXAMPLE in prose (backtick-wrapped, ``from gacalc.g2 import Vector2``): suffix-drop
   the names only -> ``from gacalc.g2 import Vector``.  This is caller *guidance* (single-
   dimension callers use the direct import), so it must NOT become the ``import ... as`` form.

2. A real/doctest import STATEMENT of graded types (`from gacalc.gN import Vector3[, ...]`,
   possibly prefixed by ``>>> ``/``... ``): rewrite to ``import gacalc.gN as gN``.  Applies to
   the two module imports AND every ``>>> from gacalc.gN import VectorN`` doctest line, so each
   doctest becomes self-contained in the module-qualified idiom.

3. Every remaining suffixed graded name: qualify -- ``Vector2`` -> ``g2.Vector``,
   ``Vector3`` -> ``g3.Vector``, ``Bivector3`` -> ``g3.Bivector``.  This covers code, comments,
   docstring prose, doctest bodies (``Vector3.e_1`` -> ``g3.Vector.e_1``, resolved via the
   module global) AND doctest repr OUTPUT (``Vector3(coeff_e_1=...)`` -> ``g3.Vector(...)``,
   the 0.0.16 module-qualified repr) -- all with the same map, because the target is identical.

The doctest runner (`pytest --doctest-modules`) is the oracle: a wrong prefix or an unresolved
name fails there at the exact line.  Idempotent (no suffixed names / bare graded imports remain
on a second run).  Revert with `git checkout` and re-run once if it needs changing.
"""

from __future__ import annotations

import pathlib
import re

FILE = pathlib.Path("src/modelviewprojection/mathutils.py")

_QUALIFY = {"Vector2": "g2.Vector", "Vector3": "g3.Vector", "Bivector3": "g3.Bivector"}
_DROP = {"Vector2": "Vector", "Vector3": "Vector", "Bivector3": "Bivector"}

_GRADED = r"Vector[123]|Bivector[123]"

# pass 1 -- a backtick-preceded import example: drop the suffix off its names only
_EXAMPLE = re.compile(r"(?<=`)from gacalc\.(g[123]) import ([^`]+)")
# pass 2 -- a real/doctest import statement of graded types -> `import gacalc.gN as gN`
_STATEMENT = re.compile(
    rf"^(\s*(?:>>> |\.\.\. )?)from gacalc\.(g[123]) import (?:{_GRADED})(?:, ?(?:{_GRADED}))*\s*$",
    re.MULTILINE,
)
# pass 3 -- qualify any remaining suffixed graded name
_SUFFIXED = re.compile(rf"\b({_GRADED})\b")


def _drop_example(m: re.Match[str]) -> str:
    mod, names = m.group(1), [n.strip() for n in m.group(2).split(",")]
    return f"from gacalc.{mod} import " + ", ".join(_DROP.get(n, n) for n in names)


def transform(src: str) -> str:
    src = _EXAMPLE.sub(_drop_example, src)
    src = _STATEMENT.sub(lambda m: f"{m.group(1)}import gacalc.{m.group(2)} as {m.group(2)}", src)
    src = _SUFFIXED.sub(lambda m: _QUALIFY[m.group(1)], src)
    return src


if __name__ == "__main__":
    FILE.write_text(transform(FILE.read_text()))
    print(f"migrated {FILE}")
