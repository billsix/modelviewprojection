# Fix no-op `exec` in jupyter.sh

**Status:** complete
**Completed:** 2026-06-14
**Created:** 2026-06-13

Resolved 2026-06-14 as part of restoring Jupyter support: `entrypoint/jupyter.sh`
was rewritten to `exec jupyter lab …` (no more bare no-op `exec`) and to run
`loadpackages.sh` first so the notebooks can `import modelviewprojection` (the
editable install had been lost). Also (re)added a `make jupyter` target that prints
the `http://127.0.0.1:8888/lab` URL, and seeded `~/.bash_history` with
`/usr/local/bin/jupyter.sh # on http://127.0.0.1:8888/lab` (geometricalgebra style).
The `.bash_history` line requires a `make image` rebuild to take effect.

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
