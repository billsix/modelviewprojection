# Emacs Python LSP: switch the editor back to pyright (npm), keep ty as the gate

**Status:** ready — decision made, implementation needs go-ahead (William Emerison Six <billsix@gmail.com>, 2026-11-05)

**Priority:** 4
**Difficulty:** 3

## BLUF

Emacs here uses ty as its Python language server, through a custom lsp-mode client. In
github.com/billsix/geometricalgebra on 2026-11-04, the maintainer found ty's completion and parameter
hints weaker than pyright's. The fix there was lsp-pyright with an npm-installed pyright, which works
offline, and the maintainer confirmed on 2026-11-05 that it behaves as wanted. This task applies that
setup to the editor only; `ty` stays the `format.sh`/`type-check` gate. Done means that offline, with
`--network=none`, a headless Emacs attaches pyright and ruff and answers both completion and
signature help.

## Context

- **Current state.**
  - `entrypoint/dotfiles/.emacs.d/init.el` registers a custom `ty server` client at priority 1.
  - `lsp-pyright` is not in `install-melpa-packages.el` or the vendored `elpa/`.
  - `entrypoint/04-install-emacs.sh` dnf-installs `emacs` and `python3-lsp-server`. pylsp is never
    selected, because its lsp-mode priority is -1.
- **Why ty was chosen (2026-08-23).** See `tasks/archive/2026/08/23/switch-typechecker-pyright-to-ty.md`:
  one checker, matching gacalc's gate. There was also a worry that pyright's
  `reportIncompatibleMethodOverride` would flag gacalc's `@typing.overload` operators. Two things have
  changed since:
  - gacalc's own Emacs now runs pyright with `typechecking-mode "basic"` against those same operators,
    and its maintainer is satisfied with it.
  - The *gate* question is unaffected: `format.sh` and `make type-check` keep running ty.
  - Pyright's editor diagnostics may still disagree with ty in places. That is accepted, the same as in
    gacalc.
- **How gacalc did it.** Read `tasks/reference/emacs-lsp-setup.md` and
  `tasks/archive/2026/11/04/dockerfile-lean-layers-first.md` in github.com/billsix/geometricalgebra.
  Until the maintainer merges it, that work is on the `emacs-python-lsp-investigation` branch. The rules
  it settled:
  - Install pyright with **npm**. The pip `pyright` package is only a launcher that downloads Node and
    the server on first use in each fresh container, so it fails offline. mvp's pre-2026-08-23 setup
    used that pip launcher.
  - lsp-mode shows parameter hints when you type `(` or `,`, and on demand with
    `M-x lsp-signature-activate`.

## Plan

1. **`entrypoint/04-install-emacs.sh`:** add `nodejs npm` to the dnf line and drop `python3-lsp-server`,
   which is unused. Then add `npm install -g pyright`. That makes the script two commands, so accumulate
   their exit statuses (`s=0; … || s=1; …; exit $s`), as github.com/billsix/towersofhanoi
   `python/entrypoint/04-install-emacs.sh` does. Update the header comment, and restore `+x`
   (`git add --chmod=+x`).
2. **`install-melpa-packages.el`:** add `lsp-pyright` after `lsp-mode`. Then run
   `make update-emacs-packages` to re-vendor `elpa/`. The vendored elpa tree must not be hand-edited.
3. **`init.el`:** replace the custom `ty server` client stanza and its comment with gacalc's
   `use-package lsp-pyright` block (`typechecking-mode "basic"`, `auto-import-completions t`). Keep the
   `/mvp/` root pin.
4. **`make image`** (`USE_EMACS=1`, the Makefile default).
5. **Verify offline.** Run a headless Emacs that loads the real `init.el` in the image, using the probe
   pattern from gacalc's history (`tasks/adhoc/emacs-python-lsp-investigation/`, removed when that task
   was archived):
   - Mount the repo `:ro` and the elpa tree `:O` (overlay).
   - Run under `--network=none`.
   - Require servers `(pyright ruff)` on a `src/` file.
   - Check that completion after a module attribute returns members.
   - Check that `lsp-signature-activate` inside a call returns a signature.
6. **Run the gates:** `make format` and `make type-check`. Both stay ty-based, and nothing in `src/`
   should change.
7. **Update the docs:** the `design-decisions.md` entry for the 2026-08-23 ty switch, which should say
   that ty remains the gate and pyright is the editor LSP from this change on, and any `CLAUDE.md` or
   reference text that names ty as the Emacs LSP. Both go in the same staging.

## Decisions

- **Editor LSP → pyright (npm); `format.sh` and `make type-check` stay on ty.** Reverses only the editor half of
  the 2026-08-23 decision. Decided by William Emerison Six <billsix@gmail.com>, 2026-11-05, after the same setup
  worked as wanted in gacalc.
