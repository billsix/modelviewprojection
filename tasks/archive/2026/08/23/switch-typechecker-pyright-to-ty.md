# Switch the type checker from pyright to ty (single checker: ty)

**Status:** complete
**Completed:** 2026-08-23 (William Emerison Six <billsix@gmail.com>). ty wired as the active emacs
LSP and **verified working interactively by Bill**; pyright + its `libatomic` dep + the `lsp-pyright`
MELPA entry then removed.
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
2. **Remove pyright + fallback. [DONE 2026-08-23, after Bill's interactive verify.]**
   - `Dockerfile` — dropped `uv pip install pyright …` and the `libatomic (a pyright runtime dep)`
     comment (the `setuptools wheel` line still ends the block with `&& \`; verified continuation).
   - `entrypoint/01-install-base.sh` — removed `dnf install -y libatomic` + its comment. Grep
     confirmed `libatomic` existed *only* for pyright (no other consumer in our build/config files).
   - `install-melpa-packages.el` — removed the `lsp-pyright` package from the selected set.
   - `init.el` — removed the commented-out pyright fallback block and the fallback wording, leaving a
     clean ty-only comment. Both elisp files re-parsed cleanly (`emacs --batch` sexp scan).
   - **Left the vendored `entrypoint/dotfiles/.emacs.d/elpa/lsp-pyright-*/` tree alone** (off-limits;
     it clears on the next `make update-emacs-packages` now that the install list drops it).
   (Task's original line numbers were stale — the pyright pip was ~54, not ~128.)
3. **Verify. [DONE]** Bill confirmed ty's LSP works in `make shell` emacs. `make format` is
   unaffected (the gate already ran ty). gacalc pin is 0.0.16, which carries the precise operator
   overloads (`v2 * v2 : Rotor2`).

## Note for the future

This lsp-mode version ships a **built-in `lsp-python-ty` client** (seen in `lsp-mode.el`'s client
autoload list) — so the task's premise "lsp-mode has no first-class ty client" is now outdated. The
custom `lsp-register-client` stanza in `init.el` is the *verified-working* one and was kept for that
reason; a future cleanup could switch to the built-in `lsp-python-ty` and drop the custom stanza, but
that's an unforced change and would want its own interactive re-verify.

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
