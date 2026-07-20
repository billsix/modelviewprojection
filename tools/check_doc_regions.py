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

2. **Name collision.** Two regions with the same name (a query always selects
   the first), or one name that is a **prefix** of another in the same file
   (``define rotate`` vs ``define rotate around``) -- Sphinx matches the first
   line *containing* the anchor text, so the shorter can pull the wrong region.
   Both are silent.

Run from the repo root: ``python tools/check_doc_regions.py`` (or ``make
check-regions``).  A third check -- region content vs a lockfile, to catch
cross-repo drift -- is planned but not yet wired (it depends on the marker-ID
scheme still being decided); see ``tasks/dangling-book-code-includes.md``.
"""

from __future__ import annotations

import collections
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
# Match only genuine marker COMMENTS (``# doc-region-begin ...``), not the
# string ``doc-region-begin`` appearing inside a regex/docstring (this file
# itself contains the pattern in its regex literals -- without the ``#`` anchor
# it would falsely flag its own source as a duplicate).
_BEGIN_MARKER: re.Pattern[str] = re.compile(
    r"#\s*doc-region-begin (?P<name>.+?)[ \t]*$", re.MULTILINE
)
_END_MARKER: re.Pattern[str] = re.compile(
    r"#\s*doc-region-end (?P<name>.+?)[ \t]*$", re.MULTILINE
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


def _name_collision_errors() -> list[str]:
    """Every anchor in one file that another anchor can shadow: an **exact
    duplicate** (two regions with the same name -- a query always selects the
    first) or a **prefix** of another name (a query for the shorter can match
    the longer's line, since Sphinx matches the first *containing* line).

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
            # raw list keeps repeats, so exact duplicates are visible (a set
            # would collapse them and hide the collision)
            occurrences: list[str] = [
                m.group("name") for m in marker.finditer(text)
            ]
            counts: collections.Counter[str] = collections.Counter(occurrences)
            name: str
            count: int
            for name, count in sorted(counts.items()):
                if count > 1:
                    errors.append(
                        f"{source_path.relative_to(_REPO_ROOT)}: "
                        f"doc-region-{kind} '{name}' appears {count} times -- "
                        f"a query always selects the first"
                    )
            names: list[str] = sorted(counts)
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
    collisions: list[str] = _name_collision_errors()

    if collisions:
        print("NAME COLLISIONS (a query can select the wrong region):")
        for problem in collisions:
            print(f"  {problem}")
    if unresolved:
        print("UNRESOLVED ANCHORS (the listing renders empty):")
        for problem in unresolved:
            print(f"  {problem}")

    total: int = len(unresolved) + len(collisions)
    if total == 0:
        print("doc-region anchors OK: all resolve, no name collisions.")
        return 0
    print(
        f"\n{total} problem(s): {len(collisions)} name collision(s), "
        f"{len(unresolved)} unresolved anchor(s)."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
