# Fix `ports/codetheclassics/_smoketest.py` — broken `pgzero_gl.pgzrun` reference

**Status:** proposed — needs go-ahead
**Created:** 2026-07-23 (surfaced while verifying the frozen-vector rebind migration —
the smoke test was the intended render gate and couldn't run)

## The bug

`ports/codetheclassics/_smoketest.py` fails on any game with:

```
AttributeError: module 'pgzero_gl' has no attribute 'pgzrun'
```

at (roughly) `_smoketest.py:189`:

```python
pgzero_gl.pgzrun.go = lambda gl=None: None
```

`pgzrun` no longer exists on the `pgzero_gl` package. The **honest-imports pass
(2026-07-08)** deleted the synthetic `pygame`/`pgzero`/`pgzrun` `sys.modules`
impersonation modules (see `tasks/reference/design-decisions.md` › "Honest imports
cluster" and `tasks/archive/2026/07/08/ctc-honest-imports.md`). The smoke test was
not updated to match, so it has been dead since then. `go()` now lives directly on
the package (`from pgzero_gl import go`) / in `pgzero_gl.runner`.

## Why it matters

`_smoketest.py` is the **headless render gate**: it renders one frame of a ported
game to an offscreen EGL pbuffer (Mesa llvmpipe, no display/GPU), writes a PNG, and
exits non-zero if the frame is mostly black. Its own docstring says it is "how the
integer-tint black-screen bug was found + fixed", and `notable-subsystems.md` § 4a
cites it as the CI render guard. While it's broken, **no automated check verifies the
games actually draw** — only that they import and their update loops run (which is
what the frozen-vector migration's differential *state* trace covered, but that trace
never touches the renderer).

## What to do

1. **Reproduce**: `cd ports/codetheclassics && python _smoketest.py vol1/boing/boing.py`
   → the `AttributeError` above.
2. **Fix the launch stub.** The test stubs `go()` so importing the game doesn't
   actually open a window / run the loop. Point it at wherever `go` lives now — likely
   `pgzero_gl.go = lambda *a, **k: None` and/or `pgzero_gl.runner.go = …`. Confirm by
   reading `pgzero_gl/__init__.py` and `runner.py` for the real name; grep the games
   for how they call it (`go()` at module scope).
3. **Audit the rest of `_smoketest.py` for the same rot.** The honest-imports pass
   changed more than `pgzrun`; check every `pgzero_gl.<attr>` and every
   `sys.modules[...]` stub in the file against the current package surface (e.g. it
   still sets `sys.modules.setdefault("just_playback", …)`, but audio moved off
   `just_playback` to `miniaudio` on 2026-07-09 — that stub may now be pointless or
   need to be `miniaudio`). One broken reference this old usually has siblings.
4. **Verify it renders**, per the container GUI recipe: EGL surfaceless + Mesa
   llvmpipe. Run it on **one game per volume** at minimum (e.g. `vol1/boing`,
   `vol2/eggzy` — note eggzy needs the `_setup` hook that forces `State.PLAY`), and
   **check the PNG has non-black pixels**, not just a zero exit code (a GUI smoke test
   that doesn't crash can still draw nothing — see the sandbox GUI-verification note).
5. **Consider wiring it as a gate.** Right now nothing runs it. Out of scope to
   decide here, but note whether it *should* be part of `format.sh` / a make target,
   or stay a manual tool.

## Notes / gotchas

- Nested-container render needs `--cgroups=disabled`; the EGL/llvmpipe path is
  headless (no X server), distinct from the GLFW-window demos.
- The state-trace harness from the frozen-vector work
  (`tasks/archive/2026/07/23/frozen-vectors-rebind-migration.md`) drives `update()`
  headless and is a good reference for the `State.PLAY` setup per game, but it is
  **not** a renderer test — this task is specifically about the draw path.

## Relationships

- Root cause: `tasks/archive/2026/07/08/ctc-honest-imports.md` (deleted the `pgzrun`
  shim without updating `_smoketest.py`).
- Surfaced by: `tasks/archive/2026/07/23/frozen-vectors-rebind-migration.md`.
