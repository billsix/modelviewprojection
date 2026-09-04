#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Measure what Actor._offset_cache actually saves, to decide whether to keep it.
#
# Background: the cache memoizes _anchor_offset() (2x _calc + one Vector build).
# It was justified by the 2026-07-09 audit of the OLD __getattr__ string-ladder
# x/y read path (x/y were 93% of ~2.5M dynamic reads per game session). Now that
# x/y are plain properties, this re-measures the SAME hot path with the cache on
# vs. off, and scales the delta to a 2.5M-read session so "is it noise?" has a
# concrete answer.
#
# Run (in the mvp container; no GL/display needed):
#   source /venv/bin/activate && cd /mvp
#   PYTHONPATH=/mvp/src python tasks/adhoc/pgzero-gl-offset-cache/measure.py

import time

from gacalc.g2 import Vector

from modelviewprojection.pgzero_gl import actor as actor_mod
from modelviewprojection.pgzero_gl.actor import Actor


class FakeImg:
    """A stand-in Drawable so we can build an Actor with no image file / GL."""

    width = 64
    height = 48

    def gl_texture(self) -> int:  # never called on the x-read path
        return 0


def make_actor() -> Actor:
    # centre anchor + a real position -- the common game case.
    return Actor(FakeImg(), pos=(100.0, 100.0), anchor=("center", "center"))


# An _anchor_offset that ALWAYS recomputes (the "no cache" variant). Same math
# as the real one, minus the cache read/store.
def _uncached_anchor_offset(self: Actor) -> Vector:
    av = self._anchor_value
    return Vector(
        actor_mod._calc(value=av[0], dim="x", total=self._rect.width),
        actor_mod._calc(value=av[1], dim="y", total=self._rect.height),
    )


def time_x_reads(a: Actor, n: int) -> float:
    _ = a.x  # warm (fills the cache for the cached variant)
    t0 = time.perf_counter()
    s = 0.0
    for _ in range(n):
        s += a.x
    return time.perf_counter() - t0


N = 2_000_000
SESSION_READS = 2_500_000  # the audit's per-session x/y read count

# Cached = the current shipping implementation.
t_cached = time_x_reads(make_actor(), N)

# Uncached = patch _anchor_offset to recompute every call.
orig = Actor._anchor_offset
Actor._anchor_offset = _uncached_anchor_offset  # type: ignore[method-assign]
try:
    # correctness: the two variants must give the same x.
    assert make_actor().x == make_actor().x
    t_uncached = time_x_reads(make_actor(), N)
finally:
    Actor._anchor_offset = orig  # type: ignore[method-assign]

saved_ns = (t_uncached - t_cached) / N * 1e9
session_ms = (t_uncached - t_cached) / N * SESSION_READS * 1000

print(f"N = {N:,} Actor.x reads")
print(f"  cached (current):   {t_cached:.4f}s  ({t_cached / N * 1e9:6.1f} ns/read)")
print(f"  uncached (recompute): {t_uncached:.4f}s  ({t_uncached / N * 1e9:6.1f} ns/read)")
print(f"  cache saves ~{saved_ns:.1f} ns/read")
print(
    f"  over a {SESSION_READS:,}-read session (the audit's count): "
    f"cache saves ~{session_ms:.2f} ms TOTAL"
)
