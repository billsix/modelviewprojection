# Explore: fewer Makefile targets, work moved to scripts (run in- or out-of-container)

**Status:** proposed — needs go-ahead. **Exploratory; the maintainer may decide NOT to do this
after reading the research below.** Follow-up after v0.0.3.
**Priority:** 7
**Difficulty:** 6
**Started:** 2026-09-18 (William Emerison Six <billsix@gmail.com>)

## BLUF

Now that the image bakes the Makefile + source (`tasks/reference/container-source-and-mounts.md`),
consider whether the Makefile should be **leaner**: most of the "work" targets become committed
**shell scripts** runnable both **in-container** (directly, or via `make shell-exec`) and **from the
host** (a thin wrapper that `podman run`s them), so the number of real targets shrinks to a small
core (`image`, `shell`, `shell-exec`, and a few others). This doc researches feasibility and
tradeoffs and gives a recommendation — but the decision is the maintainer's, and a plausible outcome
is **"don't do it"** (see "The case against").

## Context — the current Makefile (20 targets, categorized 2026-09-18)

- **Container-run "work" targets** (each is `$(CONTAINER_CMD) run … -c '<cmds>'`): `format`,
  `type-check`, `test`, `check-regions`, `book`, `html`, `jupyter` (interactive). These are the
  candidates to become scripts.
- **Dispatchers / entry (keep):** `shell` (interactive TTY), `shell-exec` (batch: already "run a
  script/command in the container env").
- **Host / image management (must stay Make/host):** `image`, `image-export`, `image-import`,
  `image-push`, `release` (git tag), `release-tarball`, `check-format` (host `git diff` wrapper),
  `clean` (host `rm`), `update-emacs-packages` (host podman + git), `help`, `all` (meta).

So the realistic "collapsible" set is ~7 container-run work targets; the ~10 host/dispatcher/image
targets stay regardless.

## Two facts that temper the motivation (read before assuming this is worth it)

1. **Baking the Makefile in does NOT create a need to run `make` inside the container.** Inside the
   container you run the tools directly (`pytest`, `ruff`, `format.sh`, `ty`), or `make shell-exec`
   gets you there from the host. A container-run target executed *inside* the container would try to
   `podman run` again (recursive/broken). So "run in- or out-of-container" is really about **the work
   scripts** being dual-runnable, not about `make` itself running in both places. The baked Makefile
   is the *trigger* for this thought, not a hard driver.
2. **`shell-exec` already provides the "run a command/script in the container" path.** e.g.
   `make shell-exec CMD='pytest'` ≈ `make test`; `make shell-exec CMD='format.sh'` ≈ `make format`.
   So the capability the refactor chases largely exists; the question is whether to *drop the named
   targets* in favor of it.

## Options

- **A — Extract each container-run body into a committed script, keep a thin Make wrapper.** e.g.
  `tools/ci/run-tests`, `tools/ci/typecheck`, reuse `format.sh`; the Make target becomes
  `shell-exec`-of-that-script. Scripts are the source of truth, runnable directly in-container; the
  host keeps `make test`/`make format` UX + `make help` discoverability. Incremental (it *extends*
  the existing `format.sh`/entrypoint-script pattern). **Recommended if anything is done.**
- **B — Drop most targets; use `make shell-exec SCRIPT=…`/`CMD=…`.** Smallest Makefile, but loses
  `make help` discoverability and the short `make test` ergonomics; every routine action becomes a
  longer invocation. Fights the established template hardest.
- **C — Context-detecting targets** (each target checks "am I in the container?" and runs the tool
  directly vs `podman run`). Keeps `make <target>` working everywhere, but adds branching to every
  target and is more machinery than the problem warrants.
- **D — Keep as-is.** The container-per-project template is host-driven by design.

## The case against (why the maintainer might decline)

- **Cross-project blast radius.** The Makefile/Dockerfile *contract* is defined in
  `dotfiles/.ai-coding-conventions.personal.md` ("Makefile contract" + "Self-contained images + live
  source"): a Makefile of `podman run` targets **plus** `shell-exec` for batch. That contract is
  shared across every template project. Restructuring targets → scripts changes the contract fleet-
  wide — a large, cross-repo churn for modest gain.
- **The gain is modest.** `shell-exec` already covers batch; `make help` + short target names are
  good UX that a script-only model loses; the current targets are thin already (one `podman run`
  each).
- **Duplication is already handled where it mattered** (`format.sh`, the `0N-install-*.sh` group
  scripts, `entrypoint.sh`) — the multi-line bodies that most deserve extraction largely already are
  scripts.

## Recommendation (for the maintainer to weigh)

If the goal is a leaner Makefile, do the **conservative A**: extract only the *multi-line*
container-run bodies (`type-check`'s inline `ty … && checker` block is the main one; `format`/`test`
are already essentially one script/one command) into committed scripts under `tools/` or
`entrypoint/`, and have the thin target `shell-exec` them — keeping every current target name and
`make help`. Do **not** collapse to a 3-target Makefile (B): it fights the template and hurts UX for
little benefit. If the Makefile isn't actually bothering the maintainer, **D (keep as-is)** is a
legitimate outcome — flag it and stop. Either way, decide at the contract level first
(`dotfiles/.ai-coding-conventions.personal.md`), because whatever is chosen should apply to all
template projects, not just mvp.

## Open questions

1. Which option (A conservative / B / C / D)? Recommendation: A-conservative or D.
2. If A: where do the extracted scripts live — `tools/` (repo tooling) or `entrypoint/` (alongside
   `format.sh`)? Recommendation: `tools/` for CI/dev scripts, `entrypoint/` only for image-lifecycle
   scripts.
3. Is this a per-project change or a change to the shared template contract in
   `dotfiles/.ai-coding-conventions.personal.md`? (Recommendation: decide at the contract level.)

## See also

- `tasks/reference/container-source-and-mounts.md` — the baked-source design that prompted this.
- `dotfiles/.ai-coding-conventions.personal.md` — where the Makefile contract is defined.
- `runClaudeInContainer/tasks/reference/shell-exec-and-container-template.md` — the `shell-exec`
  design this would lean on.
