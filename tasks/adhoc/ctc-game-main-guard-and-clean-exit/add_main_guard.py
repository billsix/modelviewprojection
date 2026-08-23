#!/usr/bin/env python3
"""Guard each Code-the-Classics game's trailing bare ``go()`` behind
``if __name__ == "__main__":`` so importing the module no longer launches the
game (a GL window + a 60 Hz loop).  Part 1 of
tasks/ctc-game-main-guard-and-clean-exit.md.

Run from the repo root:

    python tasks/adhoc/ctc-game-main-guard-and-clean-exit/add_main_guard.py

Idempotent: a file that already carries the guard is skipped, so a second run
reports zero changes (the "prove a codemod is idempotent by running it twice"
rule).  Each game currently ends with a single unindented ``go()`` line; this
rewrites that one line to the two-line guard, leaving everything else (the
module-level game state and ``update``/``draw`` functions) at module scope --
which is required, since ``go()`` reads its caller's module globals by
introspection.
"""

from __future__ import annotations

import pathlib

# The 10 game entry modules, each currently ending in a bare top-level ``go()``.
GAMES: list[str] = [
    "ports/codetheclassics/vol1/boing/boing.py",
    "ports/codetheclassics/vol1/bunner/bunner.py",
    "ports/codetheclassics/vol1/cavern/cavern.py",
    "ports/codetheclassics/vol1/myriapod/myriapod.py",
    "ports/codetheclassics/vol1/soccer/soccer.py",
    "ports/codetheclassics/vol2/avenger/avenger.py",
    "ports/codetheclassics/vol2/beatstreets/beatstreets.py",
    "ports/codetheclassics/vol2/eggzy/eggzy.py",
    "ports/codetheclassics/vol2/kinetix/kinetix.py",
    "ports/codetheclassics/vol2/leadingedge/leadingedge.py",
]

GUARD: str = 'if __name__ == "__main__":\n    go()\n'


def guard_one(path: pathlib.Path) -> bool:
    """Wrap a trailing bare ``go()`` in a __main__ guard. Return True if changed."""
    text: str = path.read_text()
    # Idempotency: once the guard is present, do nothing on any later run.
    if '__name__ == "__main__"' in text:
        return False
    # ``keepends=True`` so the trailing newline is preserved when we rejoin.
    lines: list[str] = text.splitlines(keepends=True)
    # Replace the LAST unindented ``go()`` call line with the guarded form.
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].rstrip("\n") == "go()":
            lines[i] = GUARD
            path.write_text("".join(lines))
            return True
    raise SystemExit(f"{path}: no trailing bare 'go()' found -- aborting")


def main() -> None:
    changed: int = 0
    for rel in GAMES:
        if guard_one(pathlib.Path(rel)):
            print(f"guarded : {rel}")
            changed += 1
        else:
            print(f"skip    : {rel} (already guarded)")
    print(f"\n{changed} file(s) changed, {len(GAMES) - changed} already guarded")


if __name__ == "__main__":
    main()
