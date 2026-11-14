#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Deterministically capture frames of one SuperBible v4 port, for the proof
# that the AppState refactor changed no pixels.  Run by frame_identity.sh,
# once against the pristine tree and once against the working tree.
#
# What makes two runs comparable:
#   - `random` is seeded before the app runs;
#   - the clock is FAKE: time.monotonic / time.time / time.perf_counter /
#     glfw.get_time all return frames_swapped / 30, so a timer-driven
#     animation advances by the frame COUNT, not by wall-clock jitter;
#   - the capture reads the back buffer just before swap N (or after a
#     glFlush, for a single-buffered app), as tools/render_probe.py does;
#   - window_should_close turns true after the last frame, so the app's own
#     loop ends.
#
# Usage: capture_frames.py <script.py> <outdir> <frame> [<frame> ...]
# Writes <outdir>/frame<N>.png for each requested frame.

import pathlib
import random
import runpy
import sys
import time
import typing

import glfw
import OpenGL.GL as GL
from PIL import Image

script: str = sys.argv[1]
outdir: pathlib.Path = pathlib.Path(sys.argv[2])
wanted: set[int] = {int(arg) for arg in sys.argv[3:]}
last_frame: int = max(wanted)
outdir.mkdir(parents=True, exist_ok=True)
counts: dict[str, int] = {"frames": 0, "swaps": 0}


def fake_clock() -> float:
    return counts["frames"] / 30.0


random.seed(0)
time.monotonic = fake_clock
time.time = fake_clock
time.perf_counter = fake_clock
glfw.get_time = fake_clock
# a controller plugged into the host would otherwise perturb the run
glfw.get_joystick_axes = lambda joy: []
glfw.joystick_present = lambda joy: False

real_swap: typing.Callable[[typing.Any], None] = glfw.swap_buffers
real_flush: typing.Callable[[], None] = GL.glFlush


def end_frame(window: typing.Any) -> None:
    counts["frames"] += 1
    if counts["frames"] in wanted:
        size: tuple[int, int] = glfw.get_framebuffer_size(window)
        raw: typing.Any = GL.glReadPixels(
            0, 0, size[0], size[1], GL.GL_RGB, GL.GL_UNSIGNED_BYTE
        )
        Image.frombytes("RGB", size, bytes(raw)).transpose(
            Image.Transpose.FLIP_TOP_BOTTOM
        ).save(outdir / f"frame{counts['frames']}.png")


def probing_swap(window: typing.Any) -> None:
    counts["swaps"] += 1
    end_frame(window)
    real_swap(window)


def probing_flush() -> None:
    real_flush()
    if counts["swaps"] == 0:
        end_frame(glfw.get_current_context())


glfw.swap_buffers = probing_swap
GL.glFlush = probing_flush
glfw.window_should_close = lambda window: counts["frames"] >= last_frame
runpy.run_path(script, run_name="__main__")
