#!/usr/bin/env python3
"""Rewrite the wrapped `f @ g` function compositions in the ten Code-the-Classics
GL 3.3 engines and demo07 as `compose([f, g])`.

House style (maintainer, 2026-09-06): `@` is for a composition that fits on one
line; once it wraps, `compose([...])` puts one function per line instead of the
dangling-operator layout the formatter produces.  Same order -- `compose([f, g])`
is f after g, exactly `f @ g` -- so the list is the operands verbatim.

Run from the repo root: `python tasks/adhoc/compose-for-wrapped-compositions/rewrite_wrapped_matmul.py`.
Idempotent: every pattern matches only the `@` form, so a second run reports 0
changes.  Also adds `compose` to each touched file's `from gacalc.transforms
import (...)` block when it is missing (ruff's isort pass orders it).
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
GAMES = sorted(ROOT.glob("ports/codetheclassics/vol*/*/*.py"))
DEMO07 = ROOT / "src/modelviewprojection/demos/demo07.py"

# (old, new) exact-text pairs.  The model-matrix template and the ortho matrix,
# identical in every engine; the two paddle transforms in demo07.
GAME_PAIRS: list[tuple[str, str]] = [
    (
        "    translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2)\n"
        "    @ scale_non_uniform(_W, _H, 1),\n",
        "    compose(\n"
        "        [\n"
        "            translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2),\n"
        "            scale_non_uniform(_W, _H, 1),\n"
        "        ]\n"
        "    ),\n",
    ),
    (
        "            translate(b=-1 * g3.Vector.e_1 + 1 * g3.Vector.e_2)\n"
        "            @ scale_non_uniform(2.0 / width, -2.0 / height, -1),\n",
        "            compose(\n"
        "                [\n"
        "                    translate(b=-1 * g3.Vector.e_1 + 1 * g3.Vector.e_2),\n"
        "                    scale_non_uniform(2.0 / width, -2.0 / height, -1),\n"
        "                ]\n"
        "            ),\n",
    ),
]
DEMO07_PAIRS: list[tuple[str, str]] = [
    (
        f"    p{n}_space_to_world_space = rotate(paddle{n}.rotation) @ translate(\n"
        f"        b=paddle{n}.position\n"
        f"    )\n",
        f"    p{n}_space_to_world_space = compose(\n"
        f"        [rotate(paddle{n}.rotation), translate(b=paddle{n}.position)]\n"
        f"    )\n",
    )
    for n in (1, 2)
]

# `from gacalc.transforms import (` block without `compose` -> insert it (ruff
# will sort the names).  A one-line import gets `compose` prepended the same way.
BLOCK_RE = re.compile(r"from gacalc\.transforms import \(\n(?P<names>(?:    [A-Za-z_]+,\n)+)\)\n")
LINE_RE = re.compile(r"from gacalc\.transforms import (?P<names>[A-Za-z_, ]+)\n")


def add_compose_import(src: str) -> str:
    m = BLOCK_RE.search(src)
    if m:
        if "    compose,\n" in m.group("names"):
            return src
        return src[: m.start("names")] + "    compose,\n" + src[m.start("names") :]
    m = LINE_RE.search(src)
    if m and "compose" not in m.group("names").split(", "):
        return src[: m.start("names")] + "compose, " + src[m.start("names") :]
    return src


def rewrite(path: pathlib.Path, pairs: list[tuple[str, str]]) -> int:
    src = path.read_text()
    out = src
    hits = 0
    for old, new in pairs:
        n = out.count(old)
        hits += n
        out = out.replace(old, new)
    if hits:
        out = add_compose_import(out)
    if out != src:
        path.write_text(out)
    return hits


def main() -> int:
    total = 0
    for f in GAMES:
        n = rewrite(f, GAME_PAIRS)
        total += n
        if n:
            print(f"{f.relative_to(ROOT)}: {n} composition(s) rewritten")  # noqa: T201
    n = rewrite(DEMO07, DEMO07_PAIRS)
    total += n
    if n:
        print(f"{DEMO07.relative_to(ROOT)}: {n} composition(s) rewritten")  # noqa: T201
    print(f"total: {total}")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
