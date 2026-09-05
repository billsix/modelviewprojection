#!/usr/bin/env python3
"""Generate boing_gl1.py from boing.py -- the GL 1.x (fixed-function) companion.

Run from the repo root:

    python tasks/adhoc/pgzero-gl-boing-gl14/make_boing_gl1.py

boing_gl1.py is the SAME game as boing.py, drawn with the OpenGL 1.x
fixed-function pipeline (a 2.1 compatibility context + glOrtho + glBegin/glEnd
immediate mode) instead of 3.3 core + shaders. This script derives it from
boing.py by swapping exactly two regions and rewriting the module docstring:

  1. The renderer + its 3.3-only support code -- the matrix helpers
     (_identity/_translate/_scale/ortho_pixels), the GLSL shader strings, the
     _compile() helper, and `class Renderer` -- are removed and replaced by the
     fixed-function `class Renderer1x`, read verbatim from the shared shim at
     src/modelviewprojection/pgzero_gl/renderer_gl1.py (its interface is
     identical, so blit()/draw_sprite() and the game code below are untouched).
  2. The __main__ window/context setup: 3.3-core hints -> 2.1-compat hints, drop
     the core-profile VAO bind, and construct Renderer1x instead of Renderer.

Everything else (game logic, dataclasses, Image.gl_texture texture upload,
loaders, audio, the loop body) is copied unchanged. The transform is guarded by
asserts: if any anchor text drifts in boing.py, the script fails loudly rather
than emitting a subtly-wrong file. It reads boing.py fresh and writes
boing_gl1.py, so re-running reproduces the same output.
"""

from __future__ import annotations

import pathlib

# Repo-relative paths (script is run from the repo root).
BOING = pathlib.Path("ports/codetheclassics/vol1/boing/boing.py")
BOING_GL1 = pathlib.Path("ports/codetheclassics/vol1/boing/boing_gl1.py")
RENDERER_GL1 = pathlib.Path(
    "src/modelviewprojection/pgzero_gl/renderer_gl1.py"
)

# The new module docstring for boing_gl1.py (replaces boing.py's whole one).
NEW_DOCSTRING = '''"""
boing_gl1 -- the OpenGL 1.x (fixed-function) rendering of boing.

A study companion to boing.py: the SAME game, drawn with the OpenGL 1.x
fixed-function pipeline (a 2.1 compatibility context + glOrtho + glBegin/glEnd
immediate mode + fixed-function texturing) instead of 3.3 core + shaders. Diff
this file against boing.py to see exactly what changes between the two pipelines
-- the game logic is identical; only the renderer (Renderer1x, below) and the
window/context setup differ. The fixed-function era here is the one the book
introduces at demo19 (glMatrixMode / glOrtho / glBegin / glEnable(GL_TEXTURE_2D)).
"""'''

# The inlined renderer SECTION header (banner + module docstring) came from the
# 3.3-core renderer.py; rewrite both to describe the fixed-function back end, so
# boing_gl1's prose matches its actual renderer (and no stale :func:`ortho_pixels`
# / shader references dangle).
RENDERER_BANNER_OLD = "# ===== pgzero_gl/renderer.py ====="
RENDERER_BANNER_NEW = (
    "# ===== pgzero_gl/renderer_gl1.py (fixed-function OpenGL 1.x) ====="
)

RENDERER_DOC_OLD = '''"""The OpenGL 3.3 core back end -- textured quads in pgzero pixel space.

Part of the ModelViewProjection "Code the Classics" port (originals (c)
Raspberry Pi Press and authors).

* Repo: https://github.com/raspberrypipress/Code-the-Classics-Vol1
* Book: https://magazine.raspberrypi.com/books/code-the-classics-vol-I-2ed

PyGame Zero draws by blitting CPU surfaces in a top-left-origin, y-down pixel
coordinate system. We reproduce that exactly with an orthographic projection
(:func:`ortho_pixels`) and textured quads, so the ported game code keeps its
original pixel coordinates unchanged. One shader program does both jobs --
textured sprites and flat-colour primitives -- switched by the ``uUseTex``
uniform and multiplied by a ``uTint`` colour. :class:`pgzero_gl.renderer_gl1` is
the fixed-function sibling that draws the same pixels for old GL stacks.

Matrices are row-major numpy, uploaded with ``transpose=GL_TRUE``; all
coordinates are pgzero pixels: ``(0, 0)`` top-left, ``+x`` right, ``+y`` down.
"""'''
RENDERER_DOC_NEW = '''"""The OpenGL 1.x fixed-function back end -- textured quads in pgzero pixel space.

Part of the ModelViewProjection "Code the Classics" port (originals (c)
Raspberry Pi Press and authors).

* Repo: https://github.com/raspberrypipress/Code-the-Classics-Vol1
* Book: https://magazine.raspberrypi.com/books/code-the-classics-vol-I-2ed

PyGame Zero draws by blitting CPU surfaces in a top-left-origin, y-down pixel
coordinate system. We reproduce that exactly with a fixed-function orthographic
projection (``glOrtho``) and immediate-mode textured quads (``glBegin``/``glEnd``
+ ``glTexCoord2f``/``glVertex2f``), so the ported game code keeps its original
pixel coordinates unchanged. Tinting uses the fixed-function texture environment
(``GL_MODULATE``: texture * glColor). This is the GL 1.x rendering of boing;
boing.py is the 3.3-core + shaders sibling that draws the same pixels.
"""'''

# A short comment banner introducing the inlined fixed-function renderer.
RENDERER1X_BANNER = """\
# ---------------------------------------------------------------------------
# Fixed-function OpenGL 1.x renderer -- a drop-in for the 3.3-core Renderer.
#
# Draws with the OpenGL 1.x FIXED-FUNCTION pipeline: glOrtho for the pixel-space
# projection, glBegin/glEnd immediate mode + glTexCoord2f/glVertex2f for the
# textured quad, and GL_MODULATE (texture * glColor) for tinting -- no shaders,
# no VAO. The interface is identical to the 3.3 Renderer, so blit()/draw_sprite()
# and all the game code below are unchanged. The texture upload
# (Image.gl_texture, above) is glGenTextures/glTexImage2D, which is
# 1.x-compatible. The 3.3 renderer (boing.py) and this one draw the same pixels.
# ---------------------------------------------------------------------------
"""

# --- anchor strings in boing.py (asserted unique / present) ----------------

# Region 1: delete from the "Matrix helpers" banner through everything up to
# (but not including) the _rgba() helper, which both renderers share.
REGION1_START = (
    "# ---------------------------------------------------------------------------\n"
    "# Matrix helpers (row-major numpy; uploaded with transpose=GL_TRUE)."
)
REGION1_END = "def _rgba(color: Any) -> tuple[float, float, float, float]:"

# Region 2a: the window-creation hints (3.3 core -> 2.1 compat).
HINTS_OLD = """\
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
    window = glfw.create_window(WIDTH, HEIGHT, TITLE, None, None)"""
HINTS_NEW = """\
    # OpenGL 2.1 compatibility context: 2.1 predates the core/compat profile
    # split, so request version 2.1 with the default (ANY) profile and no
    # forward-compat. The fixed-function pipeline this game draws with (glOrtho
    # + glBegin) is not available in a 3.3 core context -- that is the whole
    # point of this GL 1.x variant. See boing.py for the 3.3-core original.
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(WIDTH, HEIGHT, TITLE, None, None)"""

# Region 2b: the VAO bind + renderer construction.
RENDERER_OLD = """\
    glfw.swap_interval(1)
    # macOS core profile requires a non-zero VAO bound at all times.
    GL.glBindVertexArray(GL.glGenVertexArrays(1))
    Context.window = window
    Context.renderer = Renderer(WIDTH, HEIGHT)"""
RENDERER_NEW = """\
    glfw.swap_interval(1)
    # No VAO: the fixed-function pipeline needs none (VAOs are a 3.0+ construct).
    Context.window = window
    Context.renderer = Renderer1x(WIDTH, HEIGHT)"""


def require(condition: bool, message: str) -> None:
    """Fail loudly if an expected anchor is missing/ambiguous in boing.py."""
    if not condition:
        raise SystemExit(f"make_boing_gl1: {message}")


def main() -> None:
    src = BOING.read_text()

    # 1. Replace the module docstring by SPAN (robust to its text drifting):
    #    the first `"""` opens it, the next `"""` closes it. The license header
    #    above is all `#` comments, so the first triple-quote is the docstring.
    open_q = src.find('"""')
    require(open_q != -1, "no module docstring found in boing.py")
    close_q = src.find('"""', open_q + 3)
    require(close_q != -1, "module docstring is not closed")
    src = src[:open_q] + NEW_DOCSTRING + src[close_q + 3 :]

    # 1b. Rewrite the inlined renderer SECTION header (banner + its module
    #     docstring) from 3.3-core to fixed-function, so the prose matches the
    #     Renderer1x this file uses (no dangling ortho_pixels / shader refs).
    require(
        src.count(RENDERER_BANNER_OLD) == 1,
        "renderer.py section banner not found exactly once",
    )
    src = src.replace(RENDERER_BANNER_OLD, RENDERER_BANNER_NEW)
    require(
        src.count(RENDERER_DOC_OLD) == 1,
        "renderer.py section docstring not found exactly once",
    )
    src = src.replace(RENDERER_DOC_OLD, RENDERER_DOC_NEW)

    # 1c. The inlined Context class annotates its renderer as `Renderer` (the 3.3
    #     class we remove); point those at `Renderer1x` so ruff/ty resolve them,
    #     and fix the Context docstring's cross-reference to the 3.3 renderer.
    context_refs = (
        (
            ":class:`~pgzero_gl.renderer.Renderer`",
            ":class:`~pgzero_gl.renderer_gl1.Renderer1x`",
        ),
        (
            "renderer: Renderer | None = None",
            "renderer: Renderer1x | None = None",
        ),
        (
            "def require_renderer() -> Renderer:",
            "def require_renderer() -> Renderer1x:",
        ),
    )
    for old, new in context_refs:
        require(
            src.count(old) == 1, f"Context ref {old!r} not found exactly once"
        )
        src = src.replace(old, new)

    # 2. Extract `class Renderer1x` from the shared shim (the class runs to EOF,
    #    since set_clip is the last thing in the file). Drop the module-level
    #    `from .renderer import _rgba` -- boing_gl1 defines its own _rgba below.
    shim = RENDERER_GL1.read_text()
    marker = "class Renderer1x:"
    require(marker in shim, "class Renderer1x not found in renderer_gl1.py")
    renderer1x = shim[shim.index(marker) :].rstrip() + "\n"

    # 3. Swap region 1: matrix-helpers/shaders/_compile/Renderer -> Renderer1x.
    require(
        src.count(REGION1_START) == 1,
        "Matrix-helpers banner not found exactly once",
    )
    require(
        src.count(REGION1_END) == 1, "_rgba() helper not found exactly once"
    )
    start = src.index(REGION1_START)
    end = src.index(REGION1_END)
    require(start < end, "region-1 anchors are out of order")
    replacement = RENDERER1X_BANNER + "\n\n" + renderer1x + "\n\n"
    src = src[:start] + replacement + src[end:]

    # 4. Swap region 2: the __main__ context hints and renderer construction.
    require(src.count(HINTS_OLD) == 1, "3.3 window hints not found exactly once")
    src = src.replace(HINTS_OLD, HINTS_NEW)
    require(
        src.count(RENDERER_OLD) == 1,
        "VAO/Renderer construction not found exactly once",
    )
    src = src.replace(RENDERER_OLD, RENDERER_NEW)

    # Sanity: the 3.3-only names must be gone; the 1.x renderer must be present.
    for gone in (
        "class Renderer:",
        "_VERT",
        "_FRAG",
        "ortho_pixels",
        "OPENGL_CORE_PROFILE",
        "The OpenGL 3.3 core back end",
    ):
        require(gone not in src, f"3.3-only symbol {gone!r} still present")
    require("class Renderer1x:" in src, "Renderer1x missing from output")

    BOING_GL1.write_text(src)
    print(f"wrote {BOING_GL1} ({src.count(chr(10)) + 1} lines)")


if __name__ == "__main__":
    main()
