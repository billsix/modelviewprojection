# Fix no-op `exec` in jupyter.sh

**Status:** proposed — not started
**Created:** 2026-06-13

## Goal

`entrypoint/jupyter.sh` has a bare `exec` on its own line followed by the
`jupyter lab …` invocation as a separate statement. A bare `exec` (no command)
only applies redirections and returns — it does nothing here — so `jupyter lab`
runs as an ordinary child process instead of replacing the shell. Make the
server actually `exec` so it becomes PID-correct (clean signal handling /
shutdown inside the container).

## Plan

- [ ] Join the two statements: `exec jupyter lab \` … (i.e. put `exec`
      immediately before `jupyter lab` on the same logical command), and remove
      the stray bare `exec` line.

## Notes / decisions

- Single-line fix; tracked as a task only because the cleanup sweep is being
  recorded per-project.

## Open questions

- None.
