"""Point the Code-the-Classics games at the shared ``pgzero_gl`` engine modules.

For each game named on the command line (``boing``, ``leadingedge``, ...; none
means all eleven files), this:

1. replaces the whole ``# ===== engine: audio =====`` section with a short one
   that builds the game's ``music`` from the shared mixer;
2. deletes the engine definitions that now live in the library -- ``Image``,
   ``_Loader`` and the GL helpers -- and rebuilds ``images``/``sounds`` with the
   library's root-taking ``Loader``;
3. renames the GL helper call sites (``_link_program()`` ->
   ``link_program(_VERT, _FRAG)``, ``_make_buffer(`` -> ``make_buffer(``);
4. adds the library imports after the ``from PIL`` imports.

Imports the game no longer uses are left for ``ruff check --fix`` (F401) to
drop. Idempotent: a converted file is left unchanged.

Usage (from anywhere)::

    python tasks/adhoc/pgzero-gl-step3-reextract-library/use_library.py [game ...]
"""

import ast
import pathlib
import re
import sys

REPO: pathlib.Path = pathlib.Path(__file__).resolve().parents[3]
AUDIO_BANNER: str = "# ===== engine: audio ====="
GAME_CODE_BANNER: str = "# ===== game code"
#: Top-level engine definitions deleted from each game.
MOVED: frozenset[str] = frozenset(
    {
        "Image",
        "_Loader",
        "images",
        "sounds",
        "ortho_pixels",
        "_compile",
        "_link_program",
        "GLBuffer",
        "_make_buffer",
    }
)
AUDIO_SECTION: str = """\
# ===== engine: audio =====
#
# Sound effects and the music track play through the shared software mixer,
# modelviewprojection.pgzero_gl.audio (one miniaudio device, best effort:
# silent when no device opens). The game only says where its music/ is.

music: Music = Music(ASSET_ROOT)


"""
LOADERS: str = """\
images: Loader[Image] = Loader(
    ASSET_ROOT, "images", ("png", "gif", "jpg", "jpeg", "bmp"), Image.load
)
sounds: Loader[Sound] = Loader(ASSET_ROOT, "sounds", ("ogg", "wav", "oga"), Sound)
"""
IMPORT_AUDIO: str = (
    "from modelviewprojection.pgzero_gl.audio import Music, Sound, shutdown_audio\n"
)
IMPORT_GL: str = (
    "from modelviewprojection.pgzero_gl.gl import (\n"
    "    GLBuffer,\n    link_program,\n    make_buffer,\n    ortho_pixels,\n)\n"
)
IMPORT_RESOURCES: str = (
    "from modelviewprojection.pgzero_gl.resources import Image, Loader\n"
)


def replace_audio_section(lines: list[str]) -> list[str]:
    """Swap the audio section, banner to next banner, for ``AUDIO_SECTION``.

    Args:
        lines: The file's lines (with line ends).

    Returns:
        The lines with the section replaced; unchanged if already replaced.
    """
    start: int = lines.index(AUDIO_BANNER + "\n")
    end: int = next(
        i for i in range(start + 1, len(lines)) if lines[i].startswith("# =====")
    )
    if "".join(lines[start:end]) == AUDIO_SECTION:
        return lines
    return lines[:start] + AUDIO_SECTION.splitlines(keepends=True) + lines[end:]


def node_names(node: ast.stmt) -> set[str]:
    """Return the names a top-level class, function or assignment binds.

    Args:
        node: A module-level statement.

    Returns:
        The bound names; empty for any other statement.
    """
    match node:
        case ast.ClassDef(name=name) | ast.FunctionDef(name=name):
            return {name}
        case ast.AnnAssign(target=ast.Name(id=name)):
            return {name}
        case ast.Assign(targets=targets):
            return {t.id for t in targets if isinstance(t, ast.Name)}
        case _:
            return set()


def delete_moved(source: str) -> str:
    """Delete the moved definitions above the game code; put the loaders back.

    Each deleted span runs from the definition's first decorator, plus any
    comment lines directly above it, to its last line. The new ``images`` /
    ``sounds`` loaders go where the old ``images`` assignment was.

    Args:
        source: The file's text.

    Returns:
        The rewritten text.
    """
    lines: list[str] = source.splitlines(keepends=True)
    end_of_engine: int = next(
        i for i, line in enumerate(lines, 1) if line.startswith(GAME_CODE_BANNER)
    )
    spans: list[tuple[int, int, str]] = []
    for node in ast.parse(source).body:
        names: set[str] = node_names(node)
        if node.lineno >= end_of_engine or not names & MOVED:
            continue
        first: int = min(
            [node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])]
        )
        while lines[first - 2].lstrip().startswith("#") and not lines[
            first - 2
        ].startswith("# ====="):
            first -= 1
        assert node.end_lineno is not None
        spans.append((first, node.end_lineno, "images" if "images" in names else ""))
    for first, last, role in sorted(spans, reverse=True):
        lines[first - 1 : last] = [LOADERS] if role == "images" else []
    return "".join(lines)


def add_imports(source: str) -> str:
    """Insert the library imports after the last ``from PIL`` import.

    Args:
        source: The file's text.

    Returns:
        The text with any missing library import added.
    """
    wanted: list[str] = [IMPORT_AUDIO, IMPORT_RESOURCES]
    if "link_program(" in source:
        wanted.insert(1, IMPORT_GL)
    missing: str = "".join(i for i in wanted if i not in source)
    if not missing:
        return source
    pil: list[re.Match[str]] = list(re.finditer(r"^from PIL import .*\n", source, re.M))
    at: int = pil[-1].end()
    return source[:at] + missing + source[at:]


def convert(path: pathlib.Path) -> bool:
    """Convert one game file in place.

    Args:
        path: The game's ``.py`` file.

    Returns:
        Whether the file changed.
    """
    before: str = path.read_text()
    after: str = add_imports(
        delete_moved(
            "".join(replace_audio_section(before.splitlines(keepends=True)))
        )
        .replace("_link_program()", "link_program(_VERT, _FRAG)")
        .replace("_make_buffer(", "make_buffer(")
    )
    path.write_text(after)
    return after != before


def main(games: list[str]) -> None:
    """Convert the named games (all of them when none is named).

    Args:
        games: Game file stems.
    """
    paths: list[pathlib.Path] = sorted(
        REPO.glob("ports/codetheclassics/vol*/*/*.py")
    )
    for path in paths:
        if games and path.stem not in games:
            continue
        print(f"{'changed' if convert(path) else 'unchanged'}: {path.stem}")


if __name__ == "__main__":
    main(sys.argv[1:])
