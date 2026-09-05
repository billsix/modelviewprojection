# Tighten every Code-the-Classics game: dataclasses + `__post_init__`, tighter functions, drop the pygame-zero comments

**Status:** DONE + ARCHIVED 2026-09-05 — all ten games (eleven files) tightened, each behind the
byte-identical frame gate and a 1500-frame input trace, ruff + ty clean, 104 tests; staged (the
maintainer commits). See "Completion record" at the end. The standard is
`tasks/reference/code-the-classics-tightening.md` — read that before touching any game.
**Priority:** 1
**Difficulty:** 7

## BLUF

Make each of the 10 Code-the-Classics games (`ports/codetheclassics/vol1|vol2/`) as **tight and
modern as the fidelity rule allows**: convert hand-rolled `__init__`s + data-shaped classes to
`@dataclass` with **`__post_init__`** for derived setup/validation wherever it genuinely helps,
tighten functions (kill boilerplate, prefer expressions/`match`, precise types), and **strip the now-
misleading "this IS pygame / PyGame Zero" comments**. The one inviolable constraint: these are
**behavior-faithful ports — NO behavior change** (same RNG call order, same update/draw order, same
gameplay). *Structure* may be modernized freely; *behavior* may not. **"Done" = every game plays
byte-identically (frame-capture proof), ruff + ty green, and reads tighter.**

**This is an umbrella.** Fable owns turning it into per-game step-tasks and doing the work; this doc
holds the vision, the guardrails, the method, and the pointers a cold reader needs.

## Context — read first (cold-start; assume none of the discussion is in memory)

- **What Code-the-Classics is here.** 10 faithful game ports (BSD-2-Clause, © Eben Upton et al.) under
  `ports/codetheclassics/vol1/{boing,bunner,cavern,myriapod,soccer}` and
  `vol2/{avenger,beatstreets,eggzy,kinetix,leadingedge}`, each a single self-contained file. They used
  to run on a shared `pgzero_gl` shim; that shim has now been **inlined into each game** (steps 1–2 of
  `tasks/pgzero-gl-inline-strip-reextract.md` — DONE and play-tested 2026-09-05), so each game owns its
  own ~3–6k-line copy. This task tightens those inlined copies.
- **THE guardrail — the fidelity rule (mvp `CLAUDE.md` › "Code-the-Classics ports").** The games are
  **behaviour-faithful**: *no behaviour changes* — same RNG call order, same update/draw order, same
  gameplay. Since 2026-07-08 their *structure* MAY be modernized (dataclasses, `match`, annotations,
  `@override`, precise callable types) and they ARE ruff-formatted. So aggressive *structural*
  tightening is not just allowed, it's the point — but a change that alters a single RNG draw, reorders
  updates, or shifts a sprite by a pixel is a **regression**, not a refactor.
- **The behaviour-preservation gate you MUST use per game.** `tasks/adhoc/pgzero-gl-inline/capture_frame.py`
  is the seeded frame-capture harness (the same one that proved steps 1–2 byte-identical). For each
  game: capture a reference frame trace (e.g. frame 180) on the **pre-change** file, make the changes,
  re-capture, and assert **byte-identical**. This is the "derive the before mechanically, then diff"
  discipline — an empty diff IS the proof nothing changed. (Reconstruct the "before" via `git stash` /
  `git show`, never a hand-copied baseline.) Then `make test` + `make format` (ruff check+format + `ty
  check` on vol1/vol2) green.
- **Coding standard (mvp `CLAUDE.md` › "Coding standard (Python)").** `line-length = 80` (the book is a
  PDF); ruff enforces layout/naming/imports/etc.; **prefer `match` + `case _`** for exhaustive dispatch;
  **annotate generously**; **`dataclass(slots=True, kw_only=True)`** is the house default where it fits;
  modern Python (3.14). "New code vs existing code" normally says don't rewrite working code to chase
  shapes — **this task is the deliberate, maintainer-approved exception** (a modernization sweep, like
  the one-time 2026-07-18 pass), so restructuring existing game code is in-scope here.
- **This FOLDS IN two existing tasks (maintainer confirmed 2026-09-05) — subsumed, not duplicated:**
  - `tasks/remove-pygame-comments-from-ctc.md` (P4/D5) — strip the misleading pygame/PyGame-Zero
    **comments & docstrings** (~987 mentions; **comments only, NEVER identifiers**; pygame's influence
    stays acknowledged where true — only the "this IS pygame" framing goes). Do this **as part of each
    game's pass** here; use its detail as the per-game comment-concern checklist, and archive it as
    subsumed once every game's comments are done.
  - `tasks/code-the-classics-round3-types.md` (blocked, P7) — "add more types." Tighter/precise typing
    is part of "as tight as possible," so absorb its intent per-game (its own open questions —
    which games / annotations-vs-new-types — get answered by Fable's per-game analysis).
  - **Boundary:** `tasks/archive/2026/09/05/pgzero-gl-dataclasses-investigation.md` is about the **shim renderer** classes
    (`renderer.py`/`renderer_gl1.py` — textures, GL-resource wrappers), a *separate* investigation the
    maintainer wants to discuss first. The inlined copy of that renderer lives inside each game now, so
    Fable will encounter it — **do not restructure the renderer/GL-resource classes under this task**;
    flag them for that investigation instead, and keep this task to the games' own gameplay classes and
    functions.
- **Do not touch** the vendored `entrypoint/dotfiles/.emacs.d/elpa/` tree, and remember the games are
  play-tested working now — a display is required to *fully* verify, which only the maintainer can do;
  the frame-capture gate is the automatable proxy.

## The three concerns, per game

1. **Dataclasses + `__post_init__`.** Convert data-shaped classes with hand-rolled `__init__`s to
   `@dataclass`; move derived/validated setup into `__post_init__`. **Default shape (settled — see
   Open questions Q3):** `@dataclass(slots=True)`; add `kw_only=True` only where call sites read better;
   `frozen=True` only for genuinely-immutable classes. Fable may refine per-class during analysis.
   **Watch the traps:** mutable defaults → `field(default_factory=…)`; a class that
   is NOT plain data (real behaviour in `__init__`, ordering-sensitive setup) may be wrong to convert —
   leave it and say why. gacalc vectors are **frozen**, so any "change a coordinate" is a rebind, not a
   mutation (already true in these games; keep it).
2. **Tighter functions.** Remove boilerplate; prefer expressions, comprehensions, `sum`/`math.prod`,
   `match` + `case _`; inline single-use locals; precise type annotations. **But keep the game logic
   legible** — tightness must not obscure what the port does, and it must not change behaviour.
3. **Strip the pygame-zero comments** (per `remove-pygame-comments-from-ctc.md`): comments/docstrings
   only, never identifiers; keep honest acknowledgements of pygame's influence, drop the misleading
   "this reimplements pygame" framing.

## Method (how Fable should run this)

1. **Analyze first (read-only).** Read this doc, the mvp `CLAUDE.md` Code-the-Classics section, the
   fidelity rule, `capture_frame.py`, and the two folded-in tasks. Skim each game to gauge its shape
   (which classes are data-vs-behaviour, where the boilerplate is, comment density).
2. **Scaffold per-game step-tasks.** Create `tasks/codetheclassics-tighten-<game>.md` per game (10 of
   them), each a normal cold-readable step-task: `Part of:` this umbrella, its own before/after plan and
   done-state. Keep a one-line-per-game status checklist **in this umbrella** (it's the index). Order
   them easy-first — **pilot with `boing`** (smallest/simplest) to establish the pattern and depth, get
   the maintainer's read on it, THEN fan out to the rest.
3. **Execute one game at a time, gated.** For each game: capture the reference frame trace → make the
   three-concern changes → re-capture → assert byte-identical → `make test` + `make format` green →
   stage. One game per commit boundary (the maintainer commits). Never batch multiple games into one
   unverified change.
4. **Report per game:** what was tightened, which classes became dataclasses (and which were left, with
   the reason), and the byte-identical proof. The judgment calls (a class that looked like data but
   wasn't; a function left long because tightening hurt legibility) are the review-worthy part.

## Verification / done-state

- Every game: gameplay **byte-identical** (frame-capture proof, not assumed), `make test` + `make
  format` (ruff + `ty` on vol1/vol2) green.
- Data-shaped classes are `@dataclass`(+`__post_init__`) where it genuinely helps; the exceptions are
  named with reasons.
- Functions are tighter (boilerplate gone, expressions/`match`/precise types), game logic still legible.
- The misleading pygame-zero comments are gone (identifiers untouched); pygame's real influence still
  acknowledged where true.
- Per-game step-tasks archived on their own completion; this umbrella archives when the last game lands
  (harvest any durable "how we tightened the CtC games" rationale into a `tasks/reference/` note first).

## Per-game status (the umbrella is the index)

| game | vol | step-task | status |
|---|---|---|---|
| boing (+ boing_gl1) | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-boing.md` | **DONE + ARCHIVED** 2026-09-05 — maintainer sign-off; AE=0 ×3, 1500-frame input trace identical ×3, ruff+ty clean; `#:` field docs applied |
| cavern | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-cavern.md` | scaffolded (P2/D4) — first after the pilot; its engine half splices into myriapod |
| myriapod | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-myriapod.md` | READY — next; engine from `splice_vol1_engine.py myriapod …` |
| bunner | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-bunner.md` | READY — next (vol1-rich family; its engine splices into soccer) |
| soccer | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-soccer.md` | READY — next (vol1-rich; engine from the splice + bunner's additions as needed) |
| kinetix | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-kinetix.md` | READY — next; first vol2 game, its engine half splices into the other four |
| avenger | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-avenger.md` | **DONE + ARCHIVED** 2026-09-05 — AE=0, 1500-frame trace identical; vol2 flags `sound`/`mask`/`lines` added to the splice; `_MixerSound` gone (per-play `volume=`) |
| eggzy | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-eggzy.md` | **DONE + ARCHIVED** 2026-09-05 — AE=0, 1500-frame trace identical (two levels + a second game); vol2 flags `collide`/`fill`/`rect`/`region` added (`IntRect`, tileset region draws) |
| leadingedge | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-leadingedge.md` | **DONE + ARCHIVED** 2026-09-05 — AE=0, 1500-frame trace identical; vol2 flags `polygon`/`scale`/`text` added; **the title fade now fades (HEAD's shim showed solid black) — flagged** |
| beatstreets | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-beatstreets.md` | **DONE + ARCHIVED** 2026-09-05 — AE=0, 1500-frame trace identical; scooter channel path deleted, `Fighter` a kw_only dataclass; **the post-intro fade now fades — flagged** |

Order = easy-first within each engine family, and each family's first game carries the engine
work the siblings splice (`tasks/reference/code-the-classics-tightening.md` §3).

**Follow-up found on avenger (2026-09-05), not in this task's scope:** `ports/codetheclassics/_smoketest.py`
(and the README lines that point at it) imports a game as a module and drives `update()`/`draw()`;
no game has allowed that since the inlining pass made each game own its loop, and the import guard
now exits on import. It is dead, superseded by `tasks/adhoc/codetheclassics-tighten-games/verify_game.sh`
(which runs the game as `__main__` under Xvfb). Decide at umbrella-archive time: delete it and fix the
README, or rewrite it as a subprocess runner (recommend delete — `verify_game.sh` is the tool now).

## Decisions and direction changes logged during the pilot (2026-09-05)

Recorded here so a cold reader sees *why* the pilot looks the way it does; the full rationale is
in the reference doc.

- **Maintainer: the games are library code like the demos** — window and renderer created at
  module level, no `require_renderer()` guard, no `__main__` guard, loop at the bottom ("is there
  any reason it would need to be checked every time?" — no). Applied to boing; the standard.
- **Maintainer: extract the Protocols that are hiding in the code, copied per file, never
  outside it.** boing gained `Sprite` and `SpriteRenderer`. **Tested with ty: declaring
  conformance by subclassing the Protocol makes ty miss a deleted method (the stub is
  inherited), so Protocols stay structural** — the docstrings say so.
- **Maintainer: every `match` ends in `case _: raise`**, with deliberate no-op arms written out.
- **Maintainer asked for a standard way to attach field descriptions instead of comments** —
  researched: `field(metadata=)` is for machine data, PEP 727 `Doc()` was withdrawn; the tooling-
  read standard is Sphinx's `#:` doc-comment. Recommendation recorded (reference doc §1.9), not
  yet applied — see the open question below.
- **Fable (with the maintainer's "change direction / make it better" grant):** fold the decided
  BSD-2-Clause header into each game's pass (the licensing task's plan; vol 2 © year is **2024**
  per `LICENSE`, not 2020); replace the `# ===== pgzero_gl/<mod>.py =====` banners now instead
  of at step 3; strip the audio mixer to what each game uses (boing: no fades/loops); dissolve
  boing's `Context` into `ASSET_ROOT` + the module `renderer`; `images.load()` over the
  `getattr`/attribute idiom (which also makes `_Loader` slots-safe and generic).
- **Analysis finding: the inlined engines are byte-identical within three families** → tighten
  each family's engine once and splice; input to step 3 of `tasks/pgzero-gl-inline-strip-reextract.md`.
- **Maintainer (2026-09-05): GL-resource classes are dataclasses of STATE built by FACTORY
  functions**, with related instance variables grouped into named dataclasses (`Uniforms`,
  `GLBuffer`; `make_renderer`, `load_image`). Implemented across all six tightened games by the
  `renderer_dataclasses.py` codemod; this also closed `tasks/pgzero-gl-dataclasses-investigation.md`
  (archived). The same "factory computes, dataclass holds" shape is the answer for constructors
  that compute their base's inputs (bunner's rows) — a candidate follow-up, not done.
- **Harnesses:** `tasks/adhoc/codetheclassics-tighten-games/verify_game.sh` (frame identity vs a
  git ref, or A/B) and `state_trace.py` (seeded, scripted-input, whole-object-graph diff) — the
  frame gate alone only covers the attract mode.

## Open questions — all SETTLED by the maintainer 2026-09-05

4. ~~**Adopt Sphinx `#:` doc-comments for dataclass field descriptions**~~ → **SETTLED (maintainer,
   2026-09-05: "absolutely")** — applied to boing/boing_gl1 the same day; every later game applies it.

### The original three

1. **Pilot-first** — YES. Do `boing` first, get the maintainer's read on the tightening *depth*, then
   apply that same bar to the other 9. (Fixes the standard once instead of re-litigating per game.)
2. **Fold-in** — YES, fold in. `remove-pygame-comments-from-ctc.md` and
   `code-the-classics-round3-types.md` are **subsumed** into this per-game work: one pass per game
   touches all three concerns, and each standalone task is archived as subsumed when the games its
   concern covers are all done (see the "folds in" bullets in Context, updated to reflect this).
3. **Dataclass shape** — maintainer deferred to discretion (mine, or Fable's next-session judgment).
   **Default set:** `@dataclass(slots=True)`; add `kw_only=True` **only** where a class's call sites
   read better keyword-only (some game constructors are positional by long habit — don't force those).
   `frozen=True` only where a class is genuinely immutable and nothing mutates it. **Fable may refine
   this per-class during analysis** — this is the starting default, not a mandate; the behavior gate is
   what actually constrains the change.

## Completion record (2026-09-05, Fable)

All ten games tightened in one session, in the umbrella's order, each behind the same gates:
frame 180 pixel-identical to HEAD (`AE=0`), a seeded 1500-frame scripted-input trace structurally
identical to HEAD's, ruff + ty clean on `ports/codetheclassics/vol1|vol2`, 104 tests. Per-game
records are in the archived step-tasks (this directory); the durable "how" is in
`tasks/reference/code-the-classics-tightening.md` (§6 has the outcome table and the deviations).

| game | lines before | after | change | pygame/pgzero mentions left |
|---|---|---|---|---|
| boing | 1854 | 1367 | −26% | 2 |
| boing_gl1 | 1724 | 1222 | −29% | 2 |
| cavern | 2971 | 2010 | −32% | 2 |
| myriapod | 3081 | 2119 | −31% | 2 |
| bunner | 3583 | 2248 | −37% | 2 |
| soccer | 3886 | 2620 | −33% | 2 |
| kinetix | 4124 | 2653 | −36% | 2 |
| avenger | 4456 | 2989 | −33% | 2 |
| eggzy | 4727 | 3326 | −30% | 4 |
| leadingedge | 5151 | 3784 | −27% | 2 |
| beatstreets | 6022 | 4749 | −21% | 3 |
| **all eleven files** | **41579** | **29087** | **−30%** | (the `PGZERO_MAX_FRAMES` env var, plus the int-Rect rationale in eggzy/beatstreets) |

**Maintainer play-tested all ten briefly, 2026-09-05: "seem good to go."** Three deliberate visible
deviations, all fixes to the inlined shim, none to game logic: leadingedge's title fade (HEAD showed solid black for a second);
beatstreets' post-intro fade (HEAD cut hard, and a second game's intro drew over the level);
bunner's debug labels now draw (`screen.draw.text(text, pos)` used to swallow `pos`). Every
other pixel and every traced state is identical.

**Harnesses promoted to `tools/`** (reusable: `tasks/pgzero-gl-step3-reextract-library.md` needs the
same gates): `tools/ctc_verify_game.sh`, `tools/ctc_state_trace.py`, `tools/ctc_compare_traces.py`
— manual tools, documented in the reference doc §5, not gated (they need the sandbox's Xvfb and
the nested image). **One-shot codemods left in `tasks/adhoc/codetheclassics-tighten-games/`**
(`splice_vol1_engine.py`, `splice_vol2_engine.py`, `renderer_dataclasses.py`): the audit trail of
how every engine half was built — they are staged but not yet in any commit, so they are kept
until the maintainer's commit records them; `git rm` them after that.

**Follow-ups filed:** `tasks/remove-ctc-smoketest.md` (proposed: `_smoketest.py` is dead — it
imports a game as a module, which the import guard now refuses); `tasks/demos-exit-if-not-main.md`
(the same import guard for the course demos). **Folded-in tasks archived as done:**
`code-the-classics-round3-types.md`, `remove-pygame-comments-from-ctc.md` (subsumed), and
`codetheclassics-licensing-after-shim-inline.md` (every game carries the BSD-2-Clause dual-©
header; the shim source's own fate belongs to step 3). **Next:** step 3 —
`tasks/pgzero-gl-step3-reextract-library.md` — for which the per-family engine flag list in the
reference doc §3 is the map of what is genuinely shared.
