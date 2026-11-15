# Dockerfile: order layers so an edited script or a toggled flag doesn't rebuild TeX and ePiX

**Started:** 2026-11-05 (William Emerison Six <billsix@gmail.com>). **Done:** 2026-11-14.

## Outcome

The `Dockerfile` was restructured the way github.com/billsix/geometricalgebra's was (its
`tasks/archive/2026/11/04/dockerfile-lean-layers-first.md`). Editing `entrypoint/04-install-emacs.sh`
now reruns only the Emacs layer and the cheap layers after it, and toggling `USE_SPYDER` reruns only
the Spyder layer onward; base, TeX, tex-expression-to-png, X, the venv/requirements install and ePiX
stay cached. The built package set is unchanged. The layer order and its two rules are recorded in
`tasks/reference/container-source-and-mounts.md`.

## What was wrong (2026-11-05 reading)

1. All five feature `ARG`s were declared at the top; a build-arg's value is in the cache key of every
   later `RUN`, so toggling any one rebuilt everything.
2. `COPY entrypoint/dotfiles/ /root/` and `COPY entrypoint/*.sh /usr/local/bin` ran before the first
   `RUN`, so editing any entrypoint script or dotfile invalidated every layer.
3. One `RUN` did base, docs, X, Emacs, Jupyter, Spyder, tex-expression-to-png, the venv, the Jupyter
   and Spyder config, the history seeding and the requirements install.

## What changed

- **Order:** base dnf → docs (TeX) → tex-expression-to-png → X → venv + setuptools/wheel +
  requirements → ePiX → Jupyter → Spyder → Emacs → dotfiles, run-time scripts and history seeding →
  gacalc sdist → `COPY . /mvp`.
- **Each install script is `COPY`ed just before its own `RUN`**; each `ARG` is declared just before
  the first layer that reads it (`BUILD_DOCS` covers the two adjacent docs layers).
- **The run-time scripts are copied by name at the end** (`entrypoint.sh` to `/` and to
  `/usr/local/bin`; `format.sh`, `jupyter.sh`, `loadpackages.sh`, `shell.sh`, `spyder.sh` to
  `/usr/local/bin`). They stay baked even though the Makefile bind-mounts five of them, because a
  pulled image runs without the mount and `loadpackages.sh` is never mounted.
- **Jupyter and Spyder config moved into their groups' layers**, each under its own flag check.
- **requirements.txt / constraints.txt are `COPY`ed** right before the venv layer (not bind-mounted),
  so a change to either changes that layer's cache key.
- Logic comments moved with their code; each `RUN` carries a one-line breadcrumb.

## Judgment calls

- **Requirements before ePiX.** The ePiX install puts its Python front-end into `/venv`, so it has to
  follow the venv layer, and the requirements install needs nothing from the groups that now come
  after it (uv ignores the distro `python3-*` packages and resolves from `constraints.txt`). A
  requirements bump therefore still rebuilds ePiX; putting ePiX between the venv creation and the
  requirements install would avoid that but would split the venv layer in two, and a `make
  update-pins` changes `constraints.txt`, which ePiX bind-mounts anyway.
- **Jupyter config now runs with `/venv` active, after the requirements install**, so
  `jupytext-config` and `jupyter` are the `/venv` ones the server runs (before, they were the distro
  `/usr/bin` ones). `--level=user` stays; the resulting `/root/.jupyter` files are byte-identical to
  the old image's. `tasks/reference/book-and-docs-pipeline.md` was updated to match.
- **Failures in the docs and Jupyter steps now fail the build.** The old single `RUN` joined those
  `if` blocks with `;`, so a failed tex-expression-to-png build or Jupyter config step was silently
  ignored. Each is now its own `RUN` whose exit status gates the build.
- **Layer order was not re-timed.** The plan asked to confirm the order from a build log; the
  concurrent builds in the sandbox (other agents' containers held the storage lock) made per-layer
  timings meaningless, so the order follows the known costs (TeX and ePiX are the slow layers; the
  Jupyter/Spyder/Emacs groups are single dnf calls) and the cache tests below.

## Verification

- `make image` (defaults: docs, Emacs, Jupyter, X, ePiX on; Spyder off) succeeded.
- **Package-set identity**, new image vs the old Dockerfile's image built the same day with the same
  flags: `rpm -qa`, `uv pip freeze`, `/usr/local/bin`, `/root/.jupyter` contents, `/root` entries,
  the shell history and `/opt` all identical, except a Fedora `dnf5`/`libdnf5` update (5.4.7 → 5.4.8)
  published between the two builds.
- **Cache behaviour:** with a marker line appended to `entrypoint/04-install-emacs.sh`, steps 1–24
  (through the Spyder layer) were `Using cache` and the Emacs `COPY`/`RUN` onward reran. With
  `USE_SPYDER=1`, steps 1–22 were cached and the Spyder layer reran.
- **Flag permutations:** `tools/verify_dockerfile_permutations.sh` — p1 (all off, the
  `MINIMAL_IMAGE=1` content) and p2 (every feature but docs, Spyder included) PASS: each group's
  representative package is user-installed exactly when its flag is on. p3 (docs only) was stopped
  unfinished because each build took ~40 minutes under storage-lock contention; the docs-on path is
  covered by the default `make image` above, whose package set matched the old image's.
- **Gates** against the new image: the `make format`, `make type-check` and `make test` recipes all
  exit 0; offline pulled-image path (`--network=none`, no mount, editable reinstall + `pytest`):
  57 passed. The `save`/`load` export round trip was not re-run (this change does not touch it).
