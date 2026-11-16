# Step 3 — re-extract the shared engine library from the Code-the-Classics games (done 2026-11-15)

**Part of:** `tasks/archive/2026/11/15/pgzero-gl-inline-strip-reextract.md` (umbrella) · **Followed:**
`tasks/archive/2026/09/05/pgzero-gl-step2-strip-and-restructure.md` and the tightening pass
`tasks/archive/2026/09/05/codetheclassics-tighten-games.md`
**Branch:** `pgzero-gl-step3-reextract-library` (authorized batch: the agent committed; the maintainer merges).
**Durable record:** `tasks/reference/code-the-classics-tightening.md` §9 (what is shared, what stays per game,
why) and `tasks/reference/notable-subsystems.md` §4a (the modules).

## What was done

The eleven game files under `ports/codetheclassics/vol{1,2}/` stopped carrying their own copies of the code
that is the same in every game, and now import it from `src/modelviewprojection/pgzero_gl/`:

- `audio.py` — `Sound`, `Music(root)`, `shutdown_audio()`: the one-device miniaudio mixer. It is the union
  of the per-game variants (avenger/leadingedge's voices with looping, fade-in, fade-out and per-play
  volume; leadingedge's `Music.fadeout`). With no fade active the gain is `1.0 * volume`, the same float the
  simpler mixers computed.
- `resources.py` — `Image` (CPU pixels, lazy GL texture) and `Loader[T](root, subdir, extns, make)`; each
  game builds `images`/`sounds` from its own `ASSET_ROOT`.
- `gl.py` — `link_program(vertex_source, fragment_source)`, `compile_shader`, `make_buffer`, `GLBuffer`,
  `ortho_pixels`.

Each game kept its loop, `Renderer`, `SpriteRenderer`, shaders, `Uniforms`, `MODEL`, `Actor`, `Rect`,
`Keyboard`, gamepad code and `Surface`. The game files went from 29,341 to 23,905 lines; the four package
modules are 683 lines. The 2026-09 PyGame Zero facade modules that nothing imported (`runner`, `actor`,
`screen`, `input`, …) were deleted from `pgzero_gl/`.

Also changed: `tests/test_ctc_actor_field_collisions.py` checks each game's own `Actor` (it had read the
deleted `pgzero_gl/actor.py`); the ruff per-file ignores and comments in `pyproject.toml`,
`entrypoint/format.sh` and `tools/ctc_capture_frame.py`; both licence texts; the game docstrings;
CLAUDE.md, the ports README and the reference docs. The all-games gate driver was promoted to
`tools/ctc_gate_all.sh`.

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-11-15)

1. **Criterion:** extract a unit only if at least 7 of the 11 files carry it in the same shape AND it teaches
   nothing about the game. That admitted audio, asset loading and the GL helpers; `Actor`/`Rect`/`Renderer`
   pass the count but stay per game as the teaching gradient from boing to beatstreets.
2. **Home:** the existing `src/modelviewprojection/pgzero_gl/` directory, so the code is part of the mvp
   package (this overrode the 2026-11-05 assessment, which had put it under `ports/` for licence reasons).
3. **Scope:** the whole step at once, not only the dead-code clean-up.
4. **Imports:** plain `from modelviewprojection.pgzero_gl.audio import …`; the editable install puts the
   package on the path, so no `sys.path` handling.
5. **CLAUDE.md:** "one self-contained file" became "self-contained apart from the shared engine modules".

Agent judgment calls, made under the batch go-ahead:

- **Shaders, `Uniforms` and `MODEL` stayed in the games.** The shader text belongs next to the renderer that
  uploads to it, so `link_program` takes the two sources as arguments.
- **Licence:** the new modules carry the directory's LGPL-2.1 (the code is the maintainer's own engine code,
  previously BSD-2-Clause inside each game). The games stay BSD-2-Clause and import an LGPL library, as the
  upstream games import pygame. `ports/codetheclassics/LICENSE` and `pgzero_gl/LICENSE` say so.
- **Pre-existing stale docs fixed in passing:** the ports README (the retired facade, a `PGZERO_GL` backend
  switch and `PGZERO_GL_INFO` that no game has, two deleted task docs) and the "upstream has no licence"
  claim (the game code is BSD-2-Clause per the Debian packaging); a `pyproject.toml` comment listing
  ignore rules removed 2026-09-09; a ty-diagnostic citation of a deleted file in
  `tasks/reference/python-coding-standard-mvp.md`.

## Verification

- Per game, against `master` (`tools/ctc_gate_all.sh`): frame-180 pixel identity (`tools/ctc_verify_game.sh`,
  AE=0) and a 300-frame scripted-input state trace (`tools/ctc_state_trace.py` + `ctc_compare_traces.py`;
  start, arrows, z, a, pause). All 11 identical; every traced frame was a distinct state, so the trace covered
  play rather than an idle screen. One capture timed out on the unchanged avenger baseline and passed on
  re-run (13 s); the script's header records it as a flake.
- `make check-format`, `make type-check` (ty + the annotation checker over `src`, `tests`, `ports/**`) and
  `make test` (66 passed) green on the branch. The book was not touched (no `doc-region` markers in `ports/`
  or `pgzero_gl/`).
- The codemod plus `ruff format` left a zero diff on a second run.
- **Audio and gamepad:** not gated; the maintainer (William Emerison Six <billsix@gmail.com>)
  play-tested the games on 2026-11-16: "they seem to work".

## Scripts

`tasks/adhoc/pgzero-gl-step3-reextract-library/` held `engine_defs.py` (the per-definition variant table;
its output `data/engine-defs-before.txt` was the worklog) and `use_library.py` (the codemod). Both were
one-shot and were removed in the archive commit; see that commit's parent for their text.
