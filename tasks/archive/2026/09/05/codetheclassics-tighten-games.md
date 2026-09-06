# Tighten every Code-the-Classics game: dataclasses + `__post_init__`, tighter functions, drop the pygame-zero comments

**Status:** DONE + ARCHIVED 2026-09-05 — all ten games (eleven files) tightened in one session, each
behind the byte-identical frame gate and a 1500-frame input trace, ruff + ty clean, 104 tests; the
maintainer play-tested them the same day ("seem good to go") and committed. The standard the pass set
is `tasks/reference/code-the-classics-tightening.md` — read that before touching any game. The story of
the pass, in order, is under "How it went"; the numbers under "Outcome".
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

**This was an umbrella.** Fable turned it into ten per-game step-tasks (archived beside this file) and
did the work; this doc holds the vision, the guardrails, the method as it was actually run, and the
record.

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
- **The behaviour-preservation gate used per game.** The seeded frame capture that proved steps 1–2
  byte-identical (now `tools/ctc_capture_frame.py`, driven by `tools/ctc_verify_game.sh`): capture
  frame 180 of the committed file (`git show HEAD:`) twice as a determinism check and once of the
  working tree, and assert pixel identity — the "derive the before mechanically, then diff"
  discipline. The pilot showed that covers only the no-input attract mode, so a second gate was
  built the same day: `tools/ctc_state_trace.py` + `tools/ctc_compare_traces.py`, a seeded
  1500-frame scripted-input trace of the whole game-object graph, compared structurally. Then
  `make test` + `make format` (ruff check+format + `ty check` on vol1/vol2) green.
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
  - **Boundary, as first drawn:** the GL-resource classes (`Renderer`, `Image`) belonged to a separate
    investigation (`tasks/archive/2026/09/05/pgzero-gl-dataclasses-investigation.md`) the maintainer
    wanted to discuss first. He decided it mid-pass (2026-09-05: a dataclass of state built by a
    factory), so it was folded in after all — see "How it went".
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

## Method (as it was run)

1. **Analysis first, read-only.** Three parallel readers went through all ten games with `file:line`
   anchors; the census found the inlined engine halves byte-identical within three families
   (vol1-minimal, vol1-rich, vol2), which set the method: tighten each family's engine once, splice it
   into the siblings by script, and hand-tighten only the game halves.
2. **Ten step-tasks scaffolded** (`codetheclassics-tighten-<game>.md`, archived beside this file), each
   with its own analysis, plan and done-state; this umbrella kept the index. Order: easy-first within
   each family, each family's first game carrying the engine work.
3. **Pilot on boing**, the maintainer's read on the depth ("looks great"), then the fan-out, one game at
   a time, every game behind the same gates before the next started. The maintainer committed between
   games.
4. **Per-game records** in each step-task: what was tightened, which classes became dataclasses and
   which were left (with the reason), and the gate results — the judgment calls being the part worth
   reviewing.

## Done-state (every line of it met on 2026-09-05)

- Every game: gameplay **byte-identical** (frame-capture proof, not assumed), `make test` + `make
  format` (ruff + `ty` on vol1/vol2) green.
- Data-shaped classes are `@dataclass`(+`__post_init__`) where it genuinely helps; the exceptions are
  named with reasons.
- Functions are tighter (boilerplate gone, expressions/`match`/precise types), game logic still legible.
- The misleading pygame-zero comments are gone (identifiers untouched); pygame's real influence still
  acknowledged where true.
- Per-game step-tasks archived on their own completion; the umbrella archived when the last game landed,
  after harvesting the durable "how we tightened the CtC games" rationale into the reference doc.

## Per-game status (the umbrella was the index)

| game | vol | step-task | outcome |
|---|---|---|---|
| boing (+ boing_gl1) | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-boing.md` | the pilot; maintainer sign-off; AE=0 ×3, 1500-frame trace identical ×3 |
| cavern | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-cavern.md` | first splice of the vol1-minimal engine; settled the Actor hierarchy rules (§1a) |
| myriapod | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-myriapod.md` | reused cavern's engine; `Rock`/`FlyingEnemy` left plain (RNG in the constructor) |
| bunner | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-bunner.md` | the vol1-rich engine (code-indexed keys, Pillow text, looping sounds); found the `screen.draw.text(text, pos)` shim bug |
| soccer | 1 | `tasks/archive/2026/09/05/codetheclassics-tighten-soccer.md` | vol1-rich; `float(...)` at the gacalc `Expr` boundaries |
| kinetix | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-kinetix.md` | first vol2 engine (`surface`, `joystick`, `clip`); the `Collision` dataclass; the structural trace comparator |
| avenger | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-avenger.md` | flags `sound`/`mask`/`lines`; `_MixerSound` dropped for per-play `volume=` |
| eggzy | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-eggzy.md` | flags `collide` (`IntRect`)/`fill`/`rect`/`region`; two levels and a second game traced |
| leadingedge | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-leadingedge.md` | flags `polygon`/`scale`/`text`; `TrackPieceScreen`; the title fade fixed (flagged) |
| beatstreets | 2 | `tasks/archive/2026/09/05/codetheclassics-tighten-beatstreets.md` | last and largest; scooter channel path deleted; `Fighter` a kw_only dataclass; the post-intro fade fixed (flagged) |

## How it went (2026-09-05, one session; the after-story in "Afterwards")

1. **Scoping (morning).** The maintainer set the goal and the constraint: keep the spirit of the course
   (library, not framework; repetition across demos is fine for learning), remove the pygame-zero
   comments, use dataclasses as far as reasonable, behaviour-faithful. Two existing tasks were folded in
   (comments, types) and the licensing task's decided BSD-2-Clause header was folded in too.
2. **The boing pilot** established the shape: plain `# ===== engine: … =====` banners; only the engine
   the game uses; window and renderer created at module level, demo-style, with no `require_renderer()`
   guard (the maintainer: "is there any reason it would need to be checked every time?"); dataclasses
   with every attribute declared; f-strings and `images.load(...)`. Its first input trace never made a
   bat hit the ball, which is why the trace harness gained a real key script.
3. **Five maintainer directives during the pilot's review, each applied to every later game:**
   extract the Protocols hiding in the code, copied per file and never outside it — and, tested with
   ty, never declared by subclassing (a subclass inherits the stub and a deleted method goes
   unreported); every `match` ends in `case _: raise`, with deliberate no-op arms written out; field
   descriptions as Sphinx `#:` doc-comments (researched: `field(metadata=)` is machine data, PEP 727 was
   withdrawn); an `if __name__ != "__main__": sys.exit(...)` guard before the first resource is
   acquired (and a task filed for the course demos, which have none); and — the boundary redrawn — the
   GL-resource classes become dataclasses of state built by factory functions, with related variables
   grouped (`Uniforms`, `GLBuffer`).
4. **vol1** (cavern, myriapod, bunner, soccer) followed, engines spliced from boing's by
   `splice_vol1_engine.py`. cavern settled the Actor hierarchy rules; bunner answered the maintainer's
   "can Actor and its subclasses be dataclasses?" (leaf field-bags yes; constructors that compute the
   base's inputs stay plain slotted classes) and found the debug-label shim bug. The factory decision
   was then applied to all six vol1 files by the `renderer_dataclasses.py` codemod.
5. **vol2** (kinetix, avenger, eggzy, leadingedge, beatstreets) followed, engines from
   `splice_vol2_engine.py`, which grew one flag set per game as each needed more of the engine; the
   `sed` trace normalisations were replaced by the structural comparator. Two shim fade bugs and the
   dead smoke test were found on the way and flagged rather than hidden.
6. **Archive (evening).** The umbrella archived when beatstreets landed: the three harnesses promoted to
   `tools/ctc_*`, the durable how-and-why harvested into the reference doc, the two subsumed tasks and
   the licensing task archived as done, follow-ups filed. The maintainer play-tested all ten games and
   committed.

## Afterwards (2026-09-06)

The smoke test was deleted (`tasks/archive/2026/09/06/remove-ctc-smoketest.md`); the factories became
classmethods on their classes (`Renderer.create`, `Image.load`, …; `ctc-factory-classmethods.md`);
the `PointLike` boundary type was kept after measurement (`tasks/reference/point-type-decision.md`);
the renderers' model and ortho matrices were redefined with gacalc transforms, compiled once at import
(`renderer-model-matrix-from-gacalc.md`, `tasks/reference/gacalc-transforms-in-the-renderer.md`),
with the library-side version filed in geometricalgebra; the one-shot codemods were `git rm`'d at the
maintainer's word and `tasks/adhoc/` got its `.keep`. Step 3 of the inline initiative (re-extract the
shared library) stayed parked at the maintainer's request.

## Outcome

| game | lines before (2026-09-05, pre-tightening HEAD) | after (2026-09-06 tree) | change | pygame/pgzero mentions left |
|---|---|---|---|---|
| boing | 1854 | 1431 | −23% | 2 |
| boing_gl1 | 1724 | 1224 | −29% | 2 |
| cavern | 2971 | 2078 | −30% | 2 |
| myriapod | 3081 | 2188 | −29% | 2 |
| bunner | 3583 | 2316 | −35% | 2 |
| soccer | 3886 | 2688 | −31% | 2 |
| kinetix | 4124 | 2721 | −34% | 2 |
| avenger | 4456 | 3057 | −31% | 2 |
| eggzy | 4727 | 3394 | −28% | 4 |
| leadingedge | 5151 | 3851 | −25% | 2 |
| beatstreets | 6022 | 4817 | −20% | 3 |
| **all eleven files** | **41579** | **29765** | **−28%** | the `PGZERO_MAX_FRAMES` env var; the int-Rect rationale in eggzy and beatstreets |

**Three deliberate visible deviations, all fixes to the inlined shim, none to game logic (play-tested
by the maintainer 2026-09-05):** leadingedge's title fade (HEAD showed solid black for a second);
beatstreets' post-intro fade (HEAD cut hard, and a second game's intro drew over the level); bunner's
debug labels now draw (`screen.draw.text(text, pos)` used to swallow `pos`). Every other pixel and
every traced state was identical. What the harnesses never cover — audio and the gamepad — the
maintainer's play-test did.

## Decisions settled during the pass (for the record; the reference doc carries the rationale)

- **Pilot-first, then the same bar for the other nine** — yes (maintainer).
- **Fold in the comments and types tasks** — yes; both archived as subsumed when the last game landed.
- **Dataclass shape** — `@dataclass(slots=True)` as the default; `kw_only=True` where the call sites
  read better (beatstreets' `Fighter`); `frozen=True` only for the genuinely immutable
  (`TrackPieceScreen`, the matrix templates). Left plain, with the reason in each record: constructors
  that consume RNG or compute the base's inputs.
- **Sphinx `#:` field doc-comments** — "absolutely" (maintainer, 2026-09-05).
- **Protocols structural, never subclassed; `match` always closed with `case _: raise`; module-level
  window and renderer; the import guard; GL-resource dataclasses built by factories** — all the
  maintainer's, as listed under "How it went".
