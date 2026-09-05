#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Codemod for tasks/ctc-factory-classmethods.md: move each Code-the-Classics
# game's free GL-resource factory functions onto their dataclasses as
# @classmethods, and rename every call site.
#
#   make_renderer(w, h)  -> Renderer.create(w, h)   (Renderer1x in boing_gl1)
#   load_image(path)     -> Image.load(path)
#   image_from_rgba(arr) -> Image.from_rgba(arr)
#   make_surface(...)    -> Surface.create(...)
#   mask_from_image(...) -> Mask.from_image(...)
#
# How: `ast` locates each top-level function and its target class (the class
# named by the function's return annotation); the function's source lines are
# lifted out, re-indented under the class as its last method with `cls` as the
# first parameter and `return <Class>(` rewritten to `return cls(`; then the
# call sites are renamed textually. Edits are applied bottom-up so earlier line
# numbers stay valid. Idempotent: a file with no factory functions left is
# returned unchanged (run it twice; the second run must report 0 changes).
#
# Usage (repo root): python tasks/adhoc/ctc-factory-classmethods/factory_classmethods.py <game.py>...
# Then `ruff format` the files (blank lines around the moved defs are left to it).

import ast
import re
import sys
from pathlib import Path

#: free function -> the classmethod's name (the class comes from the return type)
RENAMES: dict[str, str] = {
    "make_renderer": "create",
    "load_image": "load",
    "image_from_rgba": "from_rgba",
    "make_surface": "create",
    "mask_from_image": "from_image",
}


def convert(src: str) -> tuple[str, int]:
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    classes: dict[str, ast.ClassDef] = {
        n.name: n for n in tree.body if isinstance(n, ast.ClassDef)
    }
    funcs = [
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name in RENAMES
    ]
    if not funcs:
        return src, 0
    # (line index to insert at, method text) / (start, end) spans to delete
    inserts: list[tuple[int, str]] = []
    deletes: list[tuple[int, int]] = []
    qualified: dict[str, str] = {}  # old call name -> "Class.method"
    for f in funcs:
        assert isinstance(f.returns, ast.Name), f.name
        cls = classes[f.returns.id]
        new = RENAMES[f.name]
        qualified[f.name] = f"{cls.name}.{new}"
        body = lines[f.lineno - 1 : f.end_lineno]
        head = body[0]
        m = re.match(rf"def {f.name}\((.*)$", head)
        assert m, head
        params = m.group(1)
        body[0] = f"def {new}(cls, {params}\n" if params.strip() and not params.startswith(")") else f"def {new}(cls{params}\n"
        text = "".join(body)
        # the factory's own constructor call -> cls(...); a sibling factory it
        # calls (load_image -> image_from_rgba) -> cls.<method>(...)
        text = re.sub(rf"\breturn {cls.name}\(", "return cls(", text)
        for other, other_new in RENAMES.items():
            if other != f.name and other in text:
                text = re.sub(rf"\b{other}\(", f"cls.{other_new}(", text)
        method = "\n    @classmethod\n" + "".join(
            ("    " + ln if ln.strip() else ln) for ln in text.splitlines(keepends=True)
        )
        inserts.append((cls.end_lineno, method))
        deletes.append((f.lineno - 1, f.end_lineno))
    # apply bottom-up: deletes and inserts sorted by position, descending
    edits = [(s, e, "") for s, e in deletes] + [(i, i, t) for i, t in inserts]
    for s, e, t in sorted(edits, key=lambda x: (x[0], x[1]), reverse=True):
        lines[s:e] = [t] if t else []
    out = "".join(lines)
    # call sites and cross-references (the definitions are already gone)
    for old, q in qualified.items():
        out = re.sub(rf"(?<![\w.]){old}\(", f"{q}(", out)
        out = re.sub(rf"(?<![\w.]){old}\b(?!\()", q, out)  # bare references, e.g. _Loader(..., load_image)
        out = out.replace(f":func:`{q}`", f":meth:`{q}`")
    # the "build one with ..." contract on the class docstrings
    out = re.sub(
        r"Built by\s+:meth:`(\w+)\.create` once the GL context exists\.",
        lambda m: f"Build one with\n    :meth:`{m.group(1)}.create` once the GL context exists; the constructor takes\n    already-linked GL objects (tests, or another backend, may pass their own).",
        out,
    )
    return out, len(funcs)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = Path(arg)
        new, n = convert(p.read_text())
        if n:
            p.write_text(new)
        print(f"{p}: {n} factories moved")
