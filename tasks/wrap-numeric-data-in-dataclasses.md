# Wrap long numeric-data lists in dataclasses for readability

**Status:** proposed — needs go-ahead
**Priority:** 7
**Difficulty:** 6
**Started:** 2026-11-03 (William Emerison Six <billsix@gmail.com>)

## BLUF

Sweep the Python in this repo (`src/`, `ports/`, everything) for **long lists of bare numeric
data** — xyz coordinates, rgb colours, per-vertex attributes, tables of magic numbers — that would
read better as a **wrapper dataclass** (shared where a pattern repeats, single-use where it
doesn't), and convert them. The sole goal is **readability**: where wrapping a given blob of
numbers does not make it clearer, **leave it as is**. "Done" = the obvious wins are converted,
gates + renders still pass, and the skipped cases are noted with why.

## Context (read first)

- The codebase is full of flat numeric data: GL mesh builders emit flat
  `np.array([x, y, z, x, y, z, …], dtype=np.float32)` vertex buffers, colours are
  `tuple[float, float, float]` (e.g. the graphers' `Color` alias), demos carry tables of
  coordinates/material constants, etc.
- **gacalc already provides `Vector`** (the graded vector type) and mvp has `mathutils` around it —
  for genuine math vectors prefer those over a new dataclass; this task is about *readability
  wrappers for data*, not re-deriving the math layer.
- Related style already in the tree: `@dataclasses.dataclass(frozen=True)` value objects
  (e.g. `PlottedFunction`, `Surface` in the graphers). This task extends that habit to numeric
  blobs where it helps.

## Important caveats (where NOT to wrap)

- **GL vertex buffers are intentionally flat.** A flat `float32` array handed to `glBufferData` must
  stay flat for upload. Wrap the **authoring** side if it helps (build a list of `Point3`/`Vertex`
  dataclasses, then flatten once to the buffer), never the buffer the GL call consumes — and only
  when the authoring side is actually more readable wrapped.
- **Don't duplicate gacalc.** A 3-vector of real coordinates is a `gacalc.Vector`, not a new
  `Point3`, where the math layer is in play.
- **`ports/` mirrors upstream.** The faithful SuperBible / Code-the-Classics ports are kept close to
  their upstream structure on purpose (`tasks/reference/superbible-ports-guide.md`); restyling their
  data tables diverges them from the source they're checked against. See open question 1 before
  touching `ports/`.
- **The maintainer's guardrail:** if wrapping a given list does not improve readability, keep it as
  is — opt out freely and note it.

## Plan (draft)

- [ ] **Discover** candidates with ripgrep, not a tree-walk: large array/list literals, repeated
      `(r, g, b)` / `(x, y, z)` tuples, long `np.array([...])` authored by hand, magic-number
      tables. Log hits to `tasks/adhoc/wrap-numeric-data/data/` with a saved `discover.sh`.
- [ ] **Categorize** each: (a) clear win → wrap; (b) GL buffer / gacalc-owned / upstream-mirror →
      skip; (c) borderline → judgment, note the call.
- [ ] **Extract shared structures only where a pattern genuinely repeats** (e.g. a single `Rgb` or
      `Vertex` value object used by several builders); otherwise a **single-use** dataclass local to
      the file is fine — both are acceptable per the request.
- [ ] Convert the (a) cases; leave (b)/(c) with a one-line reason where non-obvious.
- [ ] **Verify** per touched area: the containerized gate (ruff/ty/annotations), `pytest`, and
      `tools/verify_render.sh` for any GL file whose authoring changed (prove the mesh is identical).
- [ ] Report the bulk done vs the deliberate skips (the part worth reviewing).

## Open questions

1. **Include `ports/`?** They deliberately mirror upstream, so restyling their data tables diverges
   them from the checked-against source. Recommendation: **limit to `src/` (and demos)**; touch a
   port only if a data blob is mvp-original (not from upstream) — confirm, or say to include ports
   wholesale.
2. **Shared common structures vs single-use?** The request allows both. Recommendation: introduce a
   shared value object (e.g. `Rgb`, `Vertex`) only at the 2–3-real-consumer bar; single-use
   dataclasses otherwise — avoids a premature "types" module.
3. **Colour specifically:** promote the graphers' `Color = tuple[float, float, float]` alias to a
   small `Rgb` dataclass (with named `r`/`g`/`b`), or leave the tuple alias (it already reads
   fine)? Recommendation: leave tuples unless a site reads unclearly.
