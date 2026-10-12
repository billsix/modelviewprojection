#!/usr/bin/env python3
"""Convert positional gacalc translate()/uniform_scale() calls to the keyword
form translate(b=...) / uniform_scale(m=...), to make the f(x) = m*x + b reading
explicit (see tasks/apply-python-coding-standard.md, "Cross-repo m*x+b").

Discriminates by CALL SHAPE, not by name: only a call with exactly one positional
arg and no keywords is converted. That is what distinguishes gacalc's
translate(b=vector) (one arg) from the fixed-function matrix_stack.translate(
matrix_stack, x, y, z) (four args), which must stay positional. Already-keyword
calls are skipped, so the pass is idempotent (run twice -> second run is a no-op).

Two passes, both idempotent and both shape-discriminated:
  1. real code calls, found via the AST;
  2. doctest calls on ``>>>``/``...`` lines, which the AST does not see because they
     live inside docstring string literals -- found by paren-matching the call text
     and re-parsing just that snippet with the AST to apply the same one-arg test.

Usage:  python convert_mx_b.py <file-or-dir> [<file-or-dir> ...]
Paths are taken as given (run it from the repo root). Prints every edit.
"""

from __future__ import annotations

import ast
import pathlib
import sys

TARGETS: dict[str, str] = {"translate": "b", "uniform_scale": "m"}


def _snippet_is_single_arg(snippet: str, keyword: str) -> bool:
    """True if ``snippet`` parses as a single-positional-arg call with no keywords."""
    try:
        parsed: ast.Expression = ast.parse(snippet, mode="eval")
    except SyntaxError:
        return False
    call: ast.expr = parsed.body
    return (
        isinstance(call, ast.Call)
        and len(call.args) == 1
        and not call.keywords
    )


def _doctest_edits(lines: list[str]) -> list[tuple[int, int, str]]:
    """Insertions for convertible calls on doctest (``>>>``/``...``) lines."""
    edits: list[tuple[int, int, str]] = []
    for lineno, line in enumerate(lines, start=1):
        if line.lstrip()[:4] not in (">>> ", "... "):
            continue
        for name, keyword in TARGETS.items():
            search_from: int = 0
            token: str = name + "("
            while (idx := line.find(token, search_from)) != -1:
                paren: int = idx + len(name) + 1
                search_from = paren
                if line[paren:].startswith(f"{keyword}="):
                    continue  # already converted
                depth, end = 1, -1
                for j in range(paren, len(line)):
                    depth += (line[j] == "(") - (line[j] == ")")
                    if depth == 0:
                        end = j
                        break
                if end == -1:
                    continue  # call not closed on this line -- leave it
                if _snippet_is_single_arg(line[idx : end + 1], keyword):
                    # Store the name-end column (before '('); apply() re-finds the
                    # '(' via _open_paren_col, matching the AST pass's convention.
                    edits.append((lineno, idx + len(name), keyword))
    return edits


def _convertible(node: ast.AST) -> tuple[str, str] | None:
    """Return (func_name, keyword) if this node is a convertible call, else None."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in TARGETS
        and len(node.args) == 1
        and not node.keywords
    ):
        return node.func.id, TARGETS[node.func.id]
    return None


def _open_paren_col(line: str, after_col: int) -> int:
    """Column of the '(' at or after after_col on this line."""
    return line.index("(", after_col) + 1


def convert_file(path: pathlib.Path) -> int:
    """Rewrite one file in place; return the number of call sites converted."""
    source: str = path.read_text()
    tree: ast.Module = ast.parse(source)
    # (lineno, col_just_after_open_paren, keyword) for each convertible call.
    edits: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        hit: tuple[str, str] | None = _convertible(node)
        if hit is None:
            continue
        _, keyword = hit
        func = node.func
        assert isinstance(func, ast.Name) and func.end_lineno is not None
        # The '(' sits at or just after the end of the function name; the text
        # pass re-finds it so a trailing space (``translate (x)``) is tolerated.
        edits.append((func.end_lineno, func.end_col_offset, keyword))

    lines: list[str] = source.splitlines(keepends=True)
    edits.extend(_doctest_edits(lines))

    if not edits:
        return 0
    # Group edits by line; apply right-to-left so earlier columns don't shift.
    by_line: dict[int, list[tuple[int, str]]] = {}
    for lineno, after_col, keyword in edits:
        by_line.setdefault(lineno, []).append((after_col, keyword))
    for lineno, hits in by_line.items():
        line: str = lines[lineno - 1]
        for after_col, keyword in sorted(hits, reverse=True):
            paren: int = _open_paren_col(line, after_col)
            line = line[:paren] + f"{keyword}=" + line[paren:]
        lines[lineno - 1] = line

    path.write_text("".join(lines))
    return len(edits)


def main(argv: list[str]) -> int:
    paths: list[pathlib.Path] = []
    for arg in argv:
        p: pathlib.Path = pathlib.Path(arg)
        paths.extend(sorted(p.rglob("*.py")) if p.is_dir() else [p])
    total: int = 0
    for path in paths:
        n: int = convert_file(path)
        if n:
            print(f"{path}: converted {n} call(s)")
            total += n
    print(f"total converted: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
