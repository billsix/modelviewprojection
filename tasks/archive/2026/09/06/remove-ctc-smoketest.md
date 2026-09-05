# Remove the dead Code-the-Classics smoke test (`ports/codetheclassics/_smoketest.py`)

**Status:** DONE + ARCHIVED 2026-09-06 — go-ahead from William Emerison Six <billsix@gmail.com> 2026-09-05 ("sure if you recommend to"); `git rm ports/codetheclassics/_smoketest.py`, README's two mentions replaced with the `tools/ctc_*` usage, `notable-subsystems.md` and `tests-and-gates.md` entries rewritten as removed (EGL lore kept). `tasks/adhoc/pgzero-gl-inline/context_to_class.sh` and `tasks/pgzero-gl-de-abstraction-options.md` still name it historically — left as is.
**Priority:** 6
**Difficulty:** 2

## BLUF

`ports/codetheclassics/_smoketest.py` renders one frame of a game to an EGL pbuffer by importing the
game as a module and driving its `update()`/`draw()`. No game has allowed that since the inlining
pass made each game own its loop, and every tightened game now exits on import
(`if __name__ != "__main__": sys.exit(...)`), so the tool cannot run. Delete it and the README lines
that point at it; `tools/ctc_verify_game.sh` (frame capture under Xvfb, running the game as
`__main__`) is the tool now.

## Context

- `ports/codetheclassics/README.md` lines ~84 and ~112–118 describe and invoke `_smoketest.py`.
- `tasks/reference/notable-subsystems.md` ("Headless verification") and `tasks/reference/tests-and-gates.md`
  describe it as a manual tool; `tasks/reference/design-decisions.md` mentions its 2026-07-25 fix.
- It was never wired into any gate (documented as manual), so nothing breaks by removing it.

## Plan

1. `git rm ports/codetheclassics/_smoketest.py`.
2. README: replace the `_smoketest.py` paragraph with the `tools/ctc_verify_game.sh` usage.
3. The two reference docs: mark the entry as removed (2026-09-05) and point at the tools.

Alternative, if a headless EGL render is still wanted: rewrite it as a subprocess runner
(`PGZERO_MAX_FRAMES=1` + a capture hook), which is what `capture_frame.py` already is.
