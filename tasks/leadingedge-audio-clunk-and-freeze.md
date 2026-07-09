# leadingedge: engine audio still clunky, game still freezes — investigate

**Status:** FIXED 2026-07-09 (Bill: "ok go ahead and fix it") — staged,
uncommitted. **Remaining: Bill's ears** — rebuild the image (requirements
swapped just_playback -> miniaudio) or `pip install miniaudio` in the
running container, then drive leadingedge: the engine should crossfade
smoothly through the bands and the freeze should be gone.

## The fix (implemented)

`pgzero_gl/audio.py` rewritten on pygame.mixer's architecture, exactly as
proposed: **one** miniaudio `PlaybackDevice` (opened lazily on first play;
headless -> graceful no-op) fed by a software-mixing generator. Effects
decode ONCE into shared numpy float32 buffers; each play is a lightweight
`_Voice` (offset/volume/loop/fade state) mixed in the callback — gapless
loops via buffer wraparound, per-FRAME linear fade ramps (fade_ms /
fadeout run inside the mixer now; the 2026-07-09 fade thread is gone),
per-effect voice cap of 8 (pygame's default channel count), and
starting/stopping a voice is a flag flip under a lock. Music streams from
disk in 1024-frame chunks (a decoded multi-minute track would be tens of
MB) with loop-by-stream-restart, like SDL_mixer's streamed music. The
public API (`Sound`, `music`, `available`, per-play `volume` for
`mixer.Sound`) is unchanged; `just_playback` is dropped from
requirements (replaced by `miniaudio`).

**Verified headless in-container** by driving the mixer generator by
hand against real leadingedge assets: gapless loop wraparound
(sample-exact), non-loop end, fade-in ramp from silence, fadeout to
zero + voice removal, additive mixing with per-play volumes, the exact
engine band-change shape (two crossfading looped engine samples ->
old voice fades out and is removed), the 8-voice cap with
oldest-eviction, and music streaming/volume/fadeout(seconds)/play_once
against `ambience`/`title_theme`. Plus: ty all-clean, ruff clean,
60 pytest, definitions gate 10/10, and the avenger `mixer.Sound`
wrapper re-verified over the new backend.

Worth knowing: total OS audio streams is now exactly ONE, ever — the
freeze mechanism (client-slot exhaustion blocking the game thread) is
structurally impossible, and band changes no longer touch devices at
all (crossfades are pure math in the callback).
**Created:** 2026-07-09

## Investigation results (2026-07-09)

**Method** (per Bill): cloned the untouched upstream
(`raspberrypipress/Code-the-Classics-Vol2`) and pgzero
(`lordmauve/pgzero`) sources; compared against our port and read
just_playback's installed source. (NB the in-repo import dc5bb77e was
already shim-based, but its game LOGIC is byte-identical to upstream —
verified by diff; only annotations/formatting differ. So the entire
behavioural delta is the audio framework.)

**How the original stack works** (pgzero + pygame.mixer/SDL_mixer):
- pgzero calls `pygame.mixer.pre_init(22050, -16, 2)` — **one** audio
  device for the whole process, opened once.
- `sounds.engine_short17` is `pygame.mixer.Sound(path)`: the file is
  **fully decoded into a memory buffer at load**.
- `play(loops=-1, fade_ms=100)`, `fadeout(150)`, `set_volume` all execute
  inside SDL_mixer's single audio callback, software-mixing N channels:
  **gapless loops** (buffer wraparound), **sample-accurate fades**, zero
  device operations per play. Starting/stopping a sound is a flag flip.

**How our shim works** (just_playback/miniaudio — from its source):
- **Every `Playback` owns its own miniaudio audio STREAM** —
  `load_file()` runs `terminate_audio_stream` + decode +
  `init_audio_stream`, and volume is set at DEVICE level
  (`set_device_volume`). Our `audio.Sound` pools up to
  `_MAX_VOICES_PER_SOUND = 8` such Playbacks per sound and — by design,
  to avoid the no-finalizer leak — **keeps them open forever** for
  reuse.
- leadingedge ships **41 engine sample files** (+22 other sounds).
  Driving through the speed range touches up to 40 engine sounds → up to
  40 permanently-open OS audio streams, plus the skid loop, plus
  road/grass/zoom pools (≤8 voices each).

**Root cause — the clunk**: an engine band change stops one OS-level
stream and starts another (unsynchronized device start/stop = clicks;
start latency is tens of ms), and the FIRST play of each band runs
decode + stream-init **on the game thread** (a frame hitch per new
band). A sample-level crossfade across two separate devices is
physically impossible — which is why the 50 Hz volume-ramp fade engine
improved semantics but couldn't fix the sound. One-shot effects reuse an
already-open stream, hence "other sounds are smooth".

**Root cause — the freeze**: stream accumulation. Dozens of concurrent
ALSA/PipeWire streams (one per pooled voice) exhaust the finite dmix/
client slots; when that happens, snd_pcm calls **block the calling
thread** — and our play()/stop() run inline on the game thread. Matches
the freeze arriving after driving a while (bands accumulate), not at
startup.

**Why no other game shows it**: the others use a handful of one-shot
sounds (≤8 streams/sound, few sounds hot); only leadingedge multiplies
41 loopable samples by the stream-per-voice architecture.

## The fix (proposed — needs go-ahead)

Rebuild `pgzero_gl/audio.py` on pygame.mixer's architecture: **one**
output device + a software mixer.
- Backend: the `miniaudio` (pyminiaudio) package — one `PlaybackDevice`
  with a single mixing generator over **decoded in-memory buffers**
  (numpy add + clip), or `sounddevice`/PortAudio equivalently.
- Per-voice state (offset, volume, loop flag, fade ramp) lives in the
  mixer: gapless loops = buffer wraparound; fades = per-chunk ramps;
  play/stop = flag flips. Zero device operations after startup.
- Keep the existing public surface (`Sound`, `music`, `mixer.Sound`,
  per-play volume) so the games and the earlier fixes are untouched;
  drop `just_playback` from requirements. The 2026-07-09 fade-engine
  thread becomes unnecessary (fades move into the mixer callback).
- Est. ~200–300 lines; test headless via a null/none backend if
  miniaudio offers one, else Bill's ears.

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
