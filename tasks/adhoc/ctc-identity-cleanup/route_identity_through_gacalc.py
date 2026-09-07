#!/usr/bin/env python3
"""Part B of ctc-identity-cleanup: in the six games that USE the identity model
matrix, build it once at import through gacalc -- the same machinery as MODEL /
ortho_pixels -- instead of the raw-numpy ``_identity()`` helper.

Per game it (1) replaces the ``def _identity()`` helper with a module-level
``_IDENTITY`` constant built via ``np.asarray(to_matrix(identity(), g3.Vector),
dtype=np.float32)`` (the exact wrapper ortho_pixels uses, so ty is satisfied),
(2) rewrites the ``_identity()`` call sites to ``_IDENTITY``, and (3) adds
``identity`` to the ``from gacalc.transforms import (...)`` block in isort's
position (lowercase function group, right after ``compose``).

Idempotent: a second run makes no change (the def is gone, the calls are
rewritten, and the import insert is guarded by a negative lookahead). Run once
from the repo root:
  python3 tasks/adhoc/ctc-identity-cleanup/route_identity_through_gacalc.py
"""
import re
from pathlib import Path

TARGETS = [
    "ports/codetheclassics/vol1/bunner/bunner.py",
    "ports/codetheclassics/vol1/soccer/soccer.py",
    "ports/codetheclassics/vol2/avenger/avenger.py",
    "ports/codetheclassics/vol2/beatstreets/beatstreets.py",
    "ports/codetheclassics/vol2/eggzy/eggzy.py",
    "ports/codetheclassics/vol2/leadingedge/leadingedge.py",
]

DEF_BLOCK = re.compile(
    r'def _identity\(\) -> NDArray\[np\.float32\]:\n'
    r'    """Return a 4x4 identity matrix\."""\n'
    r'    return np\.identity\(4, dtype=np\.float32\)'
)
CONST = (
    "#: The 4x4 identity model matrix, built once at import through gacalc --\n"
    "#: the same machinery as ``ortho_pixels`` / ``MODEL``.\n"
    "_IDENTITY: NDArray[np.float32] = np.asarray(\n"
    "    to_matrix(identity(), g3.Vector), dtype=np.float32\n"
    ")"
)
# add `identity,` right after the `    compose,` import line, unless already there
IMPORT_INS = re.compile(r'(\n    compose,\n)(?!    identity,\n)')

for rel in TARGETS:
    p = Path(rel)
    src = p.read_text()
    orig = src
    # 1. def -> constant (do this before rewriting call sites, so the def line's
    #    own `_identity()` isn't touched by step 2)
    src, n_def = DEF_BLOCK.subn(CONST, src)
    # 2. call sites _identity() -> _IDENTITY (only call sites remain now)
    src, n_call = re.subn(r'\b_identity\(\)', '_IDENTITY', src)
    # 3. import insertion (guarded)
    src, n_imp = IMPORT_INS.subn(r'\1    identity,\n', src)
    if src == orig:
        print(f"  {rel}: already routed (no change)")
        continue
    if n_def != 1:
        raise SystemExit(f"ERROR {rel}: def matched {n_def} times (expected 1)")
    p.write_text(src)
    print(f"  {rel}: def->const, {n_call} call site(s) rewritten, import +identity")
