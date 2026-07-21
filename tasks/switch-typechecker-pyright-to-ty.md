# Switch the type checker from pyright to ty (single checker: ty)

**Status:** proposed — needs go-ahead. Created 2026-07-21 (Bill).

## Motivation

Standardize on **ty** (Astral) as mvp's only type checker — matching gacalc, which is
ty-clean and uses ty as its gate. Concretely this also removes a real ty-vs-pyright
divergence: gacalc's generated graded types now type their **operators** via
`@typing.overload` (so `v2 * v2 : Rotor2`, `v2 ^ v2 : Bivector2` — see gacalc
`tasks/.../typed-product-helper-functions.md`). **ty accepts these overloads; pyright's
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

1. **Dockerfile:** remove `uv pip install pyright` (line ~128). Check whether the adjacent
   `dnf install -y libatomic` on that line was there *for* pyright (a Node runtime dep); if
   nothing else needs it, remove it too — otherwise keep it and just drop the pyright pip.
2. **Emacs LSP → ty.** Point `init.el` at ty's language server (`ty server`) instead of
   `lsp-pyright`. Options to evaluate: an `lsp-mode` client for ty (may need a small custom
   `lsp-register-client` stanza, since `lsp-pyright` is python-specific), or `eglot` with
   `ty server`. Remove `lsp-pyright` from the MELPA package list
   (`entrypoint/dotfiles/.emacs.d/install-melpa-packages.el`) once it's no longer referenced.
   **Do NOT edit the vendored `.emacs.d/elpa/` package tree** (off-limits, committed on
   purpose) — only the config (`init.el`) and the install list.
3. **Verify:** rebuild the image; `make format` still green (ty gate unchanged); open a source
   file in `make shell`'s emacs and confirm ty diagnostics appear via the LSP (and pyright no
   longer runs). Then confirm gacalc's precise operator types (`v2 * v2 : Rotor2`) show
   correctly once mvp bumps its gacalc pin to a release carrying the overloads.

## Open questions

1. **Is ty's LSP mature enough for the emacs workflow?** ty ships `ty server` (LSP), but
   `lsp-mode` has no first-class ty client the way it has `lsp-pyright`. Need to confirm a
   clean integration (custom `lsp-mode` client vs `eglot`) before dropping pyright, or keep
   pyright installed-but-unwired as a temporary fallback.
2. **Keep pyright as a fallback, or hard-remove?** Recommendation: wire ty first, verify it
   works interactively, *then* remove the pyright install — not the reverse.

## Not in scope

The gate (`format.sh`) already uses ty — no change there. This task is the editor/LSP + the
Dockerfile cleanup only.
