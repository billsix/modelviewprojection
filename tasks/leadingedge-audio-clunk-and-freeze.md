# leadingedge: engine audio still clunky, game still freezes — investigate

**Status:** proposed — investigate later (Bill, 2026-07-09). Reproducible
on Bill's machine; NOT reproducible headless (no sound hardware in the
build container), so diagnosis needs his box.
**Created:** 2026-07-09

## Symptoms (Bill)

1. The engine/acceleration sound is clunky, while other (one-shot)
   sounds are smooth.
2. The game freezes during play.

## What was already tried — and DIDN'T fix it (important data)

The 2026-07-09 fade engine (audio.py): real volume-ramp
`fadeout`/`fade_ms` replacing the old stop-then-restart hard cuts, on
the theory that (a) band-change hard cuts were the clunk and (b)
stop()/play() storms on live miniaudio streams when the speed band
flapped were the freeze. **Both symptoms persist**, so that hypothesis
is disproven or at best incomplete. The fade engine is still the right
behaviour (pygame semantics) — keep it — but the causes are elsewhere.

## Bill's requested method: compare against the original code in git history

- `git log --follow` on `ports/codetheclassics/vol2/leadingedge/leadingedge.py`,
  `pgzero_gl/audio.py`, and `pgzero_gl/runner.py`: find the last commit
  where Bill remembers leadingedge audio behaving well (if it EVER did
  under the shim — also worth asking: was it only ever smooth under real
  pygame?), then diff/bisect forward.
- Compare the port against the upstream Code the Classics Vol 2
  leadingedge (the book repo) for how pygame.mixer is actually being
  driven — especially anything the shim's audio model (one
  just_playback Playback per voice) structurally can't reproduce.

## Suspects for the next session

- **Loop-boundary gap (clunk, strongest candidate now):** the engine is
  40 SHORT looping samples (`engine_short0..39`); real pygame loops
  gaplessly. If `just_playback`'s `loop_at_end` has a gap/click at the
  loop point, the engine sounds clunky *within* a band, independent of
  transitions — matching "still clunky after the fade fix". Test on
  hardware: hold a constant speed (one band, no transitions) — if it
  still puts, it's the loop boundary, and the fix direction is a
  gapless backend path (or preloading into a seamless loop buffer).
- **Device/stream exhaustion (freeze):** every `_Playback` voice is its
  own just_playback stream (own miniaudio device?). leadingedge holds
  40 engine Sounds + skid + road/grass/zoom effects; count live streams
  at freeze time. ALSA device exhaustion or dmix contention could hang.
- **The fade thread** interacting with just_playback from a second
  thread (set_volume/stop off the main thread) — if just_playback isn't
  thread-safe on Bill's backend, that's new-in-2026-07-09 code; try
  disabling the fade thread as an A/B.
- **Freeze data wanted from Bill's next repro:** Ctrl-C traceback (shows
  where the main thread is stuck); does music keep playing when the
  window hangs (audio thread alive vs whole-process wedge)?;
  `PYTHONFAULTHANDLER=1` or py-spy dump if handy.

## Related

- The fade engine + its rationale: `tasks/ctc-shim-dynamism-audit.md`
  (audio round section) — that task should archive independently; this
  investigation is deliberately split out.
- Known, separate, graceful gap: `mixer.find_channel()` → None
  (beatstreets scooter engine silent).
