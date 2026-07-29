# Make JupyterLab open py:percent files as notebooks by default

**Status:** proposed — needs go-ahead to implement

## Goal

In the JupyterLab web interface (`make jupyter`), a single click on a
jupytext py:percent `.py` file should open it **as a notebook**, without the
user having to right-click → "Open With → Notebook". Accepted trade-off:
`.py` files no longer open as plain text by default in JupyterLab — a
regular text editor covers that case.

## The change

Add `jupytext-config set-default-viewer python` to the `Dockerfile` —
**inside the `if [ "$USE_JUPYTER" = "1" ]` block** (currently around lines
136–149), after the dnf install of `jupytext` / `python3-jupyterlab-jupytext`
completes:

```dockerfile
    if [ "$USE_JUPYTER" = "1" ]; then \
       dnf install -y \
                   ... \
        	   python3-jupyterlab-jupytext \
        	   python3-jupyter-lsp  && \
       uv pip install moviepy --python $(which python) && \
       jupytext-config set-default-viewer python; \
    fi; \
```

**Caveat — placement matters in this repo:** unlike gacalc/mvm, jupytext
here comes from **dnf** (system package, on PATH — no venv activation
needed), but it is **feature-flag gated**. A `jupytext-config` call outside
the `USE_JUPYTER` block would break the lean `podman build` (flag defaults
`0` in the Dockerfile, `1` in the Makefile) with command-not-found.

## Why this works / constraints checked (2026-07-29)

- `jupytext-config` is a console script shipped with jupytext; the dnf
  `jupytext` package puts it on the system PATH, so it is available right
  after the install in the same shell.
- It writes `~/.jupyter/labconfig/default_setting_overrides.json` for the
  build user (root → `/root/.jupyter/...`). The container runs as root and
  the Makefile mounts nothing over `/root/.jupyter` (checked: only
  `.tmux.conf`, `.gitconfig`, `.gnupg`, emacs `elpa` + melpa el file), so
  the baked config is what `make jupyter` sees.
- No `jupytext-config` / `set-default-viewer` call exists anywhere in the
  repo today (grepped Dockerfile, Makefile, entrypoint/*.sh).

## Verification

1. `make image` — with the repo's **default flags**, i.e. `USE_JUPYTER=1`
   ON, since the diff lives inside that flag's block; a `USE_JUPYTER=0`
   gate would verify nothing (per the flag-coverage rule). Nested podman:
   transient `--cgroups=disabled` per standing arrangement.
2. In the built image: `jupytext-config list-default-viewer` → should print
   `python`.
3. Confirm `/root/.jupyter/labconfig/default_setting_overrides.json` exists
   and names `@jupyterlab/docmanager-extension` → `defaultViewers` →
   `python: "Jupytext Notebook"`.
4. Also build once with `USE_JUPYTER=0` to confirm the lean image still
   builds (the call must be inside the guarded block).
5. Real check: `make jupyter`, open http://127.0.0.1:8888/lab, single-click
   a py:percent demo file — it must open in the notebook editor.
