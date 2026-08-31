# Pre-existing runtime crashes: pixbufobj (PBO readback) + texfloat (float-texture segfault)

**Status:** in progress — **pixbufobj VERIFIED FIXED on host GL 2026-08-31** (maintainer ran
it via `make shell-exec`, toggled "Use PBOs" ON — `PBOs: ON` printed, no `[pixbufobj] GL
error` line, clean exit). **texfloat's SIGSEGV is GONE, replaced by a clean pre-GL failure**
(same host run): `imageio` raises `OSError: Could not find a backend to open …Blobbies.exr`
at `setup_textures` — the venv has no EXR-capable backend (imageio suggests `pyav` or
`opencv`). It never reaches the float-texture GL code. Plausible retro-explanation of the
original uncatchable C-level SIGSEGV: a native crash inside whatever EXR decode backend the
older image carried; the environment moved and the honest error surfaced. NEXT: maintainer
decides the EXR backend (a real runtime dep — `imageio[pyav]` vs opencv vs converting the
.exr assets); then re-run to see whether the GL path crashes at all, and remove the
`_trace()` instrumentation once it runs.
**Priority:** 3
**Difficulty:** 5

## Update 2026-08-02 (evening) — pixbufobj crash FULLY fixed + reproduced headless

Reproduced both symptoms headlessly (Xvfb + nested `mvp-docs` container + software Mesa) —
so this no longer needs Bill's host GL to *diagnose*. The pixbufobj PBO crash was **three
stacked bugs**, each uncovered by fixing the previous:

1. `glGenBuffers` never called — PBOs bound by literal names (earlier fix, `pbo_ids`).
2. **`glReadPixels(…, None)` / `glTexImage2D(…, None)`** — PyOpenGL turns `None` into a
   freshly-allocated client array and passes its pointer; with a PBO bound, GL reads that as
   a byte OFFSET → `GL_INVALID_OPERATION (1282)`. The C uses `(GLvoid*)0`. Fixed with
   **`ctypes.c_void_p(0)`** (readback + PBO→texture upload).
3. **`np.ctypes.c_uint8`** in the map/attenuate code — numpy has no `ctypes` attribute →
   `AttributeError`. Fixed to stdlib **`ctypes.c_uint8`**.

Verified: with PBOs forced on, the demo now runs the full duration and renders (no crash).
Staged.

**The pixbufobj "multiple spinning images" issue is now its own task:
`tasks/pixbufobj-port-fidelity.md`** (behavioural fidelity, not a crash). Short version: it
does **not** reproduce under the sandbox's software GL — the port renders one clean rotating
album there (corners pixel-verified black), with draw-time GL state provably identical to the
C++ — so it appears hardware/driver-specific and needs reproduction on Bill's GPU.

## (earlier) Work done 2026-08-02 + what to run

**pixbufobj — fix applied.** Root cause confirmed by reading the code: `glGenBuffers`
was **never called**; the three pixel-pack PBOs were bound by the literal names `1/2/3`
(`current_frame + 1`, `i + 1`), and `glDeleteBuffers(3, [1,2,3])` deleted literals too —
that's what tripped `glReadPixels` → `GL_INVALID_OPERATION` (1282) on Mesa. Fix: a module
global `pbo_ids`, populated once in `setup_rc` via `glGenBuffers(3)`, used everywhere the
literals were; kept for the app lifetime (freed on context destroy). Added a `_check_gl()`
probe right after the PBO `glReadPixels` so a residual error still prints its site.

**texfloat — instrumented (no fix yet; cause unknown).** The startup SIGSEGV is C-level,
so a Python try/except can't catch it. Added a `_trace()` helper (flushed prints) before
each GL call in `setup_rc` → `setup_textures` (incl. `GL_GENERATE_MIPMAP`, the `RGB16F`/
`GL_FLOAT` `glTexImage2D`, and a `GL_MAX_TEXTURE_SIZE` readout). The **last `[texfloat]`
line printed before the crash names the failing call.**

**To run (on your host GL, in the mvp `make shell`):**

```sh
# 1. pixbufobj — open the "Options" menu and toggle "Use PBOs" ON.
#    A clean run prints NO "[pixbufobj] GL error ..." line (fix worked).
python ports/openglsuperbiblev4/chapt18/pixbufobj/pixbufobj.py

# 2. texfloat — it will still crash; send me the LAST "[texfloat] ..." line.
python ports/openglsuperbiblev4/chapt18/texfloat/texfloat.py
```

Both files are verified syntax- + ruff-clean; the real verification is your host run
(the bugs are Fedora/Mesa-specific and don't reproduce under the sandbox's software GL).
The `texfloat` `_trace` calls are temporary debug instrumentation — remove them once the
culprit GL call is fixed.

---

Surfaced 2026-05-29 while Bill visually verified the
[[ports-render-options-to-imgui]] work. Both are PRE-EXISTING (never-hardware-verified) port
bugs, NOT caused by the imgui change — confirmed via diff (the imgui commit only relocated key
handling; neither touched the crashing GL paths). Same family as [[hdrbloom-pbo-sizing-crash]]
and the motionblur accum issue (auto-memory `env-mvp-opengl-accum-buffer`): advanced ch18 demos
that crash on first run on Bill's Fedora/Mesa.

## 1. chapt18/pixbufobj — `glReadPixels` GLError 1282 when PBOs are on

`render_scene` (the `use_pbos` branch, ~line 112):
```python
GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, current_frame + 1)   # buffer NAME 1 or 2 (literal)
GL.glReadPixels(data_offset_x, data_offset_y, data_width, data_height,
                GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)          # -> GL_INVALID_OPERATION
```
Triggered by enabling "Use PBOs" (the imgui checkbox calls the same `toggle_pbos()` the old `P`
key did — pressing P pre-imgui would crash identically). Likely cause: the PBOs are referenced by
**literal buffer names `current_frame + 1` (1/2)** rather than ids from `glGenBuffers`, and/or are
never sized via `glBufferData(GL_PIXEL_PACK_BUFFER, data_height*data_pitch, ...)`, so the readback
writes past the buffer → invalid operation on Mesa. **Fix direction:** glGenBuffers(2) for the
PBOs, store the ids, and glBufferData them to `data_height * data_pitch` (cf. the
hdrbloom PBO-sizing fix). Verify against the C++ `pixelbufferobject.cpp`.

## 2. chapt18/texfloat — segfault (SIGSEGV, core dumped) at startup

Crashes right after the startup prints, i.e. in `setup_rc()` → `setup_textures(0)`, which creates
floating-point textures (RGB16F/RGB32F) from .exr/.hdr images and/or reads them back — before any
imgui code runs. A C-level segfault (not a Python exception) points at the GL driver: float-texture
creation, the image upload, or a readback with a bad/short pointer on Bill's Mesa. **Fix direction:**
isolate the failing GL call (bisect setup_textures / the float `glTexImage2D` / any `glGetTexImage`
or `glReadPixels`); check float-texture format support and that host buffers match the declared
format/size. May be partly environmental (float-texture support) like the other ch18 demos.

## Not blocking the imgui task
The imgui conversion itself is fine in both (panels compile/wire correctly); these crashes are in
the underlying demo logic. They block *visual* verification of those two demos only.
