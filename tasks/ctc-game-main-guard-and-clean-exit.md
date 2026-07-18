# CtC games: guard `go()` behind `if __name__ == "__main__"` + exit cleanly

**Status:** proposed — needs go-ahead
**Created:** 2026-07-18 (surfaced while profiling gacalc via the CtC games; the
games needed SIGKILL to stop — see gacalc `tasks/profile-gacalc-op-mix-in-mvp.md`)

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

## Plan

- [ ] Reproduce: run a game (e.g. `vol1/boing/boing.py`), close the window, confirm
      the process lingers (needs kill). Compare with an mvpViz explorer that exits 0.
- [ ] Fix the shared runner (Part 2): window-close + Esc + signal handling + clean
      teardown. Verify a single game now exits 0 on window-close and on Ctrl-C.
- [ ] Add the `__main__` guard to all 10 game files (Part 1); confirm each still
      launches when run directly and no longer launches on bare import
      (`python -c "import importlib.util, …"` / the `_smoketest.py` import path).
- [ ] Gate: `_smoketest.py` for each game still renders a frame; `make format`
      (ruff + ty) clean; a quick play-test of 2–3 games (window closes cleanly).

## Open questions

- Should the guard wrap only `go()`, or also a tiny `def main(): …` refactor? (Lean:
  minimal — just guard `go()`, keep the games near-verbatim.)
- Is `libdecor` available/desired in the image for real Wayland window decorations,
  or should we rely on Esc-to-quit + the X11 path for closing?
- Do the mvpVisualization explorers already do the right thing (they exit 0) — can
  the runner just adopt `cayley_gl.run_loop`'s close/signal handling verbatim?
