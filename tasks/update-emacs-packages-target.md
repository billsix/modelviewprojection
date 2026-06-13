# Port the `make update-emacs-packages` Makefile integration to modelviewprojection

**Status:** proposed — needs go-ahead
**Created:** 2026-06-13

> **Lead implementation.** The author considers the shared Emacs-package vendoring approach (same
> "gist" across geometricalgebra / mvp / spimulator / texExpToPng) the **gold standard**, and wants
> mvp done **first** as the model port. Once this lands, the same integration is ported to the other
> vendoring projects (`spimulator/tasks/update-emacs-packages-target.md`,
> `texExpToPng/tasks/update-emacs-packages-target.md`). So: do mvp → review → replicate.

## Goal

Port the one-command "refresh + re-vendor the Emacs `elpa/` tree" Makefile integration that
**geometricalgebra** already has into modelviewprojection: a `make update-emacs-packages` target that
rebuilds the image, wipes + reinstalls the MELPA packages into the host's bind-mounted `elpa/`, strips
the machine-specific compiled artifacts, and force-stages the tree so it's ready to commit.

modelviewprojection vendors the **largest** elpa tree of the family (1229 files, ~22M, tracked in git)
and has the `USE_EMACS`/`ELPA_MOUNT` plumbing, but there is **no ergonomic way to update the vendored
packages** — you'd have to do it by hand in `make shell USE_EMACS=1` and remember the strip +
`git add -f` dance. This task adds the convenience target.

## Reference implementation (copy from here)

geometricalgebra is the worked precedent. Read, in that repo:
- `Makefile` — the `update-emacs-packages` target (`$(MAKE) image USE_EMACS=1` → in-container
  wipe+reinstall → host strip + `git add -A -f`) and the comment block above `ELPA_MOUNT`.
- `tasks/archive/2026/06/07/emacs-package-install-strategy.md` — full rationale (why strip `*.elc`
  **and** `*.eln`; the Dockerfile build-time-install reconciliation).

Note: modelviewprojection already shares geometricalgebra's transform layer (`transforms.py` /
`InvertibleFunction`), so leaning on geometricalgebra's precedent here keeps the two repos consistent.

## How modelviewprojection currently stands

This repo is **structurally identical to geometricalgebra/spimulator** for the elpa workflow, so the
reference recipe ports almost verbatim:

- `Makefile:6` — `USE_EMACS ?= 1` (defaults on; harmless for this target, which forces it anyway).
- `Makefile:50-53` — `ELPA_MOUNT` mounts **just `elpa/`**:
  `-v $(CURDIR)/entrypoint/dotfiles/.emacs.d/elpa:/root/.emacs.d/elpa:U,z`. **Same shape as the
  reference** — so the wipe scopes naturally to `elpa/` and the rest of `.emacs.d/` is left alone.
- `CONTAINER_CMD = podman`, `CONTAINER_NAME = modelviewprojection`.
- `Dockerfile:4` — `ARG USE_EMACS=0` (standard Makefile-`1`/Dockerfile-`0` mirror).
- `Dockerfile:9` — `COPY entrypoint/dotfiles/ /root/` copies the **whole** dotfiles tree (including the
  22M vendored `elpa/`) into the image — **and** `Dockerfile:104-110` *also* runs
  `emacs --batch --load /root/.emacs.d/install-melpa-packages.el` at build time when `USE_EMACS=1`. So
  packages ship **twice** (vendored copy + build-time reinstall), the same redundancy geometricalgebra
  resolved (see Decision 2).
- No `.dockerignore` excluding the tree.
- `install-melpa-packages.el` lives at `entrypoint/dotfiles/.emacs.d/install-melpa-packages.el`.

(The actual git repo is `/billopt/modelviewprojection/modelviewprojection` — one level deeper than the
sibling mounts; this task doc lives in that repo's `tasks/`.)

## Proposed target (tailored to modelviewprojection)

Because `ELPA_MOUNT` is elpa-only, this is a near-verbatim port of geometricalgebra's target with the
container name swapped:

```make
.PHONY: update-emacs-packages
update-emacs-packages: ## USE_EMACS=1: rebuild image, wipe+reinstall elpa, strip *.elc/*.eln, git add -f
	$(MAKE) image USE_EMACS=1
	$(CONTAINER_CMD) run --rm \
		-v $(CURDIR)/entrypoint/dotfiles/.emacs.d/elpa:/root/.emacs.d/elpa:U,z \
		-v $(CURDIR)/entrypoint/dotfiles/.emacs.d/install-melpa-packages.el:/root/.emacs.d/install-melpa-packages.el:ro,z \
		--entrypoint /bin/bash \
		$(CONTAINER_NAME) \
		-c 'set -e; find /root/.emacs.d/elpa -mindepth 1 -delete; \
		    emacs --batch --load /root/.emacs.d/install-melpa-packages.el'
	cd $(CURDIR)/entrypoint/dotfiles/.emacs.d/elpa && \
		find . \( -iname '*.elc' -o -iname '*.eln' \) -delete && \
		git add -A -f .
	@echo "Done: reinstalled packages, stripped *.elc/*.eln, staged elpa -- review and commit."
```

Notes:
- The install script is bind-mounted **read-only** so you can tweak the package list and re-run without
  rebuilding the image.
- `git add -A -f .` overrides any `*.elc`/`*.eln` gitignore patterns so the full tree stages.
- Mirror geometricalgebra's `ELPA_MOUNT` comment block so the use-vs-refresh split is documented at the
  mechanism.

## Decisions to make (do not implement until chosen)

1. **Scope.** Just the `update-emacs-packages` target (recommended first), or also the Dockerfile
   reconciliation (#2)? The target alone is self-contained and low-risk.
2. **Dockerfile redundancy (the "ship twice" question).** geometricalgebra ended up: add
   `entrypoint/dotfiles/.emacs.d/elpa` to `.dockerignore` (stop copying the 22M tree into the image)
   **and** drop the build-time `emacs --batch --load …` install — image carries no Emacs packages, the
   vendored tree is the single source mounted at runtime, and the build is offline w.r.t. MELPA. Should
   modelviewprojection follow suit? If kept, the redundancy is harmless but the build stays online.

## Operational notes

- **Nested podman (running inside the sandbox):** the in-container `podman run` needs
  `--cgroups=disabled` to work nested; the `$(MAKE) image` step builds fine. Per the standing
  arrangement, add the flag transiently at run time — don't commit it into the Makefile.
- **Off-limits:** the vendored `elpa/` *contents* are build artifacts — don't read/edit/reformat them;
  this task only adds the *mechanism* that regenerates them. The author runs the target and commits the
  result deliberately (it rewrites a ~22M tree).
- **Not executed as part of this task** — parse/dry-run-verify only; actually running it rebuilds the
  image and rewrites the vendored tree, the author's call.

## Acceptance

- `make help` lists `update-emacs-packages` with its `##` description.
- The target parses and (dry-run) issues the expected `podman run` + host strip/`git add` steps.
- `ELPA_MOUNT` comment documents the use (`make shell USE_EMACS=1`) vs refresh
  (`make update-emacs-packages`) split.
- If decision #2 is "yes": `.dockerignore` excludes the elpa tree and the build-time install is gone,
  verified by a throwaway build showing `/root/.emacs.d` without `elpa/`.
