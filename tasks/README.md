# Tasks — modelviewprojection

Lightweight session task tracker (per the global `~/.claude/CLAUDE.md` convention:
one `tasks/<slug>.md` per task, check this dir at session start). Detailed specs
live alongside this list as `tasks/<slug>.md`; completed tasks move to
`tasks/archive/<YYYY>/<MM>/<DD>/`. **Ports work is parked** at Bill's request
(still tracked under `tasks/ports-*.md`).

Start here for orientation: [`codebase-overview.md`](codebase-overview.md) —
structure, the InvertibleFunction/Cayley-graph abstraction, the demo arc, the
container/build pipeline, and what I can/can't do in this container.

## Book ↔ code drift audit (whole book)

Three trackers, one per chapter range; doc-region wiring is intact throughout, so
findings are prose / captions / hand-written code / a handful of real code bugs.

| Range | Tracker | Per-finding plans |
|------|---------|-------------------|
| ch1–6 | [`book-code-drift-ch1-6.md`](book-code-drift-ch1-6.md) | natural-basis, is_clockwise, ch05-section, ch02/03-typos |
| ch7–15 | [`book-code-drift-ch7-15.md`](book-code-drift-ch7-15.md) | per-chapter detail folded into the tracker (ch15 was a satellite, now inline); cross-cutting below |
| ch16–21 + perspective | [`book-code-drift-ch16-21.md`](book-code-drift-ch16-21.md) | per-chapter detail folded into the tracker (ch16/17/18/20/21 were satellites, now inline); cross-cutting below |

**Cross-cutting plans (span ranges):**
✅ [`archive/book-explain-natural-basis.md`](archive/book-explain-natural-basis.md) (headline — DONE; e_1/e_2/e_3 now introduced 2D in ch05, 3D in ch14) ·
✅ [`archive/fix-method-vs-function-wording.md`](archive/fix-method-vs-function-wording.md) (DONE) ·
✅ [`archive/fix-mathutils-latex-and-error-strings.md`](archive/fix-mathutils-latex-and-error-strings.md) (DONE) ·
✅ [`archive/fix-is-clockwise-recursion.md`](archive/fix-is-clockwise-recursion.md) (DONE) ·
✅ [`archive/fix-demo-code-bugs.md`](archive/fix-demo-code-bugs.md) (DONE — demo14 `zero`, demo21 imports) ·
✅ [`archive/ch05-translate-section-fixes.md`](archive/ch05-translate-section-fixes.md) (DONE) ·
✅ [`archive/ch02-ch03-prose-typos.md`](archive/ch02-ch03-prose-typos.md) (DONE)

**Verified code bugs surfaced by the audit (highest value):** `is_clockwise`
recursion · `uniform_scale`/`scale_non_uniform` LaTeX-repr · "Note invertible"
typos · `demo14.py:42 zero = Vector3D.e_3()` · `demo21.py` missing `sys`/`os`.

## Other active (non-port)

| Task | Status | Doc |
|------|--------|-----|
| **Migrate mvp math onto `gacalc`** (delete overlapping vector/transform math, import gacalc vectors; rebuild graphics-only math on top) | proposed — needs go-ahead. Scope DECIDED: Path Y (port the 13 ports, no compat type) + rewrite ch05/06/14 on gacalc. Blocks on a gacalc PyPI release (animation layer) | [`gacalc-math-migration.md`](gacalc-math-migration.md) |
| **Extract duplicated demo helpers** into per-concept modules (teach-once-then-import) | in progress — `shading.py` ✅, `windowing.py` (`on_key`) ✅, `clipping.py` (`draw_in_square_viewport`) ✅; `set_mvp_uniforms` variant deferred | [`../tasks/extract-duplicated-demo-helpers.md`](../tasks/extract-duplicated-demo-helpers.md) |
| **Separate data generation from rendering** in SuperBible ports (precompute trig into `_primitives` builders) | ✅ complete 2026-05-29 — archived (~30 demos converted; leave-alone set documented; spot-checked by Bill) | [`archive/extract-data-generation.md`](archive/extract-data-generation.md) |
| **Cube-map sphere reflection doesn't track the camera** (ch09 port bug) | ✅ complete 2026-06-01 — archived (multitexture fixed; texgen/thundergl/fboenvmap audited as N/A) | [`archive/cubemap-reflection-static.md`](archive/cubemap-reflection-static.md) |
| **Make shadow-map depth values visually distinguishable** (ch14/ch18 debug view) | not started — investigated; plan ready, approach TBD w/ Bill | [`shadowmap-depth-discrimination.md`](shadowmap-depth-discrimination.md) |
| **Move keyboard render-options to imgui** (mode toggles/shader-select/etc. → checkboxes/combos) | ✅ complete 2026-06-01 — archived (all 18 demos converted; Bill verified) | [`archive/ports-render-options-to-imgui.md`](archive/ports-render-options-to-imgui.md) |
| **Mirror every keyboard control in an imgui menubar** (94 demos) | ✅ complete 2026-06-02 — archived (all 94 demos have a top menubar; texture-state fallout swept) | [`archive/ports-mirror-keyboard-in-imgui.md`](archive/ports-mirror-keyboard-in-imgui.md) |
| **hdrbloom crashes on startup** (after-glow PBO allocated 1 byte) | ✅ complete 2026-06-02 — archived (sized the PBO in setup_rc; Bill confirmed run) | [`archive/hdrbloom-pbo-sizing-crash.md`](archive/hdrbloom-pbo-sizing-crash.md) |
| **pixbufobj + texfloat runtime crashes** (PBO readback / float-texture segfault) | not started — root-caused; pre-existing, surfaced during imgui verify | [`ports-pbo-floattex-runtime-crashes.md`](ports-pbo-floattex-runtime-crashes.md) |
| De-duplicate per-demo `handle_inputs` (the camera-walk sub-block) | ✅ complete 2026-06-01 — 13 demos now share `walk_around_camera`; orbit demos converted to walk-around | [`../tasks/archive/2026/06/01/dedup-handle-inputs.md`](../tasks/archive/2026/06/01/dedup-handle-inputs.md) |
| Investigate `_face_normal` taking/returning `Vector3D` (vs the current tuple in/out) | investigation task (not started) | [`../tasks/face-normal-vector3d-io.md`](../tasks/face-normal-vector3d-io.md) |
| Confirm PDF + EPUB build green after inlinetex migration | blocked-on-Bill (needs build container) | [`finish-pdf-epub-build.md`](finish-pdf-epub-build.md) |
| Curriculum math: planar-shadow matrix in `pyMatrixStack` | planned | [`../tasks/planar-shadow-matrix.md`](../tasks/planar-shadow-matrix.md) |
| Curriculum math: `rotate_around_axis` in `pyMatrixStack` (decomposed, not Rodrigues) | planned | [`../tasks/rotate-around-axis.md`](../tasks/rotate-around-axis.md) |
| demo22 light-radius imgui slider | planned | [`../tasks/demo22-light-radius-imgui.md`](../tasks/demo22-light-radius-imgui.md) |

## Backlog (from root `TODO.org`, not yet broken out)

- Rename `rotate`/`translate`/`scale` → `R`/`T`/`S` notation (imports + code + book), and add an explanation of `I` (identity) and `T`/`R`/etc.
- Modernized demos `demo22a`/`demo23`/`demo24` (pyramid/litjet/sphereworld) exist in `src/` but have **no book chapters** (toctree stops at `ch21`).
- Many per-chapter prose/diagram improvements (ch1–22) enumerated in `TODO.org`.

## Conventions in this repo
- `tasks/` (here) = active work, one `<slug>.md` per task (the cross-session tracker).
- `tasks/archive/<YYYY>/<MM>/<DD>/` = completed tasks, dated by completion; git
  history is the rest of the record. (No separate `plans/` dir or `HANDOFF-*` files.)
- I can edit code/docs and `git add` to stage; **no commits** (Bill GPG-signs
  outside the container), **no graphical/GL runs**, **no doc build** (no
  `texExpToPng` locally).
</content>
