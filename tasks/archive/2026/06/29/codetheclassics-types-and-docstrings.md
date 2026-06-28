# Task: type-annotate the Code-the-Classics ports + document the pgzero_gl shim

**Status:** Phases 0–3 + 5 DONE — shim documented/typed; **all 10 game ports (Vol 1 + Vol 2) typed & `ty`-clean, including aggressive local-variable annotations**. `ty check` enforced over the whole `pgzero_gl` + `vol1` + `vol2` tree in `format.sh`. **Task effectively complete** (Phase 4 enforcement done; ruff-on-games and `_smoketest.py` intentionally out of scope — see Phase 4 status).
**Created:** 2026-06-28
**Area:** `ports/codetheclassics/`

## Shim fidelity fixes (surfaced by play-testing, 2026-06-28/29)

Bill played the ports on real hardware; each crash/symptom was a `pgzero_gl`
shim gap (the games are faithful BSD ports — fixes go in the shim, never the
game logic). All verified `ty`-clean + 10/10 games passing the headless harness
(`scratchpad/headless_play.py`, 600 frames each).

- **`Vector2`/`Vector3` `__mul__`**: pygame `vec * vec` is the **dot product**
  (scalar), not component-wise. Fixed both; was crashing soccer (`v0*v1 > 0.8`).
- **`scale_to_length`** added to both vector types (soccer/avenger).
- **`Sound`**: added `set_volume`/`get_volume`/`fadeout`, and `play()` now accepts
  `maxtime`/`fade_ms` (accepted-and-ignored, like pygame) — leadingedge crashed
  on `play(..., fade_ms=…)`.
- **Audio stream-leak / framerate drop**: `just_playback.Playback` opens a
  miniaudio stream and has **no finalizer**, so dropping one leaks it (froze
  bunner after rapid replays). `Sound`/`_Music` now keep a bounded **pool** of
  voices and `load_file` **once per voice** (replaying restarts without
  re-decoding). See `audio.py` (`_MAX_VOICES_PER_SOUND`, `_acquire`).
- **beatstreets `attacks.json`**: was opened relative to cwd → now script-relative.
- **`Rect` is now integer-coord like real `pygame.Rect`** (2026-06-29). It was
  float, which crashed beatstreets at `randint(boundary.top, boundary.bottom)`
  (`randint` needs ints). pgzero actually has **two** rects: `pygame.Rect` (int,
  what `game.boundary` etc. are) and `ZRect` (float). `geometry.Rect` now
  truncates coords toward zero (one `_coord` choke-point through `x/y/width/
  height` properties); added a `ZRect(Rect)` subclass that keeps float, and
  **`Actor._rect` is now a `ZRect`** so sprite movement at non-integer speeds
  keeps its sub-pixel precision (no per-frame drift). `ZRect` exported from the
  package + `pgzero.rect` stub.

> Non-issue ruled out: "lots of background music at once" was **leftover
> background `python <game>.py` processes** I'd launched, each playing audio —
> not a shim/game bug. Killed; nothing to fix.

## Progress log (Phase 3)

**2026-06-29 — Phase 3 complete: all 5 Vol 2 game ports annotated & `ty`-clean.**

- Files: `kinetix` (1228), `avenger` (1466), `eggzy` (1603), `leadingedge` (1684),
  `beatstreets` (2438) — done in parallel, each independently verified (`ty` +
  `py_compile`) and diff-audited afterward to confirm annotation-only (balanced
  insert/delete, no logic lines changed, only the two inserted bare-annotation
  globals add whitespace). Baseline was 222 diagnostics → **0**.
  `ty check .../vol2` added to `entrypoint/format.sh`.
- **Three validated high-leverage fixes** carried Vol 2 (much heavier than Vol 1's
  18 diagnostics because of these patterns):
  - **`game = None` module global** (created later via `global game; game = Game()`)
    → annotate **`game: Any = None`**. `ty` was inferring `game: None` and flagging
    every `game.<attr>`; `Any` (assume-non-null, matching the shim's dynamic Actor
    typing) clears the whole batch. `Optional[Game]` would only relocate the errors.
  - **`joystick_controls`** (assigned only inside a function via `global`, never
    bound at module top) → a **bare module-level annotation** `joystick_controls:
    Any` (no `=`). Verified this creates **no runtime binding** (PEP 526) — pure
    declaration, zero behaviour change — while giving `ty` the global it needs.
    Same trick used for `STAGES` in beatstreets.
  - **`from pygame[.math] import Vector2/Vector3/mixer/surface`** → scoped
    `# ty: ignore[unresolved-import]` (the shim's `pygame` is a synthetic
    `sys.modules` module, not statically resolvable).
- **17 suppressions/casts total across Vol 2, all with inline reasons**:
  `unresolved-import` ×6, `invalid-method-override` ×6 (Actor.draw scroll-offset
  widening; update return-flag narrowing; GravityActor.update `detect`),
  `invalid-return-type` ×2 (button_down falls through to implicit None),
  `cast(Any, …)` ×2 (eggzy XML `ElementTree.find()` returns `Optional[Element]`),
  `invalid-assignment`/`unresolved-attribute` ×1 each (flow-analysis can't narrow a
  known-non-None Actor attr / a loop var that is concretely a `CPUCar` subtype).
- Confirmed the Vol 1 nullable-unguarded-`Any` pattern recurs heavily in Vol 2 and
  is the right call there too.

## Phase 4 status (enforce + verify)
- **`ty` clean over the whole tree** (`pgzero_gl` + `vol1` + `vol2`) and enforced in
  `format.sh`. ✅
- **`ruff` is deliberately NOT run on the games** (only the shim is ours to format;
  the games stay byte-faithful to upstream). The original Phase 4 "ruff clean over
  the tree" item is intentionally scoped to the shim only.
- **`_smoketest.py` does not exist** (the original plan assumed it). Behaviour-
  unchanged was instead assured by: annotations-only edits (diff-audited), `ty`,
  `py_compile`, and import smoke tests. On-window run verification is Bill's.

## Phase 5 — local-variable annotations (DONE 2026-06-29)

**Completed 2026-06-29, aggressively per Bill's "aggressive within reason".** All
15 shim modules + all 10 game ports got local-variable annotations (done in
parallel, ~3 shim groups + 10 single-file game agents, each independently
verified). Whole tree still `ty`-clean and `py_compile` clean; **zero new
`# ty: ignore`/`cast`** (suppression counts identical to the Phase-3 baseline —
where a local would have needed a suppression, it was left to inference); diff
audited annotation-only (net 0 blank-line delta, no control-flow/call lines
touched). Working rule used for "within reason":
- **Annotated** essentially every first-binding local with a concrete type,
  including simple literals (`count: int = 0`, `done: bool = False`,
  `items: list[Foo] = []`), numpy locals (`NDArray[np.float32]`), GL handles
  (`int`), and `Vector2`/`Vector3`/Rect/game-class locals (forward refs quoted in
  the games, which lack `from __future__ import annotations`).
- **Left to inference** (deliberately): locals read off dynamic `Any` (`game.X`,
  Actor shim attrs, `getattr`, XML `.find()`), heterogeneous list-concats, and
  anything that would have forced a suppression.
- **Never annotated** (syntactically impossible): loop targets, tuple-unpacking,
  `with`/`except as`, augmented assignments, walrus, comprehension vars; and never
  re-annotated a later reassignment.

---

### Original Phase 5 plan (for reference)

Phases 1–3 deliberately **skipped trivial
local-variable annotations** ("signatures + class/global attributes; let `ty`
infer locals") to keep the faithful-port diffs small and reviewable. This phase
adds explicit type annotations to **local variables** too, across **both**:

1. **The `pgzero_gl` shim** (`ports/codetheclassics/pgzero_gl/*.py`, 15 modules) —
   our own code; annotate meaningful locals (the non-obvious ones — numpy
   intermediates, GL handles, accumulators, parsed structures), not throwaways
   like loop counters where the type is self-evident.
2. **All 10 game ports** (`vol1/*`, `vol2/*`) — still **annotations-only, zero
   behaviour change, no restructuring**; the games remain faithful BSD ports, so
   the diff must stay "added annotations" only.

### Scope / judgement
- Annotate locals where a type isn't immediately obvious from the RHS or where it
  aids readability/checking (e.g. `parts: list[str] = line.split(",")`,
  accumulators that start `[]`/`{}`/`0` and change type, results of `Any`-returning
  shim/FFI calls). **Skip** locals whose type is trivially obvious
  (`x = 0`, `name = "foo"`, `for i in range(n)`), to avoid noise — match the repo's
  light-touch style rather than annotating every binding.
- A few locals were *already* annotated in Phases 1–3 because `ty` required them
  (e.g. `all_objs: list[Any]`, `controls: list[Callable[[], int] | None]`,
  `times: dict[str, float]`, the eggzy XML `*_node: Any`); those stay.
- **`from __future__ import annotations`** is already in the shim modules; the game
  ports are not `from __future__`-annotated, so any *forward-referenced* local type
  must be quoted (or add the future import — but that's arguably a structural change
  to a faithful port, so prefer quoting).

### Constraints (unchanged)
- No behaviour change; annotations are erased at runtime. No call-site keyword-arg
  rewrites in the games. Keep `ty check` green and `py_compile` clean throughout;
  keep the games out of `ruff`'s scope.

### Verification
- [ ] `ty check` still green over `pgzero_gl` + `vol1` + `vol2`.
- [ ] Game diffs remain annotations-only (spot-audit like Phases 2–3).
- [ ] No new `# ty: ignore`/`cast` introduced just to satisfy a *local* annotation
      (if a local needs one, prefer leaving that local to inference).

### Open question
- How aggressive? Two readings of "add types to local variables": (a) annotate
  **every** local (maximally explicit, larger diff), or (b) annotate the
  **non-obvious** locals only (lighter, matches house style). Recommend (b) unless
  Bill wants exhaustive coverage — confirm before starting.

## Progress log (Phase 2)

**2026-06-29 — Phase 2 complete: all 5 Vol 1 game ports annotated & `ty`-clean.**

- Order done: `boing` → `cavern` → `bunner` → `myriapod` → `soccer` (boing by hand
  to set the convention; the other four in parallel, each verified afterward).
- `ty check /mvp/ports/codetheclassics/vol1` → **All checks passed!**; all five
  `py_compile` clean. Added `ty check .../vol1` to `entrypoint/format.sh` (still
  **no ruff** on the games — they stay byte-faithful to upstream).
- **Convention applied** (annotations only, zero behaviour change, no keyword-arg
  rewrites of calls): every `def` got param + return types; `__init__` attributes
  annotated on first assignment (tuple-unpacked ones left to inference); mutable
  module globals (`state`/`game`/counters/flags) annotated; trivial locals left to
  inference except where one was needed to satisfy `ty`.
- **8 suppressions/casts total, all justified faithful-port LSP variances** (each
  carries an inline reason):
  - `invalid-method-override` ×5 — `MyActor.draw(self, offset_x, offset_y)` in
    bunner & soccer (adds scroll offsets to the shim's `Actor.draw(self)`), and
    `Fruit/Player/Robot.update` in cavern (narrow `GravityActor.update`'s optional
    `detect`). Can't fix without editing the faithful games or the shim, so scoped
    `# ty: ignore[...]` is correct.
  - `unresolved-import` ×1 — `from pygame.math import Vector2` in soccer (`pygame`
    is the shim's synthetic `sys.modules` module; not statically resolvable).
  - `invalid-return-type` ×1 — `inverse_direction` in myriapod (exhaustive over 4
    directions; fall-through unreachable).
  - `cast` ×1 — `Game.player` in cavern (menu/attract `Game` has no player; every
    unguarded deref runs only when a real `Player` exists).
- Recurring pattern worth noting for Phase 3: nullable-but-unguarded Actor
  attributes (`game.player`, `game.bunner`, `Team.active_control_player`) are typed
  `Any` rather than `Optional[...]` — the games assume-non-null at deref sites, and
  `Optional` would just relocate the error. This matches the shim's own dynamic
  `Actor` typing.

## Progress log

**2026-06-28 — Phase 0 + 1 complete.** The whole `pgzero_gl` shim is annotated,
docstringed, and `ty`-clean.

- **Phase 0:** added `pgzero_gl/py.typed`; chose **Option A** for scope —
  `entrypoint/format.sh` now runs `ty check /mvp/ports/codetheclassics/pgzero_gl`
  (shim only; the faithful-port games stay out of `ty`/`ruff` scope until Phases
  2–3). Baseline was 34 diagnostics (30 once `just_playback` resolved).
- **Phase 1:** all 15 shim modules done — `context`, `_types` (new shared-types
  module: `Color*`/`Point*` aliases + `Drawable`/`RGBASource` Protocols),
  `geometry`, `mask`, `surface`, `resources`, `input`, `audio`, `text`, `actor`,
  `screen`, `joystick`, `renderer`, `renderer_gl1`, `runner`, `__init__`.
  `ty check .../pgzero_gl` → **All checks passed!**; all modules `py_compile`
  clean; `import pgzero_gl` works.
- **`_smoketest.py` does NOT exist** (the plan above assumed it). Verification was
  by `ty` + `py_compile` + import smoke test instead. On-window runs remain
  Bill-verified.
- **Decisions resolved:** dynamic-attribute APIs use a typed `__getattr__`
  (`Keyboard.__getattr__ -> bool`, `_Keys.__getattr__ -> int`, `Actor.__getattr__
  -> Any`) rather than explicit per-name properties (`Rect` keeps its existing
  explicit corner/edge properties). Weakly-typed FFI (PyOpenGL constants, GLFW
  window handles, `just_playback`, the synthetic `pygame`/`pgzrun`/`pgzero`
  `ModuleType`s) is contained as `Any` at the boundary with a comment. `ty`
  strictness left permissive (Any at the FFI edge).
- **Keyword arguments (per Bill, 2026-06-28):** the shim's *internal* call sites
  now pass multi-argument calls to the shim's own drawing/helper API **by
  keyword** (`draw_image(image=…, topleft=…)`, `_render(text=…, size=…)`,
  `_Loader(subdir=…, extns=…, make=…)`, the matrix helpers, etc.). Scope was
  explicitly **shim internals only** — the game ports stay byte-faithful to
  upstream and are NOT rewritten to keyword form; parameters were NOT made
  keyword-only (public signatures must stay positionally pygame/pgzero-compatible
  or the unmodified games break). Single-arg calls, operator dunders, `Rect(*args)`,
  and the `Vector2(a, b)` coordinate constructors stay positional.
- **Two latent runtime issues fixed while typing** (behaviour-preserving): the
  `pygame.transform` shim now uses `PILImage.Resampling.NEAREST/BILINEAR` (the
  non-deprecated form; the bare `PILImage.NEAREST` aliases are gone from the
  stubs and slated for removal upstream), and `audio._Playback`/`text` legacy
  Pillow `textsize` were made import/attr-robust. See git diff.

## Goal

Three deliverables, in dependency order:

1. **Type hints for the `pgzero_gl` compatibility shim** (`ports/codetheclassics/pgzero_gl/*.py`, 15 modules) — annotate the public API the games call, and the internals.
2. **Docstrings for the `pgzero_gl` shim** — module + class + public-method docstrings explaining *what pgzero/pygame behaviour each piece emulates and how*, so a reader understands the shim without cross-referencing pygame.
3. **Type hints for the game ports** — Vol 1 (`vol1/*/<game>.py`, 5 games) and Vol 2 (`vol2/*/<game>.py`, 5 games).

End state: `ty check` passes over `ports/codetheclassics/`, the shim is a documented, `py.typed` package, and the games carry annotations — all with **zero runtime/behaviour change**.

## Why

The shim is hand-written infrastructure that reimplements a third-party API (PyGame Zero / pygame); types + docstrings make it maintainable and let `ty` catch regressions. The games call into it, so once the shim's surface is typed the games' own annotations become checkable rather than cosmetic.

## Current state (measured 2026-06-28)

| Group | Files | ~Lines | ~defs | Annotated |
|---|---|---|---|---|
| `pgzero_gl/` shim | 15 | ~2,450 | ~230 | **0** |
| `_smoketest.py` | 1 | 177 | 4 | 0 |
| Vol 1 games | 5 | ~4,290 | ~185 | 0 |
| Vol 2 games | 5 | ~8,420 | ~420 | 0 |

- Type checker is **`ty`** (`entrypoint/format.sh` runs `ty check /mvp/src` + `/mvp/tests`; `ruff` formats). **`ports/` is NOT in the checked scope today** — see Phase 0.
- No `pgzero_gl/py.typed` marker, so even once typed the games/`ty` won't see the shim's types until it's added.
- The shim already has good *prose header comments* per module, but **no real docstrings** on classes/methods.
- Headless verifier exists: `_smoketest.py` renders one frame of a game to an offscreen EGL pbuffer + PNG (used to catch render regressions). This is the safety net for "behaviour unchanged".

## Constraints (read before touching the games)

- **Annotations only — do NOT restructure.** The games are faithful ports of the upstream books (BSD-2-Clause, © Eben Upton; see the per-file headers). Per the repo's pedagogy (`CLAUDE.md`: "demos are deliberately procedural … don't clean up by introducing classes"), keep the line-by-line correspondence with upstream. Add type hints; do not rename, reflow, extract functions, or change control flow.
- **No behaviour change anywhere.** Annotations are erased at runtime; if a change is needed to satisfy `ty` (e.g. a `cast`, a `# type: ignore[...]` with reason, an `assert x is not None`), prefer the least-invasive option and note it.
- **Faithful-port note:** because game changes are modifications to derivative BSD code, keep them minimal and mechanical; the diff should read as "added annotations", nothing else.

## Plan

### Phase 0 — tooling + scope (do first, small)
- Add **`pgzero_gl/py.typed`** (empty marker) so the package's types are consumed by the games and `ty`.
- Decide how `ports/codetheclassics/` enters the **`ty` check scope**:
  - Option A: extend `entrypoint/format.sh` to also `ty check /mvp/ports/codetheclassics` (enforced in `make format`/CI).
  - Option B: a scoped `ty` config (`[tool.ty]` in `pyproject.toml` or a local config) — gradual: start with the shim, add the games as they're done.
  - Recommend A + gradual file inclusion so a half-typed tree doesn't fail the whole check.
- Establish the **baseline**: run `ty check` on the shim, capture the current error count (expected high), so progress is measurable.
- Confirm `_smoketest.py` renders green *before* any change (golden frame), to compare against after.

### Phase 1 — `pgzero_gl` shim: types + docstrings (the core)
Work **leaf-modules first** (fewest internal deps), then the API-facing ones, so each module's imports are already typed:

1. `context.py` (57 ln) — process-wide state holder. Easy; sets the pattern.
2. `geometry.py` (403 ln, ~88 defs) — the `Rect`/`ZRect` work-alike. **Highest def-count**; mostly the virtual corner/edge properties (`left`/`center`/`topright`/…) and `colliderect`/`collidepoint`/`move`/`inflate`. Type the property getters/setters (`float` coords, `tuple[float,float]` points) and the collision API.
3. `surface.py` (133 ln) — CPU `pygame.Surface` work-alike, backed by numpy. Use `numpy.typing.NDArray[np.uint8]` for pixel buffers; `tuple[int,int]` sizes; color tuples.
4. `mask.py` (49 ln) — collision mask over an alpha channel (numpy). Small.
5. `resources.py` (159 ln) — image/sound loaders; return shim `Surface`/sound handles; path types.
6. `text.py` (154 ln) — text rendering (no pygame/ptext). Font metrics, color, anchor.
7. `actor.py` (178 ln) — the `Actor` sprite. **Hard case:** dynamic anchor attributes (`.left`, `.center`, …) and `.image = "name"`. Decide between explicit `@property` declarations vs a typed `__getattr__`/`__setattr__ -> float`/`Any`. Prefer explicit properties for the documented anchor names; document the dynamic ones.
8. `input.py` (96 ln) — `keyboard` object. **Hard case:** boolean attribute access (`keyboard.space`). Type via `__getattr__(self, name: str) -> bool`; type the `keys` constants.
9. `joystick.py` (132 ln) — gamepad over GLFW; best-effort. Neutral-value returns; `float`/`bool`.
10. `audio.py` (154 ln) — `sounds`/`music` over `just_playback`. Type the play/loop/volume API; `just_playback` is untyped → may need a small local Protocol or `Any` at the boundary (note it).
11. `screen.py` (110 ln) — the `screen` draw object (blit/draw.*); delegates to the renderer.
12. `renderer.py` (304 ln) + `renderer_gl1.py` (152 ln) — GL back ends. **Boundary typing:** PyOpenGL + GLFW are weakly typed; GL handles are `int`, GLFW window handle is opaque (`Any`/glfw type). Type the public surface; allow `Any` at the GL FFI edge with a comment.
13. `runner.py` (168 ln) — game loop / window. Types for the hook callbacks (`update(dt: float)`, `draw()`, `on_key_down(key)`), the GLFW callbacks.
14. `__init__.py` (202 ln) — the package surface / the `import pgzero, pgzrun, pygame` shim shape. Type the re-exports and the `pgzrun.go()` entry.

For **docstrings** in Phase 1, every shim module gets:
- a **module docstring**: which pgzero/pygame object(s) it emulates, and the key fidelity decisions (e.g. top-left-origin y-down coords; why `just_playback` instead of `pygame.mixer`). Much of this already exists as header comments — promote/expand into a real `"""docstring"""`.
- a **class docstring** per public class (`Actor`, `Rect`/`ZRect`, `Surface`, `Screen`, `Keyboard`, …): the emulated API + behavioural contract the games rely on.
- **method docstrings** on public methods, focused on *divergences from / fidelity to* the real API (one line is fine where behaviour is obvious).

Keep the existing `pygame`/PyGame-Zero API doc links in the headers.

### Phase 2 — Vol 1 game ports (annotations only)
Order by size/complexity: `boing` (489) → `cavern` (803) → `bunner` (919) → `myriapod` (931) → `soccer` (1145).
- Annotate function signatures, class attributes, and module-level globals.
- The games' types are mostly: shim `Actor`/`Rect`, `float`/`int` positions, `list[Actor]`, `Enum` states, color tuples. The shim being `py.typed` (Phase 1) makes these resolve.
- Add the game to the `ty` scope (Phase 0) as each one goes green.

### Phase 3 — Vol 2 game ports (annotations only)
Same approach, larger files: `kinetix` (1228) → `avenger` (1466) → `eggzy` (1603) → `leadingedge` (1684) → `beatstreets` (2438). `beatstreets` (145 defs) is the single biggest unit — budget for it.
- Vol 2 also uses `joystick.py`; make sure its types landed in Phase 1.

### Phase 4 — enforce + verify
- `ty check` clean over the whole `ports/codetheclassics/` tree; remove any temporary per-file excludes from Phase 0.
- `ruff check`/`ruff format` clean.
- `_smoketest.py` renders the golden frame(s) identically (no behaviour drift).
- Smoke-run each game far enough to confirm it still launches (headless where possible; on-window runs are Bill-verified per `CLAUDE.md`).

## Hard cases to decide up front (collected from above)
- **Dynamic attribute APIs** (`Actor` anchors, `keyboard.<key>`): explicit `@property` vs typed `__getattr__`. Lean explicit for documented names, typed `__getattr__ -> bool/Any` for the open-ended ones.
- **Weakly-typed FFI** (PyOpenGL, GLFW, `just_playback`, numpy at the edges): contain `Any` at the boundary with a comment; don't let it leak into the public shim surface.
- **`ty` strictness level**: start permissive, tighten. Decide whether to allow `Any`-returning externals silently or annotate boundary Protocols.

## Verification checklist
- [ ] `pgzero_gl/py.typed` present; games resolve shim types.
- [ ] `ty check /mvp/ports/codetheclassics` → 0 errors.
- [ ] `ruff` clean.
- [ ] `_smoketest.py` golden frame unchanged.
- [ ] Each of the 10 games launches; no runtime regression.
- [ ] Diffs on game files are annotations-only (no structural change).

## Open questions
- **Scope of "types" on the games:** full signatures + locals, or signatures + module globals only? (Recommend signatures + class/global attributes; skip trivial local-variable annotations to keep the faithful-port diff small.)
- **`ty` vs adding `pyright`/`mypy`:** stay on the repo's `ty` (consistent with `src/`), or is stricter checking wanted for this subtree?
- **One PR/commit per phase**, or per game? (Recommend per-module/per-game commits so review stays small — Bill commits.)
- Should the shim eventually be extracted into its own installable package (its own `pyproject.toml`)? Out of scope here, but typing + `py.typed` is a prerequisite, so note it.
