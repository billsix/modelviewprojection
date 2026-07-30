# Plan: package SuperBible v4 + v7 as standalone Python distributions

Apply the same packaging treatment as the McNopper PyPI plan
([`mcnopper-pypi-package.md`](mcnopper-pypi-package.md)) to
`/mvp/ports/openglsuperbiblev4/` (101 .py files, ~83 MB assets) and
`/mvp/ports/openglsuperbiblev7/` (83 .py files, ~258 MB assets).

**Status:** not started. Should follow McNopper packaging — reuse the
same patterns, scripts, and `pyproject.toml` shape.

**Read first:** [`mcnopper-pypi-package.md`](mcnopper-pypi-package.md)
— covers all the cross-cutting decisions (asset-bundling strategy,
license, entry-point shape, `find_media` adaptation, CLI design,
testing strategy). This plan only documents the v4/v7-specific delta.

## Why ship them separately (not as one mega-package)

Three separate packages — `mcnopper-demos`, `superbible4-demos`,
`superbible7-demos` — for these reasons:

- Different upstream sources, different upstream licences. Don't
  bundle Norbert Nopper's MIT, OpenGL SuperBible 4e's licence, and
  OpenGL SuperBible v7's licence into one wheel and pretend they're
  one project.
- Different OpenGL version floors. McNopper has GL4 demos, v4 stays
  on GL2.1/3.3, v7 mixes 4.x compute and 4.5 DSA.
- Different asset stories. v4 ships 83 MB, v7 ships 258 MB, McNopper
  ships 290 MB. Letting users install only what they want avoids
  mandatory ~600 MB downloads.
- Different demo structure. v4 is chapter-organised (`chapt01/...`),
  v7 is flat-folder. The CLI shape will diverge slightly.

## Scope per port

### v4 — `superbible4-demos`

```
superbible4-demos/
├── pyproject.toml
├── README.md
├── LICENSE                             (OpenGL SuperBible 4e + Bill's port notice)
├── src/
│   └── superbible4/
│       ├── __init__.py
│       ├── _common.py                  (the existing /mvp/ports/openglsuperbiblev4/_common.py)
│       ├── _cli.py
│       ├── chapt01/...                 (each chapter is a sub-package)
│       ├── chapt02/...
│       └── chapt22/...
└── tests/
```

CLI shape:
```
superbible4-list                        prints all ~95 functional demos
superbible4 chapt05 litjet              runs /chapt05/litjet/<demo>.py
superbible4 chapt19 sphereworld
```

Asset directory (~83 MB) is small enough to consider option (a) —
bundle directly into the wheel — but the same option-(b) split-package
pattern is cleaner long-term. Pick (b) for consistency with the
McNopper packaging.

Companion data package: `superbible4-media`.

**Special case — chapter stubs.** Per the SuperBible full port status
notes, chapt19 has stubs (RThread, GLView), chapt20 (Apple Carbon /
Cocoa) and chapt22 (OpenGL ES) are entirely stubs. The CLI should
either skip them in `superbible4-list` or print "(platform stub)"
beside them, not silently expose them as runnable.

### v7 — `superbible7-demos`

```
superbible7-demos/
├── pyproject.toml
├── README.md
├── LICENSE                             (OpenGL SuperBible v7 + Bill's port notice)
├── src/
│   └── superbible7/
│       ├── __init__.py
│       ├── _common.py
│       ├── _vmath.py
│       ├── _ktx.py
│       ├── _sb6m.py
│       ├── _sb7.py
│       ├── _colors.py
│       ├── _cli.py
│       ├── alienrain/
│       ├── basicfbo/
│       └── ...
└── tests/
```

CLI shape:
```
superbible7-list
superbible7 alienrain
superbible7 cubemapenv
```

Asset directory is **258 MB**. Option (b) split-package
(`superbible7-media`) is the only sensible choice — a 258 MB wheel
needs a PyPI exception and is unfriendly to install.

The v7 framework is class-based (`Application` subclass with
`startup` / `render` / `shutdown`). The `_cli` dispatcher needs to
import the demo module and instantiate its `Application` subclass —
unlike McNopper / v4 where the entry-point is a module-level
`_main()` function. Account for that in the entry-point glue.

Compute and 4.5 DSA demos depend on Mesa quirks documented in
[`notes-v7-port-framework-gotchas.md`](notes-v7-port-framework-gotchas.md);
include a link to those notes in the README so users on weaker
drivers understand the failure modes.

## Asset-package boundaries

Both v4 and v7 already use a `find_media` (or equivalent) helper —
adapt it to consult `importlib.resources.files("superbible4_media")`
or `importlib.resources.files("superbible7_media")` first, falling
back to the existing dev-tree resolution chain.

For v7 specifically, the media path is shared with the C++ port
(memory note `project_v7_media_path.md` — `/superbiblev7/bin/media/`).
The Python data package should bundle a copy, not symlink, so
`pip install` is self-contained and doesn't depend on the C++ tree
being checked out.

## Steps

For each port (do v4 first since it's smaller, then v7):

1. Confirm name, bundling strategy, and licence text with Bill before
   writing code.
2. Run the typing pass first
   ([`superbible-v4-v7-typing-pass.md`](superbible-v4-v7-typing-pass.md))
   if it hasn't run yet — packaged code should already be typed.
3. Mirror the McNopper packaging skeleton from
   [`mcnopper-pypi-package.md`](mcnopper-pypi-package.md). Re-use the
   `pyproject.toml` template; swap names, dependencies, and entry
   points.
4. Build the data package (`superbible4-media` /
   `superbible7-media`) as a sibling.
5. Update `_common.py` to consult `importlib.resources` first.
6. Refactor each demo's `if __name__ == "__main__":` block so the CLI
   can dispatch to it.
7. `python -m build` both packages; install into a fresh venv;
   sanity-check 3–4 demos per port (Bill verifies — needs display).
8. Push to PyPI test index, then prod, **only after Bill explicitly
   approves each upload**.

## Don't

- Don't combine v4 + v7 into one package. Different licences,
  different version floors, different framework shapes.
- Don't publish without Bill's explicit go-ahead per upload. PyPI
  uploads are visible, irreversible.
- Don't break the in-tree `python <demo>.py` development flow.
- Don't trim assets to fit PyPI limits — use the split-package
  strategy or request a limit raise.

## Done when

- All three packages (`mcnopper-demos`, `superbible4-demos`,
  `superbible7-demos`) install side-by-side in one venv without
  collision.
- Each port's `<port>-list` CLI prints the full demo inventory.
- Bill has run at least 3 demos per port from the installed venv.
- Each port has its own `LICENSE` reflecting upstream + the
  William Emerison Six MIT port notice (mirror the McNopper layout).
