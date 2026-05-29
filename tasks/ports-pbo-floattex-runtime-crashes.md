# Pre-existing runtime crashes: pixbufobj (PBO readback) + texfloat (float-texture segfault)

**Status:** not-started — surfaced 2026-05-29 while Bill visually verified the
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
