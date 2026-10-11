#!/usr/bin/env python3
"""Rewire the book's figure references from the retired gnuplot/matplotlib outputs to
the ePiX outputs: ``_static/<stem>.svg`` -> ``_static/epix/<stem>.*`` for exactly the
35 ported figure stems. The wildcard lets Sphinx pick the PDF (latex) or PNG (html)
per builder, matching the ePiX renderer's output pair.

Idempotent: after the first run the refs read ``_static/epix/<stem>.*``, which no longer
matches ``_static/<stem>.svg``, so a second run changes nothing. Verify with a re-grep
for ``_static/<stem>.svg`` returning zero. Paths are resolved relative to the repo root
(this script's location), never container-absolute.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO: Path = Path(__file__).resolve().parents[3]
DOCS: Path = REPO / "book" / "docs"

STEMS: list[str] = [
    "modelspace",
    "monitor", "monitor2",
    "screenspace", "screenspace2",
    "ndcSpace", "ndcSpace1",
    "viewport",
    "plot1", "plot2", "plot3", "plot4",
    "disproportionate1", "disproportionate2",
    "translation-forwards-0", "translation-forwards-2", "translation-forwards-3",
    "translation2-forwards-0", "translation2-forwards-2", "translation2-forwards-3",
    "scale-0", "scale-2", "scale-4",
    "incorrectrotate-forwards-1", "incorrectrotate-forwards-2",
    "incorrectrotate-forwards-3", "incorrectrotate-forwards-4",
    "incorrectrotate-forwards-5", "incorrectrotate-forwards-6",
    "rotate-sloppy-forwards-3", "rotate-sloppy-forwards-4", "rotate-sloppy-forwards-5",
    "rotate-sloppy-forwards-6", "rotate-sloppy-forwards-7", "rotate-sloppy-forwards-8",
]

# One pattern per stem: _static/<stem>.svg  (exact, not a longer name, ext-anchored).
PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"_static/" + re.escape(s) + r"\.svg(?![\w.-])"), f"_static/epix/{s}.*")
    for s in STEMS
]


def main() -> int:
    changed: int = 0
    for rst in sorted(DOCS.glob("*.rst")):
        text: str = rst.read_text()
        new: str = text
        for pat, repl in PATTERNS:
            new = pat.sub(repl, new)
        if new != text:
            rst.write_text(new)
            n: int = sum(1 for _ in re.finditer(r"_static/epix/", new)) - sum(
                1 for _ in re.finditer(r"_static/epix/", text)
            )
            print(f"{rst.name}: {n} ref(s) rewired")
            changed += 1
    print(f"files changed: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
