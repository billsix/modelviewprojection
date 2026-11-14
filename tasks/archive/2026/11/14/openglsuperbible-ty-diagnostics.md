# openglsuperbible's pre-existing ty diagnostics: kept out of the `ty` step

**Started:** 2026-09-17 (William Emerison Six <billsix@gmail.com>), split from
`tasks/archive/2026/09/17/type-all-ports.md`. **Done:** 2026-11-14.

## Outcome

`ports/openglsuperbiblev4` stays out of the `ty` steps of `make type-check`; the annotation checker
(`tools/check_local_annotations.py --include-module`) keeps covering it. The decision is now recorded
where a reader of the gate meets it: `tasks/reference/tests-and-gates.md` §5 (the decision, the
diagnostics, and the rejected options), the `CLAUDE.md` "Coding standard" parenthetical (points there),
and a comment above the `type-check` target in the `Makefile`.

## Background

The type-all-ports work annotated every local and module-level variable in the tree. That cut the
`ty` diagnostic count from 194 to 101 (93 resolved, none added), which showed the remaining 101 were
not annotation problems. They are glfw/imgui stub mismatches in faithful port code: for example
`glfw.set_window_should_close(_window, True)`, where the stub wants a non-`None` window but the value
is typed `_GLFWwindow | None`, and imgui-bundle members the stubs do not declare
(`imgui.set_window_font_scale`, see `ports/openglsuperbiblev4/chapt21/fonts/font.py`).

## Decision (William Emerison Six <billsix@gmail.com>, 2026-11-14)

Option 1 of three: leave the tree out of the `ty` step. Rationale: the code is a faithful port, the
diagnostics are upstream stub friction rather than bugs, and annotation completeness is already
enforced. Rejected:

- **Blanket-suppress** (~101 narrow `# ty: ignore[<rule>]` sites, then add the tree to `ty`):
  clutters faithful port code with ignores.
- **Fix them** (None-guards and call changes that satisfy the stubs): the most work, and it touches
  port behaviour and fidelity.

Revisit only if the glfw or imgui-bundle stubs improve.
