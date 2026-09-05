#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Step 1 of the pgzero_gl inline/strip/re-extract initiative
# (tasks/pgzero-gl-step1-inline-per-game.md): inline the whole pgzero_gl shim
# into the TOP of a single Code-the-Classics game file, so the game becomes one
# self-contained module read top-to-bottom, like a course demo. Faithful and
# behavior-preserving -- no logic changes; proven per game by a frame-identity
# trace (trace_identity.py).
#
# What it does, and the four wrinkles it handles:
#   1. Concatenate the 18 shim modules in dependency order (leaf types first;
#      audio before resources because `sounds = _Loader(make=audio.Sound)` runs
#      Sound at import; singletons after their classes).
#   2. IMPORTS: strip each module's `from __future__` and `from .` intra-package
#      imports; collect every EXTERNAL import (numpy/OpenGL/glfw/PIL/gacalc/
#      miniaudio/stdlib) and emit them ONCE at the top (else E402), de-duped by
#      `ruff --fix`.
#   3. NAMESPACES: the shim referenced three of its modules by name -- `context.`,
#      `audio.`, `_text.` (screen does `from . import text as _text`). Once
#      flattened into one namespace, bind each to this module itself
#      (`context = audio = _text = sys.modules[__name__]`); attribute get AND set
#      then reach the module globals with no `global` keyword. A game that imports
#      a shim SUBMODULE as a namespace (vol2: `joystick`, `draw as gldraw`,
#      `surface`, ...) gets the same self-alias. Valid because the 18 modules have
#      no conflicting top-level names (only `RectLike`, an identical alias).
#      Aliased name imports (`from .resources import Image as GLImage`) become a
#      plain `GLImage = Image` assignment.
#   4. COLLISIONS: a game's framework callbacks (`draw`, `update`) can share a
#      name with a shim top-level def (text.py's module-level `draw`). The game's
#      wins (it's appended last), which would shadow the shim's. So each
#      game-vs-shim top-level collision renames the SHIM's def/class (module-level
#      only -- never an indented method like `Actor.draw`) to `_pgz_<name>` and
#      rewrites its `context./audio./_text.`-qualified references to match.
#
# Usage (repo root as CWD):
#   python tasks/adhoc/pgzero-gl-inline/inline_game.py <game.py> [<out.py>]

import ast
import pathlib
import re
import sys

SHIM_DIR = pathlib.Path("src/modelviewprojection/pgzero_gl")
SHIM_ORDER = [
    "_types", "geometry", "context", "audio", "resources", "renderer",
    "renderer_gl1", "surface", "draw", "mask", "transform", "text", "screen",
    "actor", "input", "joystick", "runner", "__init__",
]
# Shim modules a GAME imports as a `.`-qualified namespace (NOT the singleton
# objects screen/keyboard/... which the game imports by value).
GAME_NAMESPACE_MODULES = {
    "joystick", "draw", "surface", "mask", "transform", "resources",
}
PKG = "modelviewprojection.pgzero_gl"


def top_names(tree: ast.Module) -> set[str]:
    """Module-level def/class/assignment names."""
    out: set[str] = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.Assign):
            out.update(t.id for t in n.targets if isinstance(t, ast.Name))
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
    return out


def strip_leading_hashes(lines: list[str]) -> list[str]:
    i = 0
    while i < len(lines) and (lines[i].startswith("#") or lines[i].strip() == ""):
        i += 1
    return lines[i:]


def analyze(src: str, is_game: bool):
    """Return (external_imports, namespaces, aliases, body_text)."""
    tree = ast.parse(src)
    ext: list[str] = []
    namespaces: list[str] = []
    aliases: list[tuple[str, str]] = []  # (local, original)  ->  local = original
    drop: set[int] = set()

    for node in tree.body:
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        for ln in range(node.lineno, (node.end_lineno or node.lineno) + 1):
            drop.add(ln)
        if isinstance(node, ast.Import):
            ext.append("import " + ", ".join(
                a.name + (f" as {a.asname}" if a.asname else "") for a in node.names))
            continue
        # ImportFrom
        if node.module == "__future__":
            continue
        if node.level > 0:  # intra-package: from . / from .mod
            if node.module is None:  # from . import a, b as c   (namespaces)
                namespaces.extend(a.asname or a.name for a in node.names)
            else:  # from .mod import Name [as Z]
                for a in node.names:
                    if a.asname and a.asname != a.name:
                        aliases.append((a.asname, a.name))
            continue
        if is_game and node.module and (
            node.module == PKG or node.module.startswith(PKG + ".")):
            sub = node.module[len(PKG):].lstrip(".")
            for a in node.names:
                local = a.asname or a.name
                if not sub and a.name in GAME_NAMESPACE_MODULES:
                    namespaces.append(local)          # `import joystick`
                elif a.asname and a.asname != a.name:
                    aliases.append((local, a.name))   # `Image as GLImage`
                # else: a plain top-level name -- flattens, no action
            continue
        # external from-import
        ext.append(f"from {node.module} import " + ", ".join(
            a.name + (f" as {a.asname}" if a.asname else "") for a in node.names))

    body_lines = [ln for i, ln in enumerate(src.splitlines(), 1) if i not in drop]
    body = "\n".join(strip_leading_hashes(body_lines)).strip("\n")
    # Function-local / TYPE_CHECKING deferred relative imports are INDENTED, so
    # the top-level ast pass above didn't drop them. The names they import are
    # top-level now, so neutralize each to `pass` (keeps its block syntactically
    # valid -- an emptied `if TYPE_CHECKING:` would be a syntax error).
    body = re.sub(r"^(\s+)from \.[^\n]*$", r"\1pass", body, flags=re.MULTILINE)
    return ext, namespaces, aliases, body


def rename_collisions(shim_text: str, names: set[str]) -> str:
    """Rename module-level shim `def/class <name>` (never indented methods) and
    its context./audio./_text.-qualified refs to `_pgz_<name>`."""
    for c in sorted(names):
        shim_text = re.sub(rf"^(def|class) {c}\b", rf"\1 _pgz_{c}",
                           shim_text, flags=re.MULTILINE)
        shim_text = re.sub(rf"\b(?:context|audio|_text)\.{c}\b",
                           f"_pgz_{c}", shim_text)
    return shim_text


def main() -> None:
    game_path = pathlib.Path(sys.argv[1])
    out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else game_path

    ext_all: list[str] = []
    namespaces: list[str] = []
    aliases: list[tuple[str, str]] = []
    shim_sections: list[str] = []
    shim_names: set[str] = set()

    for mod in SHIM_ORDER:
        src = (SHIM_DIR / f"{mod}.py").read_text()
        shim_names |= top_names(ast.parse(src))
        e, n, a, body = analyze(src, is_game=False)
        ext_all += e
        namespaces += n
        aliases += a
        shim_sections.append(f"\n# ===== pgzero_gl/{mod}.py =====\n\n{body}")

    game_src = game_path.read_text()
    game_names = top_names(ast.parse(game_src))
    e, n, a, game_body = analyze(game_src, is_game=True)
    ext_all += e
    namespaces += n
    aliases += a

    # De-dup, preserving determinism.
    ext_all = sorted(set(ext_all))
    namespaces = sorted(set(namespaces))
    aliases = sorted(set(aliases))
    collisions = game_names & shim_names

    shim_text = rename_collisions("\n".join(shim_sections), collisions)
    # Any alias whose target got renamed by a collision must follow suit.
    aliases = [(loc, f"_pgz_{orig}" if orig in collisions else orig)
               for loc, orig in aliases]

    header = "\n".join((SHIM_DIR / "_types.py").read_text().splitlines()[:6])
    out = [
        header,
        '"""',
        f"{game_path.stem} -- a Code-the-Classics game with pgzero_gl inlined.",
        "",
        "The pgzero_gl engine is pasted in full at the top (step 1 of the",
        "inline/strip/re-extract initiative); the game code follows below.",
        '"""',
        "from __future__ import annotations",
        "",
        "import sys",
        "",
        *ext_all,
        "",
        "# The inlined pgzero_gl modules referenced each other by module name;",
        "# every name is now top-level here, so bind those namespaces to this",
        "# module itself (attribute get/set reaches the module globals). A step-1",
        "# mechanical artifact -- step 2 dissolves it when the game owns the loop.",
        f"{' = '.join(namespaces)} = sys.modules[__name__]",
    ]
    out.append(shim_text)
    # Aliases (e.g. GLImage = Image) go AFTER the shim, where their target names
    # are defined -- emitting them at the top would NameError at import.
    if aliases:
        out.append("\n# ===== inlined-import aliases =====\n")
        out += [f"{loc} = {orig}" for loc, orig in aliases]
    out.append("\n# ===== game code =====\n")
    out.append(game_body)

    out_path.write_text("\n".join(out) + "\n")
    n_lines = len(out_path.read_text().splitlines())
    print(f"wrote {out_path} ({n_lines} lines)")
    print(f"  namespaces self-aliased: {namespaces}")
    print(f"  intra aliases: {aliases}")
    print(f"  game<->shim collisions renamed: {sorted(collisions)}")


if __name__ == "__main__":
    main()
