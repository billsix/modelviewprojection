# Trim modelviewprojection's CLAUDE.md (46,827 B ≈ 11.7K tok, loaded every session)

**Status:** Done — trimmed 2026-09-13 (archived 2026-09-14)
**Priority:** 3
**Difficulty:** 3

## Result (2026-09-13)

- **CLAUDE.md: 46,827 B → 10,885 B** (~77% cut, well under the ~13–15 KB target).
- **Python coding standard** relocated to the shared cross-project doc
  `runClaudeInContainer/tasks/reference/python-coding-standard.md` (canonical:
  github.com/billsix/runClaudeInContainer); mvp-specific rules/examples merged there under a
  new "modelviewprojection-specific additions" section (line-length=80-for-PDF,
  per-file-ignores reasons, wx externally-defined-name boundary, book-shorthand naming +
  graph-to-code comment rule, `@`-vs-`compose` composition style, the
  `matrix_stack.get_current_matrix` match/case_ worked example, new-vs-existing code,
  deliberate demo duplication). CLAUDE.md now points there + keeps ≤5 mvp invariants inline.
- **Content relocated (verbatim, verified landed before cutting):** Central abstraction detail
  + Pedagogical arc + Assignments → `architecture-overview.md` (§6/§7) & `demo-chapter-inventory.md`;
  gacalc-migration + gacalc-bump changelog → `design-decisions.md`; SuperBible port plan →
  `superbible-ports-guide.md`; MARKER mechanism + JupyterLab defaults + gacalc sdist pipeline →
  `book-and-docs-pipeline.md` (§2–3); texExpToPng SHA-pin + throwaway-container recipe + CtC
  audio/Rect/gacalc-costs → `notable-subsystems.md`; CtC rule-set/dialect/composition/frozen-vector
  audit → `code-the-classics-tightening.md` & `tests-and-gates.md`; the (c) GL conventions →
  `gl-and-imgui-gotchas.md` §7 (header note repointed).

## BLUF
mvp's `CLAUDE.md` is 46,827 B (~11.7K tokens) and is spliced into the AI's context on
every session/turn, so it costs that budget continuously. Most of its bulk is durable
detail — design rationale, deep mechanics, a curated task log, and gacalc-bump history —
that already lives in (or belongs in) `tasks/reference/`, and much of it duplicates docs
that exist. This task trims `CLAUDE.md` to a lean, operational core (~13–15 KB) that
points at reference docs, moving nothing that isn't already captured or captured here.

## Context
- **Why:** `CLAUDE.md` loads every session/turn, so every kilobyte is a recurring context
  tax — not a one-time read. Measurement method and worked numbers:
  runCrushInContainer `tasks/reference/crush-context-assembly.md` (geometricalgebra's
  74,732-byte CLAUDE.md measured at ~18,683 tok/turn, 47% of Crush's system prompt,
  2026-09-13). mvp is smaller at 46,827 B ≈ 11.7K tok but the same problem.
- **Current CLAUDE.md size:** 46,827 B ≈ 11.7K tok. **`@`-imports: none** (no bare
  `@path` lines — nothing to preserve on that front).
- **Convention (maintainer's own, cross-project CLAUDE.md):** "keep `CLAUDE.md` lean and
  push detail into `tasks/reference/`." `tasks/reference/` is the expanded, on-demand,
  agent-facing companion; `CLAUDE.md` is the always-loaded lean layer. This task is that
  convention applied to mvp.
- **This is a PLANNING doc** — it proposes the stay/move split; it does NOT edit
  `CLAUDE.md` or move anything. Execution is a follow-up after go-ahead.
- **Existing `tasks/reference/` docs (20)** — most MOVE targets already exist, so the work
  is mostly *deletion of duplication* plus a couple of small new/updated docs:
  `architecture-overview.md`, `book-and-docs-pipeline.md`, `book-figures-and-images.md`,
  `code-the-classics-tightening.md`, `coordinate-spaces-in-code-the-classics.md`,
  `demo-chapter-inventory.md`, `design-decisions.md`,
  `gacalc-symbolic-transforms-and-lambdify.md`, `gacalc-transforms-in-the-renderer.md`,
  `gl-and-imgui-gotchas.md`, `glossary-authoring.md`,
  `library-not-framework-authorship-style.md`, `lighting-and-shading.md`,
  `notable-subsystems.md`, `notebook-sphinx-integration.md`,
  `pgzero-gl-design-for-a-personal-learning-library.md`, `point-type-decision.md`,
  `superbible-ports-guide.md`, `tests-and-gates.md`.
- Also relevant: `tasks/apply-python-coding-standard.md` (31 KB task doc) already holds the
  coding-standard detail; the coding-standard section in `CLAUDE.md` largely duplicates it
  and the sibling geometricalgebra repo's copy.

## Stay vs move (section-by-section)

| CLAUDE.md section (heading) | ~bytes | Verdict | Destination |
|---|---|---|---|
| Intro — "This is modelviewprojection…" (what it is, mistake-driven, external sources) | ~1,090 | STAY | CLAUDE.md (this is the one-paragraph "what this is") |
| `## Central abstraction — Cayley graphs + InvertibleFunction` | 3,501 | TRIM | CLAUDE.md keeps ~6 lines (the abstraction in one breath + "speak in edges/paths/inverses, never multiply matrices"); the gacalc-migration `Note` blocks, the `mathutils` de-façade history, and the primitive/FunctionStack enumeration → `tasks/reference/architecture-overview.md` + `design-decisions.md` (mostly already there — verify, then cut) |
| `## Pedagogical arc (demo01 → demo24)` | 2,475 | MOVE | `tasks/reference/demo-chapter-inventory.md` / `architecture-overview.md` (already cover the arc); keep a 2-line pointer |
| `## SuperBible port plan` | 1,265 | MOVE | `tasks/reference/superbible-ports-guide.md` (exists); keep a 1-line pointer + the "confirm slot before porting" rule |
| `## How to apply` | 1,744 | STAY (trim) | CLAUDE.md — these are the operational "while working" guardrails (edge/path vocabulary, match demo-era style, unpack vectors into GL). Keep; can tighten the vector-unpack bullet to one line + pointer to the test |
| `## Dev environment` | 378 | STAY | CLAUDE.md (short, operational: Fedora host caveat, never edit vendored elpa) |
| `## Keeping the Dockerfile, Makefile, and dependencies in sync` | 4,185 | TRIM | CLAUDE.md keeps ~4 lines (deps live in `requirements.txt` + Dockerfile distro pkgs + Makefile ARGs — check all three when you touch one); the JupyterLab-default mechanics, texExpToPng SHA-pin details, and throwaway-container test recipe → `tasks/reference/book-and-docs-pipeline.md` / `notable-subsystems.md` |
| `## Code-the-Classics ports` | 7,182 | MOVE | `tasks/reference/code-the-classics-tightening.md`, `tests-and-gates.md`, `point-type-decision.md`, `notable-subsystems.md`, `gacalc-transforms-in-the-renderer.md` (ALL exist and cover this). Keep ~5 lines: what CtC is, "read `code-the-classics-tightening.md` before editing any game", the gate scripts by name, and the frozen-vector `+=` grep gotcha. The fidelity-gotchas list + gacalc-cost measurements → confirm in `notable-subsystems.md`, then cut |
| `## Assignments` | 2,042 | TRIM | CLAUDE.md keeps ~3 lines (assignments are format-covered; three carry deliberate holes — leave them; `tools/verify_render.sh` to check render). The review history + "where solutions live is undecided" → a reference doc (fold into `architecture-overview.md` or a short `tasks/reference/assignments.md`) |
| `## The book includes code by MARKER…` | 5,671 | MOVE | `tasks/reference/book-and-docs-pipeline.md` §3 (exists). Keep the core rule (~4 lines: book includes by `doc-region` marker with `:lineno-match:`, so editing source never breaks line numbers — check "is this text inside a published region?", not "did line numbers move?"). The gacalc-sdist docs-only pipeline, region-split mechanics, and "how to bump the shown version" → reference doc |
| `## Coding standard (Python)` | 10,073 | MOVE | Biggest single item. (a) ruff-enforced list and (b) generic judgment calls duplicate `tasks/apply-python-coding-standard.md` and geometricalgebra → propose `tasks/reference/python-coding-standard.md` (or point at the existing task doc). Keep in CLAUDE.md: ~6 lines — "green `make format` = the mechanical tier is done; `line-length=80` because the book is a PDF; judgment calls in <ref>." The (c) mvp-specific GL gotchas (import order, GL constants not int, `-1` sentinel, row-major + `GL_TRUE`, CCW winding, VAO-always-bound, shader dir) → `tasks/reference/gl-and-imgui-gotchas.md` (exists); keep a 1-line pointer |
| `## Tasks` | 7,221 | MOVE/TRIM | Duplicates `tasks/` (which the section itself calls authoritative) and carries a "Cross-repo (done)" gacalc-bump changelog that is pure history. Convention: CLAUDE.md is not a task log. Keep ~3 lines (active work in `tasks/`, one file per task; `tasks/reference/` for durable knowledge; archive under `tasks/archive/`). The gacalc-bump history → `tasks/reference/design-decisions.md` (much already there) |

## Projected result
- **Trimmed CLAUDE.md ≈ 13–15 KB (~3.3–3.8K tok)**, down from 46,827 B — roughly a 70%
  cut, saving ~8K tokens per turn.
- **Reference docs:** almost all MOVE targets already exist — the execution is mostly
  verifying the detail is captured there and then cutting the duplicate from `CLAUDE.md`.
  Likely new/updated docs: a `tasks/reference/python-coding-standard.md` (or fold into the
  existing `apply-python-coding-standard.md`); small additions to `architecture-overview.md`
  (assignments + Cayley/arc detail) and `design-decisions.md` (gacalc-bump history), if not
  already present.
- Every trimmed section leaves a **one-line pointer** to its reference doc, so nothing
  becomes undiscoverable.

## Open questions (for the maintainer)
1. Coding-standard detail — should the judgment-calls / ruff-tier detail move into a **new
   `tasks/reference/python-coding-standard.md`**, or just point `CLAUDE.md` at the existing
   `tasks/apply-python-coding-standard.md` (31 KB) that already holds it? Recommendation:
   new short reference doc, since that task doc will archive on completion whereas a
   reference doc is permanent.
2. Target leanness — is **~13–15 KB** the right target, or do you want it more aggressive
   (~10 KB, moving the "How to apply" and mvp-specific GL bullets out too)? Recommendation:
   ~13–15 KB — keep genuinely operational "while working" guardrails inline.

## Related
- runCrushInContainer `tasks/reference/crush-context-assembly.md` — measurement + method
  (how the per-turn token cost of a CLAUDE.md is computed).
- Cross-project `CLAUDE.md` — "Reference documents" and "keep CLAUDE.md lean" conventions.
