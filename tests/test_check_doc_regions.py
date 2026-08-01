# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""Regression tests for ``tools/check_doc_regions.py``'s empty-region check.

The checker is a container gate (``make check-regions``), not on the test
``pythonpath``, so it is loaded by path.  These lock in the behaviour that a
``doc-region-begin``/``-end`` pair with nothing between it -- adjacent, or
separated only by blank/marker lines -- is caught: exactly the ch01 "Importing
Libraries" bug (``tasks/archive/2026/07/23/demo01-import-region-empty.md``),
which both markers-exist checks passed while Sphinx rendered nothing.
"""

from __future__ import annotations

import importlib.util
import pathlib
import types

import pytest

_REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent
_CHECKER_PATH: pathlib.Path = _REPO_ROOT / "tools" / "check_doc_regions.py"


def _load_checker() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_doc_regions", _CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module: types.ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker: types.ModuleType = _load_checker()


@pytest.mark.parametrize(
    ("source", "start", "end", "expected"),
    [
        # adjacent markers -> empty
        ("# doc-region-begin a\n# doc-region-end a\n", "a", "a", True),
        # only blank lines between -> empty
        ("# doc-region-begin a\n\n  \n# doc-region-end a\n", "a", "a", True),
        # a real code line between -> not empty
        ("# doc-region-begin a\nx = 1\n# doc-region-end a\n", "a", "a", False),
        # split region (begin/end names differ) with content -> not empty
        ("# doc-region-begin a\nx = 1\n# doc-region-end b\n", "a", "b", False),
        # split region, adjacent -> empty
        ("# doc-region-begin a\n# doc-region-end b\n", "a", "b", True),
        # only nested markers between -> still empty
        (
            "# doc-region-begin a\n# doc-region-begin i\n"
            "# doc-region-end i\n# doc-region-end a\n",
            "a",
            "a",
            True,
        ),
        # end before begin: no ordered pair -> not this check's error
        ("# doc-region-end a\nx = 1\n# doc-region-begin a\n", "a", "a", False),
    ],
)
def test_region_is_empty(
    source: str, start: str, end: str, expected: bool
) -> None:
    assert checker._region_is_empty(source, start, end) is expected


def test_empty_region_errors_flags_adjacent_only(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End to end: a directive whose markers are adjacent is flagged; a
    directive over a non-empty region on the same file is not."""
    book: pathlib.Path = tmp_path / "book" / "docs"
    book.mkdir(parents=True)
    (tmp_path / "book" / "demo.py").write_text(
        "# doc-region-begin empty one\n"
        "# doc-region-end empty one\n"
        "x = 1\n"
        "# doc-region-begin good one\n"
        "y = 2\n"
        "# doc-region-end good one\n"
    )
    (book / "chX.rst").write_text(
        ".. literalinclude:: ../demo.py\n"
        "   :start-after: doc-region-begin empty one\n"
        "   :end-before: doc-region-end empty one\n"
        "\n"
        ".. literalinclude:: ../demo.py\n"
        "   :start-after: doc-region-begin good one\n"
        "   :end-before: doc-region-end good one\n"
    )
    monkeypatch.setattr(checker, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(checker, "_BOOK_DIR", book)

    errors: list[str] = checker._empty_region_errors()
    assert len(errors) == 1
    assert "empty one" in errors[0]
    assert "good one" not in "".join(errors)


def test_markers_match_only_comment_lines() -> None:
    """The marker regexes match a genuine comment-line marker but NOT the token
    embedded in a string literal or as a trailing comment -- otherwise this
    test file's own marker-shaped strings (and the checker's prose) would
    register as markers and trip the collision / dead-marker scans."""
    real: str = "    # doc-region-begin real one\n"
    in_string: str = '    x = "# doc-region-begin fake"\n'
    trailing: str = "    value = 1  # doc-region-begin trailing\n"

    names: list[str] = [
        match.group("name") for match in checker._BEGIN_MARKER.finditer(real)
    ]
    assert names == ["real one"]
    assert list(checker._BEGIN_MARKER.finditer(in_string)) == []
    assert list(checker._BEGIN_MARKER.finditer(trailing)) == []


def test_dead_marker_report_flags_only_unreferenced(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A marker a literalinclude references is not reported; one nothing
    references is."""
    book: pathlib.Path = tmp_path / "book" / "docs"
    book.mkdir(parents=True)
    (tmp_path / "book" / "demo.py").write_text(
        "# doc-region-begin used\ncode = 1\n# doc-region-end used\n"
        "# doc-region-begin unused\ncode = 2\n# doc-region-end unused\n"
    )
    (book / "ch.rst").write_text(
        ".. literalinclude:: ../demo.py\n"
        "   :start-after: doc-region-begin used\n"
        "   :end-before: doc-region-end used\n"
    )
    monkeypatch.setattr(checker, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(checker, "_BOOK_DIR", book)

    report: str = "\n".join(checker._dead_marker_report())
    assert "unused" in report
    assert "'used'" not in report  # the referenced region is not flagged
