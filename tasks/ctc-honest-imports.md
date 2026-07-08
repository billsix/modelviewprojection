# Code the Classics: retire the synthetic pygame/pgzero/pgzrun modules

**Status:** proposed — needs go-ahead
**Created:** 2026-07-08

## Goal (Bill, 2026-07-08)

Make the games' imports reflect what is actually imported. Today
`pgzero_gl/__init__.py`'s `_make_pygame()` forges a synthetic `pygame`
module (plus `pygame.math`, `pygame.mixer`, …) out of shim parts and
registers it in `sys.modules` — so upstream lines like
`from pygame.math import Vector2` resolve to `pgzero_gl.geometry.Vector2`
at runtime while being statically unresolvable. Same trick backs `pgzero`
(version attribute) and `pgzrun` (`.go()`). Replace all of it with direct
imports from the shim, and delete the module-forging machinery.

Fits the 2026-07-08 policy shift: the games are behaviour-faithful, no
longer byte-faithful — impersonating pygame was only ever needed to keep
upstream text verbatim.

## Survey (2026-07-08): the whole synthetic surface

~94 sites across the 10 games, ~12 API shapes:

| synthetic usage | count | honest replacement |
|---|---|---|
| `from pygame.math import Vector2/Vector3` | 6 | `from pgzero_gl.geometry import …` |
| `pygame.mixer.init/quit/set_num_channels/find_channel` try-blocks | ~21 | `from pgzero_gl import mixer` (same stub object) |
| `pygame.joystick.get_count()` etc. | 5 | `from pgzero_gl import joystick` |
| `pygame.draw.line/rect/polygon` (leadingedge track, bunner debug) | 8 | shim draw helpers, exported properly |
| `pygame.Rect` / `from pygame.rect import Rect` | 3 | `from pgzero_gl.geometry import Rect` |
| `pygame.transform.scale/smoothscale` (leadingedge) | 2 | shim surface API |
| `pygame.mask.from_surface` | 1 | `from pgzero_gl import mask` |
| `from pygame import surface` (kinetix) | 1 | shim surface module |
| `import pgzero` + `pgzero.__version__` version-check boilerplate | 16 | DELETE the blocks — they check a library that isn't there |
| `pgzrun.go()` | 10 | the shim runner's real name (see pgzero_gl/runner.py) |

Shim side: delete `_make_pygame()` + the `sys.modules["pygame*"]`
registrations (~130 lines in `pgzero_gl/__init__.py`), export the real
names via `__all__`.

## Why it's low-risk

Every call site routes to the exact same shim object it reaches today —
only the import path changes. Failure modes are loud (`ImportError` /
`NameError` at boot), not subtle. One check during implementation: make
sure no shim-internal code reads the synthetic module back out of
`sys.modules` (internals appear to use relative imports).

## Payoffs

- The 4 format-fragile `# ty: ignore[unresolved-import]` suppressions on
  the pygame imports disappear (the imports become statically resolvable —
  these fought `ruff format` during the 2026-07-08 formatting work).
- ~130 lines of module-forging machinery deleted; the shim's public API
  becomes its actual API.
- Clears the ground for [[ctc-vector2-deferral]]: Vector2's provenance is
  visible at the import site.

## Sequencing / gates

- Slot AFTER the in-flight display verification of the dataclasses +
  formatting batch (don't stack another all-games diff before those boots),
  and BEFORE [[ctc-vector2-deferral]].
- Per-game chunks; gate each with py_compile + `ty check` (expect the
  diagnostic count to DROP), full-tree ruff, and Bill's boot pass.
- The version-check deletions are the only non-mechanical judgment: they're
  upstream boilerplate guarding a pgzero that doesn't exist — removing them
  is the honest move, but flag it in the diff summary for Bill.
