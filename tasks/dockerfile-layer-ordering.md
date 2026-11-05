# Dockerfile: order layers so an edited script or a toggled flag doesn't rebuild TeX and ePiX

**Status:** proposed — needs go-ahead
**Priority:** 4
**Difficulty:** 3
**Started:** 2026-11-05 (William Emerison Six <billsix@gmail.com>)

## BLUF

Editing `entrypoint/04-install-emacs.sh` on 2026-11-05 forced a full image rebuild: every package
group, TeX Live, tex-expression-to-png, the requirements install, and the ePiX build. Restructure the
`Dockerfile` the way github.com/billsix/geometricalgebra's was restructured (its
`tasks/archive/2026/11/04/dockerfile-lean-layers-first.md`): slow and rarely changed layers first,
each optional group in its own `RUN`, each `ARG` declared right before the first layer that reads
it. Done means: editing a cheap group script (Emacs, Jupyter, Spyder) or toggling its flag rebuilds
only that group's layer and the cheap layers after it, and the built package set is unchanged.

## Context

- **Read first:** `Dockerfile`, `entrypoint/0N-install-*.sh`, `.dockerignore`,
  `tasks/reference/container-source-and-mounts.md`, and the cross-project RUN-ordering rule
  ("order `RUN` layers least-volatile-first", in the maintainer's personal conventions overlay).
- **What busts the cache today** (2026-11-05 reading of `Dockerfile`):
  1. `ARG BUILD_DOCS USE_EMACS USE_JUPYTER USE_SPYDER USE_X_WINDOWS` are all declared at the top.
     A build-arg's value is in the cache key of every later `RUN` (measured with podman in gacalc on
     2026-11-04), so toggling any one rebuilds everything below it.
  2. `COPY entrypoint/dotfiles/ /root/` and `COPY entrypoint/*.sh /usr/local/bin` run before the
     first `RUN`. Editing **any** entrypoint script (`format.sh`, `shell.sh`, `entrypoint.sh`, an
     install script) or any dotfile (`init.el`, `.extrabashrc`) invalidates every layer.
  3. One `RUN` does base, docs (TeX), X, Emacs, Jupyter, Spyder, the tex-expression-to-png build, the
     venv, the Jupyter and Spyder config, the `.bashrc`/history seeding, and the requirements install.
     Any change to any part reruns all of it.
- **Already done right:** `GACALC_VERSION`, `USE_EPIX`/`EPIX_COMMIT` and `COPY . /mvp` are late,
  with their own `ARG`s and their own `COPY` of just what they read. Keep that.

## Plan

1. Order the layers by cost and volatility, roughly: base (dnf) → docs (TeX) + tex-expression-to-png
   → X → venv + setuptools/wheel → requirements → ePiX → Jupyter → Spyder → Emacs → dotfiles and
   history seeding → gacalc sdist → `COPY . /mvp`. Confirm the order by timing each layer in a build
   log, not by guessing. Check first whether the requirements install needs any package from a group
   placed after it.
2. `COPY` each install script just before its own `RUN`, instead of `COPY entrypoint/*.sh` up front.
   Move the dotfiles `COPY` and the `.bashrc`/history seeding to the end, above `COPY . /mvp`.
   Scripts that are bind-mounted at run time (`shell.sh`, `format.sh`) may not need baking at all.
   Check the Makefile mounts before dropping any of them.
3. Declare each `ARG` immediately above the first `RUN` that reads it. `BUILD_DOCS` is read twice
   (the docs group and tex-expression-to-png), so keep those two in adjacent layers.
4. Split the Jupyter and Spyder config out of the venv `RUN` into their groups' layers, each under
   its own flag check. Packages stay in the group script, config stays in the Dockerfile.
5. Move the logic comments with the code they explain, and leave a one-line breadcrumb at each `RUN`.

## Verification

- **Package-set identity:** diff `rpm -qa | sort` and `/venv/bin/pip freeze` between the old and new
  images, both built with the Makefile defaults. They must be identical (versions may move only if
  the two builds happen on different days; build both the same day).
- **Cache behaviour:** after a full build, touch `entrypoint/04-install-emacs.sh` and rebuild. Only
  the Emacs layer and the layers after it may rerun; TeX and ePiX must show `Using cache`. Repeat
  for one flag toggle (`USE_SPYDER=1`).
- **Flag permutations:** `make image MINIMAL_IMAGE=1` and the default build both succeed, and each
  group's sentinel package is present only when its flag is on.
- **Gates:** `make format` and `make type-check` exit 0, and the offline export test from
  `tasks/reference/container-source-and-mounts.md` still passes (pulled-image path without a mount).

## Open questions

None.
