#!/usr/bin/env python3
"""Rename the ``pgzero_gl`` launch function ``go`` -> ``main`` at each Code-the-
Classics game's import and (already-guarded) call site, for
tasks/ctc-game-main-guard-and-clean-exit.md.

Runs AFTER add_main_guard.py (the games already have
``if __name__ == "__main__":\\n    go()``). The shim's ``go`` was renamed to
``main`` (see ``src/modelviewprojection/pgzero_gl/runner.py`` / ``__init__.py``);
this moves the 10 games' references to match.

Run from the repo root, THEN run ``ruff check ports --fix`` to re-sort the
import block (``main`` sorts to a different position than ``go`` did):

    python tasks/adhoc/ctc-game-main-guard-and-clean-exit/rename_go_to_main.py
    ruff check ports --fix        # isort: put ``main`` in sorted order

**Word-precise, so prose is never touched** (e.g. myriapod's "which way to go"
comment): it rewrites only the exact whole lines ``    go,`` (the import entry)
and ``    go()`` (the guarded call), not the substring "go" anywhere else.

Idempotent: once neither exact line remains, a re-run makes no change.
"""

from __future__ import annotations

import pathlib

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


def rename_one(path: pathlib.Path) -> bool:
    """Rename the import and guarded call ``go`` -> ``main``. True if changed."""
    text: str = path.read_text()
    # Exact whole-line replacements: the import-tuple entry and the guarded
    # call. Anchoring on the leading indent + trailing newline keeps this from
    # matching "go" inside identifiers or prose.
    new: str = text.replace("    go,\n", "    main,\n").replace(
        "    go()\n", "    main()\n"
    )
    if new == text:
        return False
    path.write_text(new)
    return True


def main() -> None:
    changed: int = 0
    for rel in GAMES:
        if rename_one(pathlib.Path(rel)):
            print(f"renamed : {rel}")
            changed += 1
        else:
            print(f"skip    : {rel} (already main)")
    print(f"\n{changed} file(s) changed, {len(GAMES) - changed} already main")


if __name__ == "__main__":
    main()
