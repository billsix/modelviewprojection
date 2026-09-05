#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Compare two tools/ctc_state_trace.py dumps STRUCTURALLY, frame by frame (the
# last step of the Code-the-Classics input-path gate; promoted from
# tasks/adhoc/codetheclassics-tighten-games/ on 2026-09-05). A refactor
# legitimately changes the
# dump's SHAPE without changing behaviour -- a derived property dropped from
# the Actor (`left`/`centerx`/`centery`), an attribute now declared as a
# dataclass field (so it appears from frame 0 instead of on first assignment),
# a CPU surface whose class name changed -- so a plain `diff` is too strict.
# This parses each frame's dict and reports the first differing PATH, after
# dropping the keys named with --ignore and collapsing objects of the classes
# named with --opaque to their class name. Exit 0 iff no frame differs.
#
# Usage:
#   python tools/ctc_compare_traces.py base.txt cur.txt \
#       [--ignore left,centerx,centery,frame] [--opaque Surface] [--show N]

import argparse
import ast
from collections.abc import Iterator
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("base")
ap.add_argument("cur")
ap.add_argument("--ignore", default="left,centerx,centery")
ap.add_argument("--opaque", default="")
ap.add_argument("--show", type=int, default=2)
args = ap.parse_args()
IGNORE = set(filter(None, args.ignore.split(",")))
OPAQUE = set(filter(None, args.opaque.split(",")))


def load(path: str) -> list:
    return [
        ast.literal_eval(line.split(" ", 1)[1]) for line in Path(path).open()
    ]


def norm(x):  # noqa: ANN001
    if isinstance(x, dict):
        if x.get("class") in OPAQUE:
            return x["class"]
        return {k: norm(v) for k, v in x.items() if k not in IGNORE}
    if isinstance(x, list):
        return [norm(v) for v in x]
    return x


def walk(x, y, path: str = "") -> Iterator[str]:  # noqa: ANN001
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x:
                yield f"only in cur: {path}.{k} = {y[k]!r:.80}"
            elif k not in y:
                yield f"only in base: {path}.{k} = {x[k]!r:.80}"
            else:
                yield from walk(x[k], y[k], f"{path}.{k}")
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            yield f"length differs: {path} {len(x)} vs {len(y)}"
            return
        for i, (a, b) in enumerate(zip(x, y)):
            yield from walk(a, b, f"{path}[{i}]")
    elif x != y:
        yield f"differs: {path} {x!r:.60} -> {y!r:.60}"


base, cur = load(args.base), load(args.cur)
if len(base) != len(cur):
    print(f"frame counts differ: {len(base)} vs {len(cur)}")
    raise SystemExit(1)
bad = 0
for i, (b, c) in enumerate(zip(base, cur)):
    diffs = list(walk(norm(b), norm(c)))
    if diffs:
        bad += 1
        if bad <= args.show:
            print(f"frame {i}:")
            print("\n".join("  " + d for d in diffs[:8]))
print(
    f"{'IDENTICAL' if not bad else 'DIFFER'}: {len(base)} frames, {bad} differ"
    f" (ignoring {sorted(IGNORE)}; opaque {sorted(OPAQUE)})"
)
raise SystemExit(1 if bad else 0)
