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

3. **Empty region.** A directive with BOTH a ``:start-after:`` and an
   ``:end-before:`` whose markers exist but have nothing between them -- markers
   placed adjacently, or separated only by blank/marker lines.  Both markers
   resolve, so check 1 passes, yet Sphinx renders an EMPTY listing.  This
   shipped: ch01's "Importing Libraries" block was empty this way (see
   ``tasks/archive/2026/07/23/demo01-import-region-empty.md``).

Run from the repo root: ``python tools/check_doc_regions.py`` (or ``make
check-regions``).  A further check -- region content vs a lockfile, to catch
cross-repo drift -- is planned but not yet wired (it depends on the marker-ID
scheme still being decided); see ``tasks/dangling-book-code-includes.md``.
"""

from __future__ import annotations

import argparse
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
# Match only genuine marker COMMENTS -- a ``#`` at the START of the line (after
# indentation) followed by the token.  Anchoring to line-start is what keeps the
# token from matching when it appears *inside* a string literal or mid-line in a
# docstring/comment (this file's own prose mentions ``# doc-region-begin``, and
# tests/test_check_doc_regions.py embeds the marker syntax in test strings);
# real markers are always their own comment line, so nothing genuine is missed.
_BEGIN_MARKER: re.Pattern[str] = re.compile(
    r"^[ \t]*#[ \t]*doc-region-begin (?P<name>.+?)[ \t]*$", re.MULTILINE
)
_END_MARKER: re.Pattern[str] = re.compile(
    r"^[ \t]*#[ \t]*doc-region-end (?P<name>.+?)[ \t]*$", re.MULTILINE
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


def _region_is_empty(source: str, start_name: str, end_name: str) -> bool:
    """True iff Sphinx would render an EMPTY listing for this begin/end pair:
    no content line lies strictly between the first
    ``doc-region-begin <start_name>`` line and the first *following*
    ``doc-region-end <end_name>`` line.  A content line is one that is neither
    blank nor itself a doc-region marker.

    Mirrors Sphinx's ``:start-after:`` / ``:end-before:`` semantics -- match
    the first line *containing* the anchor text, and search for the end AFTER
    the start.  Returns ``False`` when the ordered pair can't be located
    (existence and ordering are the other checks' concern -- don't
    double-report here).
    """
    lines: list[str] = source.splitlines()
    begin_needle: str = f"doc-region-begin {start_name}"
    end_needle: str = f"doc-region-end {end_name}"

    begin_idx: int | None = None
    index: int
    line: str
    for index, line in enumerate(lines):
        if begin_needle in line:
            begin_idx = index
            break
    if begin_idx is None:
        return False

    end_idx: int | None = None
    for index in range(begin_idx + 1, len(lines)):
        if end_needle in lines[index]:
            end_idx = index
            break
    if end_idx is None:
        return False

    between: str
    for between in lines[begin_idx + 1 : end_idx]:
        stripped: str = between.strip()
        is_marker: bool = (
            "doc-region-begin" in between or "doc-region-end" in between
        )
        if stripped and not is_marker:
            return False  # a real content line -> not empty
    return True


def _empty_region_errors() -> list[str]:
    """Every book anchor pair whose in-file slice is empty -- both markers
    exist (so check 1 passes) but nothing renders.  Only directives with BOTH
    a ``:start-after:`` and an ``:end-before:`` are checked; a one-sided
    include runs to the start/end of the file and is a different case.
    """
    errors: list[str] = []
    rst_path: pathlib.Path
    for rst_path in sorted(_BOOK_DIR.rglob("*.rst")):
        text: str = rst_path.read_text()
        for directive in _LITERALINCLUDE.finditer(text):
            options: str = directive.group("options")
            start = _START_AFTER.search(options)
            end = _END_BEFORE.search(options)
            if start is None or end is None:
                continue  # need both ends to bound a slice
            target: pathlib.Path = (
                rst_path.parent / directive.group("target")
            ).resolve()
            if not target.exists():
                continue  # the unresolved-anchor check reports a missing file
            source: str = target.read_text()
            if f"doc-region-begin {start.group('name')}" not in source or (
                f"doc-region-end {end.group('name')}" not in source
            ):
                continue  # a missing marker is check 1's to report
            if _region_is_empty(
                source, start.group("name"), end.group("name")
            ):
                errors.append(
                    f"{rst_path.relative_to(_REPO_ROOT)}: region "
                    f"'{start.group('name')}' .. '{end.group('name')}' in "
                    f"{directive.group('target')} is EMPTY -- adjacent or "
                    f"blank/marker-only markers render nothing"
                )
    return errors


def _referenced_anchors() -> set[tuple[pathlib.Path, str, str]]:
    """Every ``(resolved_target, name, kind)`` a book ``literalinclude``
    references -- ``kind`` is ``'begin'`` (from a ``:start-after:``) or
    ``'end'`` (from an ``:end-before:``), matched to its own marker kind the
    way the collision check does.
    """
    referenced: set[tuple[pathlib.Path, str, str]] = set()
    rst_path: pathlib.Path
    for rst_path in sorted(_BOOK_DIR.rglob("*.rst")):
        text: str = rst_path.read_text()
        for directive in _LITERALINCLUDE.finditer(text):
            target: pathlib.Path = (
                rst_path.parent / directive.group("target")
            ).resolve()
            options: str = directive.group("options")
            reference: re.Match[str]
            for reference in _START_AFTER.finditer(options):
                referenced.add((target, reference.group("name"), "begin"))
            for reference in _END_BEFORE.finditer(options):
                referenced.add((target, reference.group("name"), "end"))
    return referenced


def _dead_marker_report() -> list[str]:
    """Every doc-region marker in first-party source that **no** book
    ``literalinclude`` references (matched by target file + name + marker kind).

    Reusing a name across files is fine -- a marker is dead only if nothing
    references *that file's* copy of that kind.  This is **informational, not a
    failure**: an unreferenced marker may be a deliberate anchor for an
    unwritten chapter, so it never changes the exit code -- it just makes the
    otherwise-invisible dead set visible (the checker validates book->code, so
    a marker no chapter includes is silent).
    """
    referenced: set[tuple[pathlib.Path, str, str]] = _referenced_anchors()
    report: list[str] = []
    source_path: pathlib.Path
    for source_path in sorted(_REPO_ROOT.rglob("*.py")):
        if _BOOK_DIR in source_path.parents:
            continue
        text: str = source_path.read_text()
        resolved: pathlib.Path = source_path.resolve()
        marker: re.Pattern[str]
        kind: str
        for marker, kind in ((_BEGIN_MARKER, "begin"), (_END_MARKER, "end")):
            occurrence: re.Match[str]
            for occurrence in marker.finditer(text):
                name: str = occurrence.group("name")
                if (resolved, name, kind) not in referenced:
                    report.append(
                        f"{source_path.relative_to(_REPO_ROOT)}: "
                        f"doc-region-{kind} '{name}' -- no literalinclude "
                        f"references it"
                    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Validate the book's doc-region anchors."
    )
    parser.add_argument(
        "--report-dead",
        action="store_true",
        help=(
            "also list doc-region markers that no chapter includes "
            "(informational -- never changes the exit code)"
        ),
    )
    args: argparse.Namespace = parser.parse_args(argv)

    unresolved: list[str] = _unresolved_anchor_errors()
    collisions: list[str] = _name_collision_errors()
    empty: list[str] = _empty_region_errors()

    if collisions:
        print("NAME COLLISIONS (a query can select the wrong region):")
        for problem in collisions:
            print(f"  {problem}")
    if unresolved:
        print("UNRESOLVED ANCHORS (the listing renders empty):")
        for problem in unresolved:
            print(f"  {problem}")
    if empty:
        print("EMPTY REGIONS (both markers exist, but nothing renders):")
        for problem in empty:
            print(f"  {problem}")

    total: int = len(unresolved) + len(collisions) + len(empty)
    if total == 0:
        print(
            "doc-region anchors OK: all resolve, no name collisions, "
            "no empty regions."
        )
    else:
        print(
            f"\n{total} problem(s): {len(collisions)} name collision(s), "
            f"{len(unresolved)} unresolved anchor(s), "
            f"{len(empty)} empty region(s)."
        )

    # Opt-in, informational, and OUTSIDE the pass/fail total -- an unreferenced
    # marker may be a deliberate anchor for an unwritten chapter, so it never
    # changes the exit code (see _dead_marker_report).
    if args.report_dead:
        dead: list[str] = _dead_marker_report()
        if dead:
            print(
                f"\nINFO -- {len(dead)} dead marker(s) no chapter includes "
                "(not a failure):"
            )
            for note in dead:
                print(f"  {note}")
        else:
            print("\nno dead markers: every doc-region marker is referenced.")

    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
