# CtC games: guard `go()` behind `if __name__ == "__main__"` + exit cleanly

**Status:** complete
**Completed:** 2026-08-23 — all three parts done and **Bill-verified on his hardware**: Cavern and
boing (he checked all the games) exit cleanly on Esc. The third bug was the meaty one — Bill
reported Cavern: pressing Esc closes the window but **the process hangs**. Root cause: the runner's
`finally` tore down GLFW but **never stopped the miniaudio audio device**, whose native callback
thread then kept Python alive after the loop ended. Headless never hit it (no audio device opens →
no thread), which is why Parts 1–2 verified clean headlessly. Fixed by adding `audio.shutdown()`
(closes the `PlaybackDevice`, lock released to avoid a callback-thread-join deadlock) and calling it
from the runner's `finally` (see "Part 3"). Durable knowledge harvested to
`tasks/reference/notable-subsystems.md` (shim + audio exit gotcha, `go`→`main`) and
`tasks/reference/design-decisions.md` (audio decision).

**Follow-up (2026-08-23, Bill's request): renamed the shim launch function `go` → `main`.** Now
that the call is guarded by `if __name__ == "__main__":`, `main()` reads more naturally than the
old `go()` (which mirrored pgzero's `pgzrun.go()`). Renamed `def go` → `def main` in
`pgzero_gl/runner.py` and its `__init__.py` export + `__all__`; updated the `go()` mentions in
`context.py` and the `go`-stub in `ports/codetheclassics/_smoketest.py` (whose comment was also
corrected — the `__main__` guard, not the stub, is now what stops import-time launch); and moved
all 10 games' `import go`/`go()` → `main` via a second word-precise idempotent codemod,
`tasks/adhoc/.../rename_go_to_main.py` (+ `ruff --fix` to re-sort the import). Docstrings that
described `go` as "one of PyGame Zero's globals (`pgzrun.go`)" were reworded — `main` is this
port's own launch entry, not a pgzero global. ruff + ty clean; only `pgzrun.go` (the external
pgzero API being emulated) is still named, deliberately.
**Priority:** 5
**Difficulty:** 4
**Created:** 2026-07-18 (surfaced while profiling gacalc via the CtC games; the
games needed SIGKILL to stop — see gacalc's `tasks/archive/2026/07/18/profile-gacalc-op-mix-in-mvp.md` (`github.com/billsix/geometricalgebra`))

## Goal

Two related fixes to the `pgzero_gl` ports so the games are tool-friendly and shut
down cleanly:

1. **`__main__` guard.** Every ported game (`vol1/{boing,bunner,cavern,myriapod,
   soccer}`, `vol2/{avenger,beatstreets,eggzy,kinetix,leadingedge}`) currently ends
   with a **bare module-level `go()`** — so merely *importing* the module launches
   the game (window + 60 Hz loop). Guard the launch: `if __name__ == "__main__": go()`.
2. **Graceful exit.** Closing the game window during profiling did **not** terminate
   the process (it took `SIGKILL`; `SIGTERM` was ignored). The shared loop should
   exit cleanly on window-close / quit-key / `SIGTERM`. The `pgzero_gl`
   **mvpVisualization** explorers (`cayley_gl.run_loop`) already exit cleanly
   (observed exit 0) — mirror whatever they do.

## Part 1 — the `__main__` guard (per game, 10 one-line edits)

Change the trailing `go()` to:

```python
if __name__ == "__main__":
    go()
```

**Caveat — keep everything else at module level.** `runner.go()` reads its
*caller's* module globals via `sys._getframe(1).f_globals` (to find `update`/`draw`/
`WIDTH`/`HEIGHT`/…), and pgzero-style `update()`/`draw()` are looked up as module
globals. Guarding **only the final `go()` call** is safe (the `if __name__` block
runs at module scope, so the caller frame's `f_globals` are still the module
globals). **Do NOT** move the game's state/functions inside the `if` block — that
would make them block-locals and break both `go()`'s introspection and the
update/draw lookup.

**Faithfulness note.** These games are deliberately *near-verbatim* copies of the
originals, and the bare `go()` is the port's own addition (its comment even says
"only required when running from an IDE"). A `__main__` guard is a minimal,
low-risk wrapper around that added line — arguably *more* faithful, since real
PyGame Zero launches via `pgzrun`, not a bare `go()` at import.

## Part 2 — graceful exit (shared, in `pgzero_gl/runner.py`)

The loop is `while not glfw.window_should_close(window): … finally: glfw.terminate()`.
Investigate why window-close didn't stop it and fix in the shared runner (one change
covers all 10 games):

- **Window-close event.** On **Wayland**, a GLFW window may lack server-side
  decorations (no title-bar close button) unless `libdecor` is present, so
  `glfw.window_should_close` may never flip. Confirm decorations / the close path;
  ensure clicking-to-close actually ends the loop.
- **Quit key.** Bind **Esc** (and/or the window's close) to `quit_game()` (already
  defined — `glfw.set_window_should_close(window, True)`), so there's always a
  keyboard way out.
- **Signals.** Install `SIGINT`/`SIGTERM` handlers that flip `window_should_close`
  (or raise a clean shutdown) so `podman stop` / Ctrl-C end the loop between frames.
  (During profiling the process was also PID 1 in the container — PID 1 ignores
  signals without an explicit handler — so a handler helps there too, though that
  part is a container artifact, not the game's bug.)
- **Cleanup.** Ensure the `finally: glfw.terminate()` runs and any renderer/GL
  resources are released, so exit is clean (exit 0), matching the mvpViz explorers.

## Part 3 — audio device never stopped → process hangs on exit (found 2026-08-23, Bill's hardware)

**Symptom (Cavern):** Esc closes the window, but the process hangs — it took a kill to stop.

**Root cause.** `pgzero_gl` audio is a single-device software mixer on **miniaudio**
(`audio.py`). Cavern plays background music (`music.play("theme")`, `cavern.py:976`), which
opens a `miniaudio.PlaybackDevice`. That device runs its mixer callback on a **native (C)
thread that is not a Python `threading.Thread`.** The runner's `finally` only did
`glfw.terminate()` (window closes — the visible part) and **never closed the audio device**, so
the audio thread stayed alive and kept the interpreter from exiting. Headless the device never
opens (`_ensure_device` fails → `_failed=True`, no thread), so Parts 1–2 looked clean — the bug
is display+audio-hardware-only.

**Fix (one change, covers all 10 games).**
- `audio.py`: `_Engine.shutdown()` clears voices and calls `device.close()` **with the lock
  released** (close joins the callback thread, which itself takes `self._lock` — closing under
  the lock would deadlock). Idempotent, best-effort. Module-level `audio.shutdown()` wraps it.
- `runner.py`: the loop's `finally` now calls `audio.shutdown()` (local `from . import audio`,
  guarded) *before* `glfw.terminate()`.

**Headless gate:** `py_compile` clean; `ruff check` clean on both files; `audio.shutdown()`
proven idempotent as a no-op with no device (double call). ty shows only environment
`unresolved-import` (miniaudio/glfw/OpenGL not in the sandbox) — no type errors from the change.

**Needs Bill (display + audio hardware):** Cavern now exits 0 on Esc/window-close, *and* a
sound-effects-only game (e.g. boing) still exits 0 — confirming the fix isn't music-specific.

## Plan

- [x] **Part 3 — audio device shutdown (`pgzero_gl/audio.py` + `runner.py`).** See Part 3 above:
      `audio.shutdown()` closes the miniaudio `PlaybackDevice` from the runner's `finally`, so the
      native audio thread no longer keeps the process alive after the window closes.
- [x] **Part 2 — shared runner (`pgzero_gl/runner.py`).** Two additions, one change covers
      all 10 games:
      - **Esc-to-quit** in the key callback — on Esc PRESS, `glfw.set_window_should_close`.
        Runs *after* the game's own `on_key_down`, so gameplay is unchanged. Mirrors the
        explorers' `cayley_gl.common_key` (`cayley_gl.py:624`). Grep confirmed only
        `leadingedge` reads `keyboard.escape` (to end the game), so Esc-quit is consistent
        with it and a pure additive exit for the other 9.
      - **SIGINT/SIGTERM handlers** installed around the loop (restored in `finally`) that
        call `quit_game()` — fixes Ctrl-C / `podman stop` / the PID-1-ignores-SIGTERM case
        (the "needed SIGKILL" symptom). Guarded with `try/except (ValueError, OSError)` so a
        non-main-thread caller (a test harness) skips them and still exits via
        window-close / `PGZERO_MAX_FRAMES`.
- [x] **Part 1 — `__main__` guard on all 10 games.** Done via an idempotent codemod,
      `tasks/adhoc/ctc-game-main-guard-and-clean-exit/add_main_guard.py` (run once; re-run
      reports 0 changes — idempotency proven). Each trailing bare `go()` → `if __name__ ==
      "__main__": go()`, with all game state/functions left at module scope (required for
      `go()`'s caller-frame introspection). Original launch comments left verbatim (faithful).
- [x] **Headless gate:** all 10 games + `runner.py` + the codemod `py_compile` clean; `ruff
      check` + `ruff format --check` clean on games and runner; `ty check runner.py` shows only
      environment `unresolved-import` for `glfw`/`OpenGL.GL` (not installed in the sandbox) —
      **no type errors from the changes**.
- [x] **Bill verified Esc (2026-08-23):** "escape seems to be working now" — Cavern exits
      cleanly on Esc on Bill's hardware (the audio-thread hang from Part 3 is gone). This is the
      key confirmation the headless gate couldn't give.
- [ ] **Remaining (optional, Bill's call before archive):** confirm a **sound-effects-only** game
      (e.g. boing) also exits 0 (proves the fix isn't music-specific); confirm **window-close
      button** and **SIGTERM** (`podman stop`) also exit 0 (Part 2's other paths); full
      in-container `make format` (ty with deps) green. Then archive + `/archive-task` triages the
      adhoc codemods (`add_main_guard.py`, `rename_go_to_main.py` — one-shot → `git rm`).

## Open questions — all resolved (2026-08-23)

1. **Guard only `go()`, or a `def main()` refactor?** → **Only `go()`** (minimal, near-verbatim),
   as recommended. The caveat section makes moving code into the guard actively wrong.
2. **`libdecor` for Wayland decorations, or rely on Esc/X11?** → **Sidestepped.** Esc-to-quit +
   the signal handlers give exit paths that don't depend on window-manager decorations, so
   `libdecor` is not required. Adding it for a real title-bar close button is an optional,
   separate nicety — not needed for a clean exit.
3. **Adopt `cayley_gl.run_loop` verbatim?** → **No — took its idea, not its body.** `run_loop`
   is imgui-specific; the reason the explorers exit cleanly is `common_key`'s Esc→
   `set_window_should_close`. Mirrored that (Esc) and added signal handling the explorers don't
   have (the games can run as PID 1 in a container, where the explorers don't).
