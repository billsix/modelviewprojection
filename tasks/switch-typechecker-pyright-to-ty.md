# Switch the type checker from pyright to ty (single checker: ty)

**Status:** in-progress (2026-08-23) — **ty wired as the active emacs LSP; pyright kept installed
as a fallback** (Bill's call 2026-08-23, open Q2 → "wire ty, verify, then remove"). Awaiting Bill's
**interactive** verification in `make shell` emacs; the pyright/libatomic/MELPA removal is deferred
until then (see "Remaining" below). Not archived.
**Priority:** 5
**Difficulty:** 3

## Motivation

Standardize on **ty** (Astral) as mvp's only type checker — matching gacalc, which is
ty-clean and uses ty as its gate. Concretely this also removes a real ty-vs-pyright
divergence: gacalc's generated graded types now type their **operators** via
`@typing.overload` (so `v2 * v2 : Rotor2`, `v2 ^ v2 : Bivector2` — see gacalc
gacalc's `tasks/archive/2026/07/21/typed-product-helper-functions.md` (`github.com/billsix/geometricalgebra`)). **ty accepts these overloads; pyright's
stricter `reportIncompatibleMethodOverride` might flag them.** Since mvp consumes those
types, a single ty-based toolchain avoids a checker disagreeing with the library it depends
on.

## Current state (investigated 2026-07-21)

- **The gate already uses ty.** `entrypoint/format.sh` runs `ty check` on `src`, `tests`, and
  the three `ports/codetheclassics/*` trees. It does **not** run pyright. So mvp's CI/format
  gate would *not* hit the pyright-overload issue at all.
- **pyright is used only for interactive editing.** `Dockerfile:128`
  (`… && uv pip install pyright …`) installs it, and the emacs config
  (`entrypoint/dotfiles/.emacs.d/init.el`) wires `lsp-pyright` as the LSP server. So pyright's
  opinion only surfaces in an emacs session, never in the gate.
- `ty` itself is already installed (`Dockerfile:38`, via dnf). No `pyrightconfig.json`,
  no `[tool.pyright]`, no `ty.toml`, no `[tool.ty]` — both run with defaults.

So "switch pyright → ty" is really: **make the interactive editor use ty too, and drop the
now-unused pyright install.** The gate needs no change.

## Plan

1. **Emacs LSP → ty. [DONE 2026-08-23]** `entrypoint/dotfiles/.emacs.d/init.el`: replaced the
   `lsp-pyright` `use-package` stanza with a self-contained custom lsp-mode client that runs
   `ty server` (`lsp-register-client` + `make-lsp-client`, `:server-id 'ty`, `:priority 1`,
   `:activation-fn (lsp-activate-on "python")`). No MELPA package is needed for a custom client,
   so `install-melpa-packages.el` was left untouched (`lsp-pyright` stays there as the fallback
   package). The `lsp-pyright` block was **commented out, not deleted**, with a note on how to flip
   back. The existing `(python-mode . lsp-deferred)` hook in the `lsp-mode` block already starts the
   client on open. Verified the elisp reads cleanly (`emacs --batch` sexp scan). **Did NOT touch the
   vendored `.emacs.d/elpa/` tree.**
2. **Dockerfile + libatomic — DEFERRED (fallback kept).** Not done, on purpose: pyright stays
   installed as the fallback. The removal, once Bill verifies ty interactively, is:
   - `Dockerfile:54` — drop `uv pip install pyright --python /venv/bin/python && \`.
   - `Dockerfile:51-52` — the `libatomic (a pyright runtime dep)` comment.
   - `entrypoint/01-install-base.sh:59-61` — `dnf install -y libatomic` + its comment (it exists
     *only* for pyright; nothing else needs it — reconfirm with a grep at removal time).
   - `install-melpa-packages.el:7` — the `lsp-pyright` package (unused once the fallback is dropped).
   (Task's original line numbers were stale — Dockerfile is ~54, not ~128; corrected here.)
3. **Verify — needs Bill (interactive, can't be done headlessly).** Rebuild the image; `make format`
   still green (ty gate unchanged — it already ran ty, so this can't regress it). Open a source file
   in `make shell`'s emacs and confirm ty diagnostics appear via the LSP. Then confirm gacalc's
   precise operator types (`v2 * v2 : Rotor2`) show correctly (gacalc pin is already 0.0.16, which
   carries the overloads). Once confirmed, do step 2's removals and archive.

## Remaining (blocks archive)

- **Bill:** verify ty's LSP works in emacs (open a `.py`, confirm diagnostics; no pyright process).
- **Then:** do the step-2 removals (pyright pip, libatomic, `lsp-pyright` MELPA entry, restore-note
  cleanup in `init.el`) and archive this task.

## Open questions

1. **Is ty's LSP mature enough for the emacs workflow?** ty ships `ty server` (LSP), but
   `lsp-mode` has no first-class ty client the way it has `lsp-pyright`. **Resolved by
   implementation:** wired a custom `lsp-register-client` for `ty server` (the task's primary
   suggested option), not `eglot`. Whether it's *mature enough in practice* is exactly what Bill's
   interactive verification (step 3) will show — the fallback exists precisely so a "no" is cheap.
2. **Keep pyright as a fallback, or hard-remove?** **Answered 2026-08-23 (Bill): keep as fallback.**
   Wire ty now, verify interactively, then remove pyright — done in that order.

## Not in scope

The gate (`format.sh`) already uses ty — no change there. This task is the editor/LSP + the
Dockerfile cleanup only.
