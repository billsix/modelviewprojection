# Anchor the `.dockerignore` cache patterns with `**/`

**Status:** in progress. Created 2026-11-08 (William Emerison Six <billsix@gmail.com> asked for it).
**Priority:** 3
**Difficulty:** 1

## BLUF

`.dockerignore` patterns are anchored at the context root, unlike `.gitignore`, so `__pycache__/`,
`*.py[cod]` and `*.egg-info/` exclude only top-level matches. The host's nested `__pycache__`
directories (126 on 2026-11-08) and `src/*.egg-info` and anything else under the baked `COPY . /mvp` reach every directory `COPY`. Prefix them with
`**/`. Done = a probe build that copies the whole context finds no `__pycache__`, `.pyc` or
`.egg-info`, and still finds no `elpa/` or `.git`.

## Context

- Found while adding `.dockerignore` to github.com/billsix/methodfinder: its image kept
  `src/methodfinder/__pycache__` until the pattern became `**/__pycache__/`. The rule is in the
  Dockerfile contract (personal overlay, github.com/billsix/dotfiles `.ai-coding-conventions.personal.md`).
- Same patterns to anchor: `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`,
  `.ipynb_checkpoints/`. `build/` and `dist/` stay root-only (that is where they appear).

## Plan

1. Probe before: `podman build --no-cache -f <probe>/Dockerfile .`, where the probe is
   `FROM fedora:45`, `COPY . /ctx`, then a `RUN` that counts `__pycache__`/`.pyc`/`.egg-info`/elpa/.git.
2. Anchor the patterns, with a comment on why.
3. Probe after: all counts 0.
