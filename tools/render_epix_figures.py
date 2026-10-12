#!/usr/bin/env python3
"""Render the book's ePiX figures (``book/figures/epix/*.py``) for Sphinx.

Each figure is a jupytext percent-format Python file, written the way epix-mirror's
own ``notebooks/`` are: it builds a scene with the ``epix`` package and leaves the
result in a module-level ``fig`` (an ``epix.Figure``). Figures may drive mvp's own
taught transforms (``modelviewprojection.mathutils``) so a picture is produced by the
exact functions its chapter teaches. This script runs each file in a **fresh
interpreter** (libepix keeps global drawing state with no public reset, so figures
must not share a process), then writes next to each other under
``book/docs/_static/epix/``:

- ``<name>.pdf`` -- ``elaps --pdf`` over the figure's eepic text, for the LuaLaTeX
  build (Sphinx picks it for the ``latex`` builder);
- ``<name>.png`` -- the figure's lazily rasterized PNG (``elaps`` -> eps -> ``gs``),
  for the HTML builder. ghostscript's ``pngalpha`` leaves the background transparent,
  which reads badly on a dark-mode page; so every PNG is flattened (ImageMagick) onto
  ``DEFAULT_BACKGROUND`` (``#f2f2f2``), or onto a module-level ``BACKGROUND``
  (``"#rrggbb"``) a figure defines to override it.

A page then references the figure as ``.. figure:: _static/epix/<name>.*`` and Sphinx
chooses the format per builder. Run from the repo root, inside the image. Every figure
is attempted; the exit status is nonzero if any failed. Adapted from the sibling
geometricalgebra repo (github.com/billsix/geometricalgebra).

Usage: ``python tools/render_epix_figures.py [--dpi N] [NAME ...]``
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO: Path = Path(__file__).resolve().parents[1]
FIGURES: Path = REPO / "book" / "figures" / "epix"
OUT: Path = REPO / "book" / "docs" / "_static" / "epix"

# Every figure's PNG is flattened onto this unless the figure overrides it with a
# module-level BACKGROUND -- so no figure renders with a transparent background (which
# reads badly on a dark-mode HTML page).
DEFAULT_BACKGROUND: str = "#f2f2f2"

# Runs inside the fresh interpreter: execute the figure file, then emit its eepic
# and PNG to the paths given on the command line.
_CHILD: str = r"""
import runpy, sys
src, eepic_out, png_out, dpi = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
g = runpy.run_path(src)
fig = g["fig"]
with open(eepic_out, "w") as f:
    f.write(fig.eepic)
fig.dpi = dpi
with open(png_out, "wb") as f:
    f.write(fig.png)
print(g.get("BACKGROUND", ""), end="")
"""


def eepic_to_pdf(eepic: Path, pdf: Path) -> None:
    """``elaps --pdf`` in a scratch dir (elaps litters its cwd with TeX transcripts)."""
    with tempfile.TemporaryDirectory() as d:
        scratch: Path = Path(d) / eepic.name
        shutil.copy(eepic, scratch)
        subprocess.run(
            ["elaps", "--pdf", "-o", str(pdf), scratch.name],
            cwd=d,
            check=True,
            capture_output=True,
            text=True,
        )


def flatten_png(png: Path, background: str) -> None:
    """Replace the PNG's transparent background with a solid colour (ImageMagick)."""
    magick: str | None = shutil.which("magick") or shutil.which("convert")
    if magick is None:
        raise FileNotFoundError(
            "ImageMagick (magick/convert) is needed to flatten PNGs"
        )
    subprocess.run(
        [magick, str(png), "-background", background, "-flatten", str(png)],
        check=True,
        capture_output=True,
    )


def render_one(src: Path, dpi: int) -> None:
    """Run one figure file in a fresh process and write its .pdf and .png."""
    name: str = src.stem.replace("_", "-")
    pdf: Path = OUT / f"{name}.pdf"
    png: Path = OUT / f"{name}.png"
    with tempfile.TemporaryDirectory() as d:
        eepic: Path = Path(d) / f"{name}.eepic"
        child: subprocess.CompletedProcess[str] = subprocess.run(
            [
                sys.executable,
                "-c",
                _CHILD,
                str(src),
                str(eepic),
                str(png),
                str(dpi),
            ],
            check=True,
            cwd=src.parent,
            capture_output=True,
            text=True,
        )
        # the figure's own BACKGROUND, or the default so nothing is left transparent
        background: str = child.stdout.strip() or DEFAULT_BACKGROUND
        flatten_png(png, background)
        eepic_to_pdf(eepic, pdf)
    print(
        f"rendered {src.relative_to(REPO)} -> {pdf.relative_to(REPO)}, {png.name}"
    )


def main() -> int:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(
        "--dpi", type=int, default=200, help="PNG resolution (default 200)"
    )
    parser.add_argument(
        "names", nargs="*", help="figure stems to render (default: all)"
    )
    args: argparse.Namespace = parser.parse_args()

    if shutil.which("elaps") is None:
        print(
            "render_epix_figures: `elaps` not found -- this image was built without\n"
            "ePiX (USE_EPIX=0); rebuild with `make image` (USE_EPIX defaults on).",
            file=sys.stderr,
        )
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    sources: list[Path] = sorted(
        p for p in FIGURES.glob("*.py") if not p.name.startswith("_")
    )  # _-prefixed files are shared helpers, not figures
    if args.names:
        wanted: set[str] = set(args.names)
        sources = [
            p
            for p in sources
            if p.stem in wanted or p.stem.replace("_", "-") in wanted
        ]
    status: int = 0
    for src in sources:
        try:
            render_one(src, args.dpi)
        except (
            subprocess.CalledProcessError
        ) as exc:  # keep going; report all the red
            status = 1
            print(f"FAILED {src.relative_to(REPO)}: {exc}", file=sys.stderr)
            if exc.stderr:
                print(exc.stderr[-2000:], file=sys.stderr)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
