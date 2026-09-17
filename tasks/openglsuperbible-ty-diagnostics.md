# Decide what to do with openglsuperbible's pre-existing ty diagnostics

**Status:** proposed — needs go-ahead (a decision only the maintainer can make)
**Priority:** 7
**Difficulty:** 4
**Started:** 2026-09-17 (William Emerison Six <billsix@gmail.com>) — split from
`tasks/archive/2026/09/17/type-all-ports.md` on its completion, so the recommendation isn't
stranded.

## BLUF

`ports/openglsuperbiblev4` is fully type-annotated (locals + module-level) and enforced by the
annotation checker, but it is **not** in the `ty` step of `make type-check` because it carries
**~101 pre-existing `ty` diagnostics** that are NOT annotation problems — they are glfw/imgui stub
mismatches in faithful port code. Decide whether to fix them, blanket-`# ty: ignore` them, or
leave the tree permanently out of the `ty` step. Only after that can openglsuperbible join the
`ty` step.

## Context

- The type-all-ports work (archived `2026/09/17/type-all-ports.md`) annotated every local and
  module-level variable in openglsuperbible. Those annotations *reduced* the ty diagnostic count
  from **194 → 101** (they resolved 93 and added zero), which is why we know the remaining 101 are
  pre-existing, not annotation-caused.
- The 101 are things like `glfw.set_window_should_close(_window, True)` where the stub wants a
  non-`None` `_GLFWwindow` pointer but the value is `_GLFWwindow | None`, and
  `imgui.set_window_font_scale` / other members the imgui-bundle stubs don't declare. See
  `ports/openglsuperbiblev4/chapt21/fonts/font.py` for representative examples.
- `make type-check` currently runs `ty` over src, tests, and `ports/codetheclassics` only;
  openglsuperbible is annotated + annotation-checked (`--include-module`) but excluded from the
  `ty` step.

## Options

1. **Leave it out of the `ty` step (lowest effort).** Faithful ports; the diagnostics are upstream
   stub friction, not real bugs. Keep the annotation enforcement (already on) and accept ty doesn't
   cover this tree. Recommended unless the maintainer wants full ty coverage.
2. **Blanket-suppress.** Add narrow `# ty: ignore[<rule>]` at each of the ~101 sites (or per-file
   where a whole file is affected), then add openglsuperbible to the `ty` step. Medium effort;
   clutters faithful port code with ignores.
3. **Fix them.** Adjust the calls/None-guards so the stubs are satisfied (e.g. assert the window is
   non-None before glfw calls). Highest effort and risks touching port behaviour / fidelity —
   least aligned with "faithful port".

## Open questions

1. Which option? (Recommendation: option 1 — leave out of the `ty` step; the tree is faithful port
   code and the diagnostics are stub friction, and it's already annotation-enforced.)

## See also

- `tasks/archive/2026/09/17/type-all-ports.md` — the annotation work that surfaced this.
- `CLAUDE.md` › "Coding standard" — notes openglsuperbible is annotated but kept out of the `ty`
  step.
