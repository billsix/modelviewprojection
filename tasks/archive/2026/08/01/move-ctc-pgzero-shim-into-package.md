# Move the Code-the-Classics `pgzero_gl` shim into the mvp package

**Status:** DONE 2026-08-01 — implemented; ruff + ty green (static gate), GL host
run remains Bill's. Archived.

## Outcome (2026-08-01)

Moved `ports/codetheclassics/pgzero_gl/` → **`src/modelviewprojection/pgzero_gl/`**
via `git mv` (kept the name; `LICENSE` + `py.typed` travelled with it). The shim's
relative imports meant zero edits inside it. Decisions taken (open questions below,
resolved with the recommended options under the go-ahead):

1. **Name/location (Q1):** kept `pgzero_gl` at the package top level.
2. **E402 scope (Q2):** split the per-file-ignore — `E402` now applies only to
   `ports/openglsuperbiblev4/**` (still uses a `sys.path` dance for
   `_common`/`_primitives`); `ports/codetheclassics/**` no longer ignores it.
3. **SuperBible ports (Q3):** left out of scope (a possible later follow-up).

Changes:
- **All 10 games** rewritten: dropped the `sys.path.insert/append` hack and the
  `import os as _os`/`import sys as _sys` (or plain `import os`/`import sys` where
  used only for the hack), switched to `from modelviewprojection.pgzero_gl import
  …` at the top, and removed the now-unneeded `# noqa: E402`. eggzy kept its own
  `import os`/`import sys` (used for `sys.path[0]` tilemaps/save — untouched).
- **beatstreets** genuinely used `_os` in its body (loads `attacks.json` relative
  to the script, line ~463) — added a plain `import os` and converted that use to
  `os` (caught by ruff F821, not my initial line-count audit).
- **`_smoketest.py`** imports repointed to `modelviewprojection.pgzero_gl`.
- **`pyproject.toml`:** E402 split (above); new per-file-ignore
  `src/modelviewprojection/pgzero_gl/** = ["E501", "T201"]` — the shim is NOT in
  the book (no `literalinclude`), so the 80-col-for-PDF rule doesn't apply; it
  keeps the E501 latitude it had under `ports/**` plus its one deliberate
  `PGZERO_GL_INFO`-gated backend-info print. (67 E501 + 1 T201 would otherwise
  fire now that it's under `src/`.)
- **`entrypoint/format.sh`:** dropped the dead `ty check .../pgzero_gl` line (the
  shim is covered by `ty check /mvp/src` now); kept the vol1/vol2 checks.
- **Docs:** `CLAUDE.md`, `ports/codetheclassics/README.md`, and the games'
  `ports/codetheclassics/LICENSE` shim note all repointed to the new path.

License: the shim's own `LICENSE` (LGPL-2.1) moved *with* it into the subpackage,
so the notice stays attached (see License section below). No relicensing.

Gate: `ruff check` (src/ports/tests/assignments) and `ty check` (shim + vol1 +
vol2, deps in a scratch venv) both **green**; all 10 games + smoketest + shim
`py_compile` clean. **Not run here:** the live GL window — Bill's host `make
image` + launch (a vol1 + a vol2 game, eggzy for the tilemap/save path).

Packaging note (Q from plan step 6): mvp has **no** `package-data`/`MANIFEST.in`
and is run editable / by path, not built as a distributable — so `py.typed`/the
shim `LICENSE` need no packaging config for the dev workflow. If mvp is ever
distributed, add package-data then.

---

*Original plan below.*

## Goal

Move the shared PyGame-Zero/pygame compatibility shim from
`ports/codetheclassics/pgzero_gl/` **into the installed `modelviewprojection`
package**, so the 10 game ports import it as a normal dependency instead of
manipulating `sys.path` at runtime. This removes the `sys.path`-then-import dance
and the `# noqa: E402` exceptions it forces, and lets the games' import blocks be
cleaned up.

## Why (what's wrong today)

Each of the 10 games (`ports/codetheclassics/vol1/{boing,bunner,cavern,myriapod,soccer}`,
`vol2/{avenger,beatstreets,eggzy,kinetix,leadingedge}`) begins with:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import random  # noqa: E402
...
from pgzero_gl import (  # noqa: E402
    Actor, go, keyboard, ...
)
```

Because the `sys.path.insert/append` is a statement that runs *before* the imports,
**every subsequent import must be tagged `# noqa: E402`** ("module import not at top
of file"). That is the "exceptions for imports after code runs" this task removes.
`ports/**` also carries a blanket `E402` in `pyproject.toml`'s per-file-ignores
(line 89-90).

The shim is **our code** (a clean-room reimplementation — see
`ports/codetheclassics/pgzero_gl/LICENSE`), unlike the games (upstream BSD-2), so it
*belongs* in the package rather than living beside the third-party game code.

## Recommended location & name

**`src/modelviewprojection/pgzero_gl/`** — a top-level subpackage, imported as
`from modelviewprojection.pgzero_gl import ...`.

Reasoning:
- **Keep the name `pgzero_gl`.** It's established, self-describing ("pgzero on GL"),
  carries `py.typed` + `LICENSE`, and is referenced across `CLAUDE.md`,
  `entrypoint/format.sh`, and every game. Keeping it means the *only* churn is the
  import-path prefix (`pgzero_gl` → `modelviewprojection.pgzero_gl`); renaming would
  multiply the edit for no gain.
- **Top-level subpackage, not under `util/`.** `util/` holds small graphics helpers
  (windowing, clipping, colorutils); the shim is a whole framework layer (20 modules),
  so it reads better as its own subpackage sibling to `demos/`, `framebuffer/`,
  `cayley/`.
- **No packaging edit needed to include it.** `[tool.setuptools.packages.find]
  where = ["src"]` (pyproject.toml:16-17) auto-discovers subpackages, so
  `modelviewprojection.pgzero_gl` is picked up automatically.
- **The shim is already package-ready.** Its `__init__.py` and modules use *relative*
  imports internally (`from . import audio, context`, `from .actor import Actor`,
  `from .geometry import Rect, ZRect`), so nothing inside the shim changes on the move.

(Open question 1 records the alternative naming/grouping choices in case Bill wants a
different home.)

## License — no blocker (but preserve the shim's notice)

Three licenses are in play; the move is clean:

- **The shim** (`pgzero_gl/LICENSE`) is **LGPL-2.1**, © William Emerison Six 2026 —
  deliberately the *same license as pygame*, because it reimplements pygame's API.
- **The mvp package** (top-level `LICENSE`) is **GPL-2** (source), © William
  Emerison Six 2016-2026.
- **The games** (`vol1/`, `vol2/`) are **BSD-2-Clause**, upstream Raspberry Pi
  Press / Eben Upton — and **they are NOT moving**, so their attribution stays put.

Why there's no issue:

1. **Same copyright holder.** Bill owns the copyright to *both* the shim and mvp, so
   he can combine or relicense his own code freely — no third-party consent needed.
2. **LGPL-2.1 is GPL-compatible even setting ownership aside.** LGPL-2.1 §3 permits
   converting any copy to plain GPL, and an LGPL component combining into a GPL
   project is exactly what the LGPL is for; the combined work is GPL while the shim
   stays available under LGPL. So LGPL-2.1 code living inside a GPL-2 tree is fine.
3. **The BSD games importing an LGPL shim is unaffected by the move** — a permissive
   work using an LGPL library is the ordinary LGPL "work that uses the Library" case,
   and moving the shim's directory changes nothing about it.

**The one thing to do (preserve, don't fix):** keep the shim's own `LICENSE` file
*inside* the moved `pgzero_gl/` subdirectory so the subpackage keeps carrying its
"LGPL, same as pygame" notice, rather than being silently absorbed into the GPL tree.
This is standard (a subdir with its own LICENSE) and keeps the deliberate license
intent visible. **The move does not relicense the shim** — it stays LGPL-2.1.

## Plan

1. **`git mv ports/codetheclassics/pgzero_gl src/modelviewprojection/pgzero_gl`**
   (preserve history; **move `LICENSE` and `py.typed` with it** — the `LICENSE` must
   stay inside the subpackage per the License section above). No edits inside the
   shim — its imports are already relative.
2. **Rewrite each game's import block** (10 files): delete the `import os`/`import sys`
   (where used *only* for the path hack) and the `sys.path.insert/append(...)` call;
   change `from pgzero_gl import ...` / `from pgzero_gl.draw import ...` /
   `from pgzero_gl.resources import ...` to the `modelviewprojection.pgzero_gl`
   prefix; **remove the now-unneeded `# noqa: E402`** from the import lines that were
   only deferred by the path hack.
   - **Caveat — eggzy keeps its own `sys.path` use.** `eggzy.py` separately relies on
     `sys.path[0]` pointing at its own directory for `tilemaps/` and the save folder
     (lines ~1284, 1288, 1755), and its shim import is a `sys.path.append` (end of
     path), *not* the insert(0) the others use. Remove only the shim-path `append` and
     its `# noqa: E402`s; **do not touch the `sys.path[0]` resource logic**, and keep
     `import os`/`import sys` if eggzy still needs them for that. Verify `python
     eggzy.py` still finds its tilemaps after the change.
   - **Caveat — some games still legitimately need `os`/`sys`** for gameplay/resource
     reasons; only remove the imports that become unused. Let `ruff --fix` (F401)
     confirm which.
3. **Narrow the `E402` ignore.** After step 2, check whether *anything else* under
   `ports/**` still trips E402 — the **SuperBible ports** (`ports/openglsuperbiblev4/**`)
   use the same `sys.path.insert` dance for their `_common` helper, so E402 likely must
   stay for *those*. Options: leave the blanket `ports/**` E402 as-is (simplest, but
   the CTC games no longer need it), or split the per-file-ignore so `E402` applies to
   `ports/openglsuperbiblev4/**` but not `ports/codetheclassics/**`. Decide with Bill
   (open question 2). Whatever's chosen, the CTC game files should end up E402-clean.
4. **Update `entrypoint/format.sh`** — the explicit `ty check
   /mvp/ports/codetheclassics/pgzero_gl` line (format.sh:30) moves to the new path (or
   is dropped, since the shim is now inside the package that `ty` already checks —
   confirm the package is in ty's checked set).
5. **Update `CLAUDE.md`** — the Code-the-Classics section cites `pgzero_gl/audio.py`,
   `geometry.py`, etc. by their old path; repoint to `modelviewprojection.pgzero_gl`.
   Note the games are now run against the editable install (the shim is no longer
   reachable by path hack), which is already how the rest of mvp runs.
6. **Packaging follow-up (verify, may already be fine):** there is **no `MANIFEST.in`
   and no `package-data` config** in `pyproject.toml`. For editable-install *dev* use
   (what the container does) `py.typed` is read straight from the source tree, so `ty`
   keeps working. But for a built wheel/sdist to ship `py.typed` and the shim's
   `LICENSE`, package-data may need declaring. Check whether mvp is ever built as a
   distributable (it's primarily run editable); if not, this is a no-op — say so
   rather than adding config that isn't needed. **If it IS distributed, the shim's
   LGPL `LICENSE` must be included** (per the License section) — package-data or
   MANIFEST.in.

## Gate

- `entrypoint/format.sh` clean: `ruff check ports --fix`, `ruff format ports`, and
  `ty check` over the moved shim + `vol1` + `vol2` — all green, and E402-clean on the
  CTC games.
- Each game still *imports* without the path hack (an import smoke-check catches the
  obvious breakage).
- **Bill's host run is the final check** — on-screen GL can't be verified headless
  here; launch at least one vol1 and one vol2 game (eggzy especially, for the
  tilemap/save-path caveat above).

## Open questions

1. **Location/name:** is **`src/modelviewprojection/pgzero_gl/`** (keep the name) the
   right home, or would you prefer a different name (e.g. `pgzerogl`) or a grouping
   subpackage (e.g. `src/modelviewprojection/ctc/pgzero_gl/`)? Recommendation: keep
   `pgzero_gl` at the package top level — least churn, clearest name.
2. **E402 scope:** after the CTC games are clean, do you want the `ports/**` E402
   ignore **split** so it only covers `ports/openglsuperbiblev4/**` (which still uses
   a `sys.path` dance for `_common`), or **left as the blanket `ports/**`** for
   simplicity? Recommendation: split it, so the CTC subtree genuinely enforces E402
   going forward.
3. **Do the SuperBible ports get the same treatment later?** Their `_common` helper has
   the identical `sys.path.insert` + E402 pattern. Out of scope here (this task is the
   CTC shim only), but flagging it as a natural follow-up if the pattern bothers you.
