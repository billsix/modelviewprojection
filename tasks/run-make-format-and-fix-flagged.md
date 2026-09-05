# Run `make format` and fix everything it flags

**Status:** proposed — needs go-ahead (William Emerison Six <billsix@gmail.com>, 2026-09-05)
**Priority:** 4
**Difficulty:** 3

## BLUF

Run mvp's real format gate — `make format` (ruff `check --fix` + `ruff format` + `ty check` across
`src`, `tests`, and the `ports/` tree) **inside the nested container** — and fix every issue it flags
that isn't auto-corrected. "Done" = `make format` exits green, the formatter is idempotent (a second
run reports no changes), and `make test` still passes. This is the verification-via-the-actual-gate
pass over the `codetheclassics-gl1-and-space-refactors` branch's freshly-added code (the games were
claimed ruff+ty clean at write time — this confirms it against the gate the maintainer actually runs).

## Context

- **The gate:** `entrypoint/format.sh`, invoked by `make format` (see `CLAUDE.md` › Code-the-Classics
  ports and the Coding-standard section). It runs `ruff check --fix` + `ruff format` over `src`,
  `tests`, `assignments`, and `ports`, then `ty check` on `src`, `tests`, and the games
  (`vol1`/`vol2`). `line-length = 80` governs both the formatter and E501.
- **What this branch added (the likely source of any flags):** `boing_gl1.py` (~1725 lines) plus the
  soccer / beatstreets / leadingedge / myriapod refactors and the 10 library-ized Code-the-Classics
  games. All byte-identical and claimed ruff+ty clean, but not yet re-run through `make format` on a
  clean checkout.
- **Run it nested:** `make format` (the sandbox exports `NESTED_PODMAN=1`, so `PODMAN_RUN_FLAGS`
  auto-applies `--cgroups=disabled`; per `CLAUDE.md`, on-screen GL can't be verified headless, but
  the format/type gate needs no display).
- **Gotcha — trust the exit code but read the scroll.** `format.sh` accumulates each step's status
  (`… || status=1; exit $status`), so a green `make format` means every step passed — but a prior
  cross-repo bug had a `ty` error printed mid-output while the last step's "All checks passed!" and a
  0 exit hid it. If the exit is green, still scan the output for `ty` diagnostics before trusting it
  (see `CLAUDE.md`-referenced multi-step-gate lesson).

## What to do

1. `make format` in the nested container; capture the full output.
2. Fix everything it flags that `--fix` did not auto-correct — ruff residue and `ty` type errors —
   following the repo coding standard: annotate generously, an externally-defined name overrides the
   naming rules (suppress with a reason at the site), `# ty: ignore` over `# type: ignore`, and the
   `m`/`b` and graph-label exceptions. Don't churn working code beyond what the gate requires.
3. Re-run `make format` until it is green AND idempotent (second run reports no changes).
4. `make test` (in-container pytest) to confirm the fixes didn't break behavior.

## Verification / done-state

- `make format` exits 0, output scanned for stray `ty` errors — none.
- `make format` idempotent (re-run: no file changes).
- `make test` passes.
- Report what was flagged and how each was fixed (bulk auto-fixes vs the judgment-call ones).

## Open questions

None blocking. If the gate surfaces a flag that's a deliberate exception (an externally-fixed name, a
teaching-facing shorthand), suppress-with-reason rather than renaming, and note it in the done report.
