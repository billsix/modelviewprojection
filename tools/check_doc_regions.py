# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""Validate the book's ``literalinclude`` doc-region anchors.

The book selects code to display with
``:start-after: doc-region-begin <name>`` / ``:end-before: doc-region-end
<name>``.  Two failure modes are **silent** -- Sphinx emits at most a warning
and renders the wrong thing (or nothing), so a broken listing ships unnoticed.
This tool makes both loud (exit 1):

1. **Unresolved anchor.** A directive names an anchor that does not exist in its
   target file.  Sphinx renders an EMPTY block -- the caption and prose survive,
   the code silently vanishes.

2. **Prefix collision.** Sphinx matches the first line *containing* the anchor
   text, so if one anchor name is a prefix of another in the same file
   (``define rotate`` vs ``define rotate around``), a query for the shorter can
   match the longer's line and pull the wrong region -- again with no error.

Run from the repo root: ``python tools/check_doc_regions.py`` (or ``make
check-regions``).  A third check -- region content vs a lockfile, to catch
cross-repo drift -- is planned but not yet wired (it depends on the marker-ID
scheme still being decided); see ``tasks/dangling-book-code-includes.md``.
"""

from __future__ import annotations

import pathlib
import re
import sys

# Where the book's .rst sources live and where included code lives.
_REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent
_BOOK_DIR: pathlib.Path = _REPO_ROOT / "book" / "docs"

# A literalinclude directive plus its option block (the indented ``:key:``
# lines that follow it).  Captures the target path and the option text.
_LITERALINCLUDE: re.Pattern[str] = re.compile(
    r"^[ \t]*\.\. literalinclude:: (?P<target>\S+)\n"
    r"(?P<options>(?:[ \t]+:[^\n]*\n)+)",
    re.MULTILINE,
)
_START_AFTER: re.Pattern[str] = re.compile(
    r":start-after: doc-region-begin (?P<name>.+?)[ \t]*$", re.MULTILINE
)
_END_BEFORE: re.Pattern[str] = re.compile(
    r":end-before: doc-region-end (?P<name>.+?)[ \t]*$", re.MULTILINE
)
_BEGIN_MARKER: re.Pattern[str] = re.compile(
    r"doc-region-begin (?P<name>.+?)[ \t]*$", re.MULTILINE
)
_END_MARKER: re.Pattern[str] = re.compile(
    r"doc-region-end (?P<name>.+?)[ \t]*$", re.MULTILINE
)


def _unresolved_anchor_errors() -> list[str]:
    """Every book anchor whose begin/end marker is absent from its target."""
    errors: list[str] = []
    rst_path: pathlib.Path
    for rst_path in sorted(_BOOK_DIR.rglob("*.rst")):
        text: str = rst_path.read_text()
        for directive in _LITERALINCLUDE.finditer(text):
            target: pathlib.Path = (
                rst_path.parent / directive.group("target")
            ).resolve()
            options: str = directive.group("options")
            start = _START_AFTER.search(options)
            end = _END_BEFORE.search(options)
            if start is None and end is None:
                continue  # a plain literalinclude, not a doc-region one
            if not target.exists():
                errors.append(
                    f"{rst_path.relative_to(_REPO_ROOT)}: target file "
                    f"{directive.group('target')} does not exist"
                )
                continue
            source: str = target.read_text()
            # Sphinx matches a line CONTAINING the anchor text; mirror that.
            if start is not None and (
                f"doc-region-begin {start.group('name')}" not in source
            ):
                errors.append(
                    f"{rst_path.relative_to(_REPO_ROOT)}: no "
                    f"'doc-region-begin {start.group('name')}' in "
                    f"{directive.group('target')}"
                )
            if end is not None and (
                f"doc-region-end {end.group('name')}" not in source
            ):
                errors.append(
                    f"{rst_path.relative_to(_REPO_ROOT)}: no "
                    f"'doc-region-end {end.group('name')}' in "
                    f"{directive.group('target')}"
                )
    return errors


def _prefix_collision_errors() -> list[str]:
    """Every pair of anchors in one file where one name is a prefix of another.

    Checked for begin- and end-markers separately, since ``:start-after:`` and
    ``:end-before:`` select on their own marker kind.
    """
    errors: list[str] = []
    source_path: pathlib.Path
    for source_path in sorted(_REPO_ROOT.rglob("*.py")):
        if _BOOK_DIR in source_path.parents:
            continue
        text: str = source_path.read_text()
        marker: re.Pattern[str]
        kind: str
        for marker, kind in ((_BEGIN_MARKER, "begin"), (_END_MARKER, "end")):
            names: list[str] = sorted(
                {m.group("name") for m in marker.finditer(text)}
            )
            shorter: str
            longer: str
            for shorter in names:
                for longer in names:
                    if shorter != longer and longer.startswith(shorter):
                        errors.append(
                            f"{source_path.relative_to(_REPO_ROOT)}: "
                            f"doc-region-{kind} '{shorter}' is a prefix of "
                            f"'{longer}' -- a :start-after:/:end-before: query "
                            f"for the shorter can match the longer's line"
                        )
    return errors


def main() -> int:
    unresolved: list[str] = _unresolved_anchor_errors()
    collisions: list[str] = _prefix_collision_errors()

    if collisions:
        print("PREFIX COLLISIONS (a query can select the wrong region):")
        for problem in collisions:
            print(f"  {problem}")
    if unresolved:
        print("UNRESOLVED ANCHORS (the listing renders empty):")
        for problem in unresolved:
            print(f"  {problem}")

    total: int = len(unresolved) + len(collisions)
    if total == 0:
        print("doc-region anchors OK: all resolve, no prefix collisions.")
        return 0
    print(
        f"\n{total} problem(s): {len(collisions)} prefix collision(s), "
        f"{len(unresolved)} unresolved anchor(s)."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
