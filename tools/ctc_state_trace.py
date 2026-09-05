#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Seeded differential STATE trace for the Code-the-Classics games -- the
# input-path complement to the frame-capture gate (tools/ctc_verify_game.sh
# only ever sees the no-input attract mode). Run it after any edit to a game:
# once on the committed baseline (`git show HEAD:<game>`, written beside the
# game as `_baseline_<game>.py` so its assets resolve) and once on the working
# tree, with the same key script, then compare the dumps with
# tools/ctc_compare_traces.py.
# Promoted from tasks/adhoc/codetheclassics-tighten-games/ on 2026-09-05.
# This imports a game as a plain module (so its loop is disabled -- see below
# -- but its window IS created), seeds `random`, then drives update() for N
# frames while scripting key presses/releases, and after every frame dumps a
# canonical picture of the module's game state: the
# `state`/`num_players`-style module globals plus the whole object graph under
# `game` (dataclass fields and __slots__/__dict__ attrs, lists, enums by name,
# gacalc vectors by coordinates, callables by name). Run it on the committed
# baseline and on the working tree and diff the two dumps: identical output
# means the tightening changed no observable state on that input path.
#
# Usage (in the project container, with DISPLAY pointing at an X server):
#   python tools/ctc_state_trace.py <game.py> <frames> <keyscript> \
#       [skip,keys] > trace.txt
# keyscript: comma-separated  <frame>:<keyname>:<press|release>  events, e.g.
#   "5:space:press,6:space:release,40:z:press,70:z:release,80:space:press"
# Key names are the game's own keyboard names (a, z, k, m, up, down, space...).

import enum
import inspect
import os
import random
import runpy
import sys
from dataclasses import fields, is_dataclass

random.seed(0)
# No audio: the trace is about game state, and opening a miniaudio device in
# a headless container is slow and can block. A None entry in sys.modules
# makes the game's `import miniaudio` raise ImportError, so its audio layer
# falls back to no-ops (exactly what it does on a machine with no sound card).
sys.modules["miniaudio"] = None  # type: ignore[assignment]

import glfw  # noqa: E402  (must follow the seed; game shares this module)

game_path, n_frames, keyscript = sys.argv[1], int(sys.argv[2]), sys.argv[3]
# Optional 4th argument: attribute names to leave out of the dump (e.g.
# leadingedge's 3000-piece `track`, which would swamp the trace).
SKIP: set[str] = set(sys.argv[4].split(",")) if len(sys.argv) > 4 else set()
events: dict[int, list[tuple[str, str]]] = {}
for ev in filter(None, keyscript.split(",")):
    frame, key, action = ev.split(":")
    events.setdefault(int(frame), []).append((key, action))

# The games create their window and run their loop at module level, demo
# style, so run the file as __main__ but make the loop exit at once: the
# window and renderer get built, zero frames run, and this harness then
# drives update() itself. (Needs a DISPLAY, e.g. the sandbox's Xvfb.)
glfw.window_should_close = lambda _win: True  # type: ignore[assignment]
# Run directly, a game's sys.path[0] is its own directory (eggzy finds its
# tilemaps/ and replay file there); under this harness it would be ours.
sys.path[0] = os.path.dirname(os.path.abspath(game_path))
# runpy returns a COPY of the module globals; update() rebinds `game`/`state`
# in the live namespace its functions close over, so snapshot THAT dict.
mod = runpy.run_path(game_path, run_name="__main__")["update"].__globals__
keyboard = mod["keyboard"]
# Baseline (pre-tightening) boards register keys as `_press`/`_release`.
press = getattr(keyboard, "press", None) or getattr(keyboard, "_press")
release = getattr(keyboard, "release", None) or getattr(keyboard, "_release")


def code(name: str) -> int:
    return getattr(glfw, "KEY_" + name.upper())


def canon(obj, depth=0):  # noqa: ANN001  (a generic walker)
    if depth > 6:
        return "..."
    if isinstance(obj, enum.Enum):
        return obj.name
    if isinstance(obj, (bool, int, float, str)) or obj is None:
        return obj
    if callable(obj) and not is_dataclass(obj):
        return "fn:" + getattr(obj, "__qualname__", repr(obj)).split(" at ")[0]
    if isinstance(obj, (list, tuple)):
        return [canon(x, depth + 1) for x in obj]
    if isinstance(obj, dict):
        return {str(k): canon(v, depth + 1) for k, v in sorted(obj.items())}
    if isinstance(obj, set):
        return sorted(repr(x) for x in obj)
    if hasattr(obj, "coeff_e_3"):  # a gacalc g3 vector: coordinates only
        return ("vec3", float(obj.x), float(obj.y), float(obj.z))
    if hasattr(obj, "coeff_e_1"):  # a gacalc g2 vector: coordinates only
        return ("vec", float(obj.x), float(obj.y))
    # Union of dataclass fields, __dict__ attrs, __slots__ AND the class's
    # public properties (an Actor's x/y/pos/image live behind properties),
    # sorted, plus the class name: the same object dumps identically whether
    # it is a dataclass, slotted, or plain.
    names: set[str] = set()
    if is_dataclass(obj):
        names |= {f.name for f in fields(obj)}
    names |= set(getattr(obj, "__dict__", {}))
    for c in type(obj).__mro__:
        names |= set(getattr(c, "__slots__", ()))
        names |= {n for n, v in vars(c).items() if isinstance(v, property)}
    out = {
        n: canon(getattr(obj, n, None), depth + 1)
        for n in sorted(names)
        if not n.startswith("_") and n not in SKIP
    }
    out["class"] = type(obj).__name__
    return out


for frame in range(n_frames):
    for key, action in events.get(frame, []):
        (press if action == "press" else release)(code(key))
    # leadingedge's update() takes the frame delta; the others take nothing
    if inspect.signature(mod["update"]).parameters:
        mod["update"](1.0 / 60.0)
    else:
        mod["update"]()
    snapshot = {
        k: canon(mod[k])
        for k in ("state", "num_players", "space_down", "game")
        if k in mod
    }
    print(frame, snapshot)
