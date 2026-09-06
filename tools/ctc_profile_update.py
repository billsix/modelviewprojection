#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Whole-game measurement for tasks/pointlike-type-study.md: how long a game's
# update() takes per frame, and how much of that is gacalc vector work. Runs a
# game the way tools/ctc_state_trace.py does (as __main__, loop disabled, audio
# stubbed, keys scripted) but times N frames of update() instead of dumping
# state, then prints a cProfile summary restricted to gacalc's modules.
#
# Promoted from tasks/adhoc/pointlike-type-study/ on 2026-09-06: run it whenever
# a game feels slow, or after a change to the vector/point types, and compare
# the µs/frame and the gacalc share with tasks/reference/point-type-decision.md.
#
# Usage (in the project container, DISPLAY set):
#   python tools/ctc_profile_update.py <game.py> <frames> <keyscript>
# keyscript as for ctc_state_trace.py, e.g.
#   "5:z:press,6:z:release,30:z:press,31:z:release".

import cProfile
import inspect
import os
import pstats
import random
import runpy
import sys
import time

random.seed(0)
sys.modules["miniaudio"] = None  # type: ignore[assignment]

import glfw  # noqa: E402

game_path, n_frames, keyscript = sys.argv[1], int(sys.argv[2]), sys.argv[3]
events: dict[int, list[tuple[str, str]]] = {}
for ev in filter(None, keyscript.split(",")):
    frame, key, action = ev.split(":")
    events.setdefault(int(frame), []).append((key, action))

glfw.window_should_close = lambda _win: True  # type: ignore[assignment]
sys.path[0] = os.path.dirname(os.path.abspath(game_path))
mod = runpy.run_path(game_path, run_name="__main__")["update"].__globals__
keyboard = mod["keyboard"]
press = getattr(keyboard, "press", None) or getattr(keyboard, "_press")
release = getattr(keyboard, "release", None) or getattr(keyboard, "_release")
update = mod["update"]
takes_dt = bool(inspect.signature(update).parameters)


def code(name: str) -> int:
    return getattr(glfw, "KEY_" + name.upper())


def run() -> None:
    for frame in range(n_frames):
        for key, action in events.get(frame, []):
            (press if action == "press" else release)(code(key))
        update(1.0 / 60.0) if takes_dt else update()


t0 = time.perf_counter()
prof = cProfile.Profile()
prof.runcall(run)
total = time.perf_counter() - t0
name = os.path.basename(game_path)
per_frame = total / n_frames * 1e6
print(  # noqa: T201 -- the report is the output
    f"{name}: {n_frames} frames of update() in {total * 1e3:.0f} ms "
    f"= {per_frame:.0f} µs/frame (profiled; 60 Hz budget is 16667 µs)"
)
stats = pstats.Stats(prof)
gacalc_t = sum(
    ct
    for (fn, _, _), (_, _, _, ct, _) in stats.stats.items()  # type: ignore[attr-defined]
    if "/gacalc/" in fn
)
gacalc_ms = gacalc_t * 1e3
print(f"time inside gacalc modules (cumulative): {gacalc_ms:.0f} ms")  # noqa: T201
print("--- top gacalc functions by cumulative time ---")  # noqa: T201
stats.sort_stats("cumulative").print_stats("gacalc", 12)
