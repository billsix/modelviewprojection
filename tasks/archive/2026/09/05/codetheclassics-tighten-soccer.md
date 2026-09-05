# Tighten soccer (Code the Classics vol 1)

**Status:** DONE 2026-09-05 (Fable session) — all gates green, staged; archived. Play-test audio
(looping crowd, the 1-second music fade-out on game start, one-shot effects) when convenient.
**Priority:** 4
**Difficulty:** 5
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` · **Depends on:** `tasks/archive/2026/09/05/codetheclassics-tighten-bunner.md` (same engine family) · **Next:** `tasks/codetheclassics-tighten-kinetix.md`
**Engine family:** vol1-rich (with bunner): `_types geometry context audio resources renderer surface draw text screen actor input __init__`; no mask/transform/joystick. Splice bunner's tightened engine.

## BLUF

Apply `tasks/reference/code-the-classics-tightening.md` to
`ports/codetheclassics/vol1/soccer/soccer.py` (3886 lines). Medium opportunity: `Game` and
`Player` are the dataclass targets (both have attributes wired after construction), several
`if/elif` chains without `else` in `Player.update`, and the whole `Surface` class is dead.

## Context (read first)

- Shape (HEAD 2026-09-05): banners `_types` 55 … `__init__` 2341; game code from 2446; `__main__`
  at 3810; alias line 53 `_text = audio = gldraw = sys.modules[__name__]`. `update()` no `dt`.
- Import-time: version check 2448–2453; `mixer.quit/init` 3788–3791; **`game = Game()` 3803 →
  `music.play("theme")` / `sounds.crowd.stop()` at import**.
- One `ty: ignore` in the game part: 2613 (`invalid-method-override`).

## Analysis

**Engine dead here:** `Surface` class 1510 entirely + `set_alpha`; `Image.get_width/get_height/
get_size/get_rect/gl_texture(direct)/from_rgba`; `_Loader.load/values/clear` (soccer never touches
`images` — blits by name); `Screen.clear/fill/bounds`; `Renderer.draw_image(direct)/filled_rect/
rect/polygon/circle/set_clip`; `_Painter.rect/filled_rect/line/circle/filled_circle`;
`_Surface.set_clip/blit/get_width/get_height/get_size`; `Sound.set_volume/get_volume`;
`_Music.play_once/set_volume/get_volume`; `Actor.distance_to/colliderect`;
`_RectBase.contains/move_ip/inflate/move`; `gfx_filled_polygon/gfx_polygon/rect/polygon` in draw.
Used and notable: **`keys.*` ×14** (3640–3650, 3688, 3706, 3708, 3736 — keep `_Keys` or use
GLFW constants), `getattr(sounds, …)` 3607, `screen.draw.text` 3601 (**debug-only,
`DEBUG_SHOW_COSTS`**), `screen.surface` as the first arg of `gldraw.line` 3572–3590,
`screen.blit` ×8, `music.fadeout(1)` 3304 + `music.play` 3309 (**keep `_Music.fadeout`**),
`sounds.crowd.play(-1)` 3305 (**loop path**) + `.stop()` 3310, `Rect(...)` 2483–2489.

**Game classes:** `Difficulty` 2532 dataclass; `MyActor` 2601 (`vpos`; sets `pos` 2615);
`Goal` 2652 / `Ball` 2725 / `Team` 3282 dataclasses (`Ball` already uses `default_factory`);
`Player` 2994 — hand `__init__` (`home team dir anim_frame timer shadow debug_target`) plus
**`peer`/`mark`/`lead` annotated at 2999–3001 but assigned cross-object in `Game.reset`
3358–3374** → they are declared, so `slots=True` is reachable; `Game` 3291 — hand `__init__`
that plays music (3300–3315) and calls `reset()`, which sets `players goals kickoff_player ball
camera_focus debug_shoot_target` (3328–3381) → declare all six; `Controls` 3637 (5 key fields);
`State`/`MenuState` enums.
**RNG trap:** `Game.reset` 3333–3345 calls `random_offset` four times per iteration in a fixed
order — no comprehension rewrite that changes call order.

**Function-tightening candidates:** `Player.update` 3062 (4-branch, no else), 3081 (3), 3083
(4), 3126 (3) — `match` + `case _: raise` where the subject is an enum/state; `Controls.move`
3652–3663 → two conditional expressions; 3705–3712 `selection_change` → expression;
`key_just_pressed` 3618–3635 → expression; 3601 `.format` → f-string; 3783 string concat →
f-string; 2850 `len(...) > 0` → truthiness; 3499 nested `dist_key_weighted` single-use closure
(`dist_key` 2582 exists); 3596–3600 single-use `screen_pos`; `steps()` 2640–2649 keep.

**pygame comments in the game part (5):** 2597–2598 (drop "extends Pygame Zero's Actor …
Pygame's Vector", keep "read/write position via vpos"), 3669 false, 3807 → banner, 3856 env var.

## Work record (2026-09-05)

- **Engine:** `splice_vol1_engine.py soccer "Substitute Soccer" - 800x480` (code-indexed keyboard:
  `keys.UP` etc. → `glfw.KEY_*`), plus soccer's additions: bunner's looping/volume/stop sounds
  **and a fade-out ramp** (`_Voice.fade_*`, `_Music.fadeout` — soccer's `music.fadeout(1)` on game
  start), a `draw_text(..., centered=True)` for the cost overlay, a `Renderer.line` primitive for
  the four debug line overlays, `Image.from_rgba`. Then the **renderer/image dataclass codemod**
  (below) ran on it like the other games.
- **Classes:** `Difficulty`/`Goal`/`Ball` → `slots=True`; `MyActor` plain + `__slots__` with
  `draw_at(world_to_screen)` replacing the widened `draw` override (its `ty: ignore` is gone);
  `Player` plain + a 10-name `__slots__` (its cross-object `peer`/`mark`/`lead` wiring declared);
  `Team` (`controls: Controls | None`, `active_control_player: Player | None`), **`Controls` →
  dataclass** (`player_num` InitVar, the five key codes assigned in one tuple in `__post_init__`),
  **`Game` → dataclass** (`p1_controls`/`p2_controls`/`difficulty_level` InitVars, the seven
  `reset()` attributes declared, music block + `reset()` in `__post_init__`, same order).
- **Functions:** `cost -> tuple[float, Vector]`; the CPU kick decision compares the two costs'
  first elements (the upstream compared whole tuples, which would have raised on an exact cost
  tie — its own comment admitted it); speed/bounds if-else → conditional expressions;
  `Controls.move` → two conditional expressions; the menu's up/down detection keeps BOTH
  `key_just_pressed` calls (each records its key's state for next frame) but folds the result into
  one expression; `1 - team` for the other team; `sounds.load(f"…")`; `blit(name, x, y)` with the
  camera-mapped positions unpacked via `float(v.x)`; f-strings; both `match state:` blocks end in
  `case _: raise`; the mixer no-ops and the Python-3.5 check are gone. `Game.draw`'s
  camera-as-inverse `world_to_screen` (the archived camera task) is untouched.
- **Numbers:** 3886 → 2552 lines (−34%); pygame/pgzero mentions 117 → 2.
- **Gates:** frame 180 AE=0 vs HEAD (the original 3886-line file); 1500-frame input trace
  (menu → 1P game, kick-off, running, shooting; a goal was scored, 833 frames of ball possession)
  byte-identical modulo the baseline's derived `left/centerx/centery` properties and the
  `Controls` object's rendering; `make format` ruff + ty clean; 104 tests.

## Open questions — settled by Fable (maintainer had delegated discretion)

- `DEBUG_SHOW_COSTS` text overlay: KEPT (centred `draw_text`). `Controls` stays a class (now a
  dataclass), not a Protocol.

Engine: splice bunner's, keeping `_Music.fadeout`, the `Sound` loop path, `Rect`. Game:
dataclass `Player`/`Game` with the declared set above (keep `reset()` order verbatim), the
`match` conversions, expressions, header, comments; fix or justify the 2613 suppression. Gates
as boing plus a key script that kicks off and shoots. Open question: keep the `DEBUG_SHOW_COSTS`
text overlay (and thus `_Painter.text`)? *(Recommend keep, as for bunner.)*
