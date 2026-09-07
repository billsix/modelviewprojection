#!/usr/bin/env python3
"""Remove the dead ``_identity()`` helper from the four CtC games that define
but never call it (boing, cavern, myriapod, kinetix).

Idempotent: matches the exact 3-line def plus its two trailing blank lines and
deletes it; a second run finds nothing and is a clean no-op. Run once from the
repo root:  python3 tasks/adhoc/ctc-identity-cleanup/apply.py
"""
import re
from pathlib import Path

# The four files where `_identity` is defined but has zero call sites (verified
# by an AST unused-private-symbol sweep, 2026-09-07). The six other games call
# _identity() and are deliberately left untouched here (see the task doc).
TARGETS = [
    "ports/codetheclassics/vol1/boing/boing.py",
    "ports/codetheclassics/vol1/cavern/cavern.py",
    "ports/codetheclassics/vol1/myriapod/myriapod.py",
    "ports/codetheclassics/vol2/kinetix/kinetix.py",
]

# The def block, plus up to two trailing blank lines. The two blank lines that
# *precede* the block stay, so the surviving neighbours keep PEP8 2-blank
# separation (ruff format is run afterwards and must report no change).
BLOCK = re.compile(
    r'def _identity\(\) -> NDArray\[np\.float32\]:\n'
    r'    """Return a 4x4 identity matrix\."""\n'
    r'    return np\.identity\(4, dtype=np\.float32\)\n'
    r'(?:\n){0,2}'
)

for rel in TARGETS:
    p = Path(rel)
    src = p.read_text()
    new, n = BLOCK.subn("", src)
    if n == 0:
        print(f"  {rel}: already clean (0 removed)")
        continue
    if n > 1:
        raise SystemExit(f"ERROR: {rel} matched {n} times, expected 1")
    p.write_text(new)
    print(f"  {rel}: removed _identity()")
