"""List each top-level engine definition of the Code-the-Classics games, by variant.

For every game file under ``ports/codetheclassics/vol*/``, the definitions above
the ``# ===== game code`` banner are compared by exact source text. Each name is
printed with its section, and with one line per distinct text: the number of
lines in that text and the games that carry it.

Usage (from anywhere)::

    python tasks/adhoc/pgzero-gl-step3-reextract-library/engine_defs.py [name ...]

With names, the differing variants of those definitions are also printed as a
unified diff against the most common variant.
"""

import ast
import difflib
import hashlib
import pathlib
import sys
from collections import defaultdict
from dataclasses import dataclass

REPO: pathlib.Path = pathlib.Path(__file__).resolve().parents[3]
GAME_CODE_BANNER: str = "# ===== game code"


@dataclass(frozen=True, slots=True)
class Definition:
    """One top-level engine definition in one game file."""

    game: str
    section: str
    name: str
    text: str


def section_of(lines: list[str], lineno: int) -> str:
    """Return the ``# ===== ... =====`` banner text above ``lineno``.

    Args:
        lines: The file's lines.
        lineno: A 1-based line number.

    Returns:
        The banner's title, or ``"(header)"`` above the first banner.
    """
    banners: list[str] = [
        line.strip("# =\n")
        for line in lines[:lineno]
        if line.startswith("# =====")
    ]
    return banners[-1] if banners else "(header)"


def names_bound(node: ast.stmt) -> list[str]:
    """Return the names a top-level statement defines.

    Args:
        node: A module-level statement.

    Returns:
        The class/function name, or the assigned names; empty for any other
        statement.
    """
    match node:
        case ast.ClassDef(name=name) | ast.FunctionDef(name=name):
            return [name]
        case ast.AnnAssign(target=ast.Name(id=name)):
            return [name]
        case ast.Assign(targets=targets):
            return [t.id for t in targets if isinstance(t, ast.Name)]
        case ast.If() | ast.Try():
            return [
                f"<{type(node).__name__.lower()}@{node.lineno}>"
            ]
        case _:
            return []


def engine_definitions(path: pathlib.Path) -> list[Definition]:
    """Collect the engine-half definitions of one game file.

    Args:
        path: A game ``.py`` file.

    Returns:
        One ``Definition`` per bound name above the game-code banner.
    """
    source: str = path.read_text()
    lines: list[str] = source.splitlines(keepends=True)
    end: int = next(
        i for i, line in enumerate(lines, 1) if line.startswith(GAME_CODE_BANNER)
    )
    return [
        Definition(
            game=path.stem,
            section=section_of(lines, node.lineno),
            name=name,
            text=ast.get_source_segment(source, node, padded=False) or "",
        )
        for node in ast.parse(source).body
        if node.lineno < end
        for name in names_bound(node)
    ]


def main(selected: list[str]) -> None:
    """Print the variant table, then diffs for the selected names.

    Args:
        selected: Definition names whose variants to diff.
    """
    games: list[pathlib.Path] = sorted(
        REPO.glob("ports/codetheclassics/vol*/*/*.py")
    )
    by_name: defaultdict[str, list[Definition]] = defaultdict(list)
    for path in games:
        for definition in engine_definitions(path):
            by_name[definition.name].append(definition)
    for name, definitions in sorted(
        by_name.items(), key=lambda item: (item[1][0].section, item[0])
    ):
        variants: defaultdict[str, list[Definition]] = defaultdict(list)
        for definition in definitions:
            variants[definition.text].append(definition)
        print(f"{name}  [{definitions[0].section}]  in {len(definitions)}")
        for text, carriers in sorted(
            variants.items(), key=lambda item: -len(item[1])
        ):
            digest: str = hashlib.sha1(text.encode()).hexdigest()[:7]
            print(
                f"    {digest} {text.count(chr(10)) + 1:4d} lines: "
                + " ".join(d.game for d in carriers)
            )
        if name in selected:
            ordered: list[tuple[str, list[Definition]]] = sorted(
                variants.items(), key=lambda item: -len(item[1])
            )
            base_text: str = ordered[0][0]
            for text, carriers in ordered[1:]:
                sys.stdout.writelines(
                    difflib.unified_diff(
                        base_text.splitlines(keepends=True),
                        text.splitlines(keepends=True),
                        fromfile=ordered[0][1][0].game,
                        tofile=carriers[0].game,
                        n=1,
                    )
                )


if __name__ == "__main__":
    main(sys.argv[1:])
