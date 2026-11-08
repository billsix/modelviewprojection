# Anchor the `.dockerignore` cache patterns with `**/`

Done 2026-11-08 (William Emerison Six <billsix@gmail.com> asked for it), on branch
`dockerignore-anchor-patterns`.

## What changed

`.dockerignore` patterns are anchored at the context root, unlike `.gitignore`, so `__pycache__/`,
`*.py[cod]`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/` and `.ipynb_checkpoints/` excluded only
top-level matches. The `Dockerfile` bakes the source with `COPY . /mvp`, so the host's nested caches went
into every image. The patterns are now `**/`-prefixed, with a comment saying why; `build/`, `dist/` and
`output/` stay root-only. Found while adding `.dockerignore` to github.com/billsix/methodfinder; the rule
is in the Dockerfile contract's `.dockerignore` bullet (personal overlay, github.com/billsix/dotfiles
`.ai-coding-conventions.personal.md`).

A stale `git am` session (one patch, "added task to migrate to doctests", already committed) blocked
the branch switch; it was cleared with `git am --quit` at the maintainer's request, leaving `master`
unchanged at `d8377514`.

## Verification (2026-11-08, nested podman)

A probe build with this repo as context (`FROM fedora:45`, `COPY . /ctx` like the real `COPY . /mvp`,
then a `RUN` counting files):

| | `__pycache__` | `.pyc` | `.egg-info` | `elpa/` | `.git` |
|---|---|---|---|---|---|
| before | 126 | 241 | 1 | 0 | 0 |
| after | 0 | 0 | 0 | 0 | 0 |

A full `make image` was not run: only exclusions changed, the probe performs the same `COPY .`, and
none of the newly excluded paths is named by a `COPY`.
