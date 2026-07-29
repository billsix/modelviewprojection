# Suppress JupyterLab's "official Jupyter news" notification prompt

**Status:** DONE 2026-07-29 — implemented and gate-verified; ready to archive

Outcome: implemented **with one deviation from the plan below** — the call
needs `--level=user`. The first build (default sys_prefix level) passed its
gate but verification caught the config landing in
`/usr/etc/jupyter/labconfig/`, which the venv-launched server never reads:
at that point in the giant RUN the venv has no `jupyter` binary yet (the
requirements pip install that seeds `jupyter_core` into /venv comes later),
so the command resolved to `/usr/bin/jupyter` (system-python shebang →
sys.prefix=/usr). `--level=user` writes `/root/.jupyter/labconfig/
page_config.json`, read under any prefix. Rebuilt gate PASSED; plugin lists
under "Disabled extensions" with the venv active; jupytext default-viewer
setting survived. (Unlike gacalc/mvm's sys-prefix writes, the user-level
write is not auto-locked — acceptable for a single-user container.)
Remaining human check: `make jupyter` in a fresh browser profile shows no
news prompt.

## Goal

`make jupyter` should come up without the "Would you like to receive
official Jupyter news?" toast. That prompt is JupyterLab's built-in
announcements plugin (`@jupyterlab/apputils-extension:announcements`)
phoning the news feed; disabling the plugin removes both the prompt and
the fetch.

## The change

In the `Dockerfile`, chain onto the `jupytext-config` call **inside the
`if [ "$USE_JUPYTER" = "1" ]` block** (same placement rule as the
jupytext-default-viewer change — jupyterlab only exists when that flag is
on, so the call outside the guard would break the lean build):

```dockerfile
       uv pip install moviepy --python $(which python) && \
       jupytext-config set-default-viewer python && \
       jupyter labextension disable "@jupyterlab/apputils-extension:announcements"; \
    fi; \
```

Placement checked: `/venv` is created (line ~117) and activated earlier in
this same giant RUN's shell, before the `USE_JUPYTER` block (~line 136),
so the disable command runs venv-active and writes at the venv sys-prefix
even though jupyterlab itself comes from dnf.

## Verified in the built image (2026-07-29, current `localhost/modelviewprojection`)

- With `/venv` active, the command writes
  `/venv/etc/jupyter/labconfig/page_config.json`:
  `{"disabledExtensions": {"@jupyterlab/apputils-extension:announcements": true}}`.
  `jupyter.sh` activates `/venv` before `exec jupyter lab`, so the running
  server reads that sys-prefix labconfig; nothing in the Makefile mounts
  over `/venv`.
- `jupyter labextension list` then shows the plugin under
  "Disabled extensions".
- The command prints a warning that since JupyterLab 4.1 a user can
  re-enable disabled plugins in the UI unless they are locked
  (`jupyter labextension lock`), and exits 0. For this single-user
  teaching container the lock is unnecessary — a user re-enabling it is
  making a deliberate choice; skip the lock unless that proves annoying.

## Verification

1. `make image` with default flags (`USE_JUPYTER=1` ON — the diff lives
   inside that flag's block, so a lean gate would verify nothing). No
   separate `USE_JUPYTER=0` build needed: the shell parses the whole RUN
   regardless of flag values, and the guarded call is skipped by
   construction (same argument as the jupytext-default-viewer task).
2. In the built image (venv active): `jupyter labextension list` shows
   `@jupyterlab/apputils-extension:announcements` disabled, and
   `/venv/etc/jupyter/labconfig/page_config.json` has the entry above.
3. Real check: `make jupyter`, open http://127.0.0.1:8888/lab in a fresh
   browser profile/private window (the prompt is also suppressed by a
   browser-side "answered" flag, so an already-used profile can false-pass)
   — no news prompt should appear.
