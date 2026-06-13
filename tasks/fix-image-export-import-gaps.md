# Bring mvp's `image-export` / `image-import` up to the standard convention

**Status:** proposed — needs go-ahead
**Created:** 2026-06-13

## Goal

modelviewprojection is the *original* home of the `image-export` / `image-import` target pair (it's the
reference the other projects are copying). But its copy predates the standardized convention now
recorded in `~/.claude/CLAUDE.md` ("Makefile contract") and has three small gaps. Fix them so mvp
matches the convention the rollout uses.

## Current code (`Makefile`)

```make
image-export: ## export the OCI image
	podman save $(CONTAINER_NAME) -o $(CONTAINER_NAME)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

image-import: ## import the OCI image, "make image-import FILE=foo.tar"
	podman load -i $(FILE)
```

## The three gaps

1. **Hardcoded `podman`** instead of `$(CONTAINER_CMD)` — mvp defines `CONTAINER_CMD = podman` and uses
   it everywhere else; these two targets are the odd ones out.
2. **No `.PHONY`** declarations — every other real target in this Makefile is `.PHONY`; these aren't.
3. **Exported tars aren't gitignored** — `podman save` drops a multi-hundred-MB
   `modelviewprojection-<timestamp>.tar` in the repo root, and nothing in `.gitignore` excludes it, so
   it's one stray `git add` away from being committed.

## Proposed fix

```make
.PHONY: image-export
image-export: ## export the OCI image to a timestamped tar in the repo root
	$(CONTAINER_CMD) save $(CONTAINER_NAME) -o $(CONTAINER_NAME)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

.PHONY: image-import
image-import: ## import an OCI image tar: make image-import FILE=foo.tar
	$(CONTAINER_CMD) load -i $(FILE)
```

And add to `.gitignore`:

```
modelviewprojection-*.tar
```

(or the broader `*.tar` if you prefer — there are no other tracked `.tar` files in the repo).

## Notes

- Pure cleanup; no behavior change beyond honoring `CONTAINER_CMD` and protecting against an accidental
  commit of the export artifact.
- `save`/`load` start no container, so nothing here needs `--cgroups=disabled` to run nested.

## Acceptance

- The two targets use `$(CONTAINER_CMD)` and are each `.PHONY`.
- `modelviewprojection-*.tar` (or `*.tar`) is gitignored; a `make image-export` followed by
  `git status` shows the tar as ignored, not untracked.
- `make help` still lists both with `##` descriptions.
