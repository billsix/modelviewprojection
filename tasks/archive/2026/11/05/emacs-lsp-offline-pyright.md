# Emacs Python LSP: switch the editor back to pyright (npm), keep ty as the gate — done-record

**Completed:** 2026-11-05. William Emerison Six <billsix@gmail.com> made the decision ("1 yes") and
gave the go-ahead ("go on … modelviewprojection"). The setup is github.com/billsix/geometricalgebra's
(`tasks/reference/emacs-lsp-setup.md` there), which the maintainer confirmed on 2026-11-05 works as wanted.

## Decision

- **The editor LSP is pyright (npm). `format.sh` and `make type-check` stay on ty.** This reverses only
  the editor half of the 2026-08-23 decision (`tasks/archive/2026/08/23/switch-typechecker-pyright-to-ty.md`).
  In gacalc, ty's completion and parameter hints had proved weaker than pyright's. Pyright's in-editor
  diagnostics can differ from ty's, and that is accepted, because the gate is ty. The decision is
  recorded in `tasks/reference/design-decisions.md`.

## What changed

- **`entrypoint/04-install-emacs.sh`** installs `emacs`, `emacs-gtk+x11`, `emacs-pgtk`, `nodejs` and
  `npm`, then runs `npm install -g pyright`, accumulating the exit status. The mode stays `100755`.
  `python3-lsp-server` was dropped: pylsp has lsp-mode priority -1, so it was never selected.
- **`install-melpa-packages.el`** gained `lsp-pyright`. `elpa/` was re-vendored with
  `make update-emacs-packages`: lsp-mode is now 20261020.1728, and lsp-pyright is 20260507.1742.
- **`init.el`:** the custom `ty server` client stanza was replaced with gacalc's `use-package lsp-pyright`
  block (`typechecking-mode "basic"`, `auto-import-completions t`). The `/mvp/` root pin was kept.
- **Docs:**
  - The `design-decisions.md` entry now reads "ty is the type-check gate; pyright is the Emacs LSP".
  - `tasks/external-editor-remote-dev.md` "Current state" now lists the language servers that are
    actually installed.

## Verification (2026-11-05)

- `make update-emacs-packages` exited 0, after a full image rebuild. The edited Emacs script lives in the
  shared base `RUN`, which sits above every other layer, so every layer was rebuilt.
- The image has `/usr/local/bin/pyright-langserver` and no `pylsp`.
- **Offline headless probe** with the real `init.el`, under `--network=none`, with the repo mounted
  `:ro` and elpa `:O`, on `src/modelviewprojection/mathutils.py`:
  - lsp-mode attached `(pyright ruff)`.
  - Completion of `math.sq` returned `isqrt` and `sqrt`.
  - Signature help inside `math.isclose(` returned the full signature.
- `make format` exited 0, and `make type-check` (ty plus the annotation checker) exited 0. Nothing in
  `src/` changed.
