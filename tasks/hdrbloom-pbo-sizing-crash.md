# hdrbloom crashes on startup: after-glow PBO allocated 1 byte

**Status:** FIXED 2026-05-29 (pending Bill's run-to-confirm) — sized the after-glow PBO at its real
size in `setup_rc` (`fbo_height * (((fbo_width*3)+3)&~0x3)`) instead of the 1-byte placeholder, so
`final_pass`'s `glReadPixels`-into-PBO no longer reads past the end on startup. Compiles clean.
Root cause below. NOT related to the geometry-extraction refactor.

## Symptom

`python ports/openglsuperbiblev4/chapt18/hdrbloom/hdrbloom.py` crashes immediately:

```
OpenGL.error.GLError(err = 1282,  # GL_INVALID_OPERATION
    baseOperation = glTexImage2D,
    pyArgs = (GL_TEXTURE_2D, 0, GL_RGB8, 512, 512, 0, GL_RGB, GL_UNSIGNED_BYTE, None))
```
…at `final_pass()` (`render_scene` → `final_pass`).

## Root cause (confirmed by reading the code)

The after-glow feedback re-uploads the previous frame's pixels from a pixel buffer object.

1. `setup_rc` allocates the PBO with a **1-byte placeholder**:
   ```python
   pbo_id = GL.glGenBuffers(1)
   GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, pbo_id)
   GL.glBufferData(GL.GL_PIXEL_PACK_BUFFER, 1, None, GL.GL_STREAM_COPY)   # 1 byte!
   ```
2. `change_size` only grows it to the real size **when the size changes**:
   ```python
   orig = (fbo_width, fbo_height)
   ...
   if (fbo_width, fbo_height) != orig and pbo_id != 0:
       pitch = ((fbo_width * 3) + 3) & ~0x3
       GL.glBufferData(GL.GL_PIXEL_PACK_BUFFER, fbo_height * pitch, None, GL.GL_STREAM_COPY)
   ```
   At startup the window opens at the default 512×512, so the one `change_size(512, 512)` call
   from `main` sees `(fbo_width, fbo_height) == orig` and **skips the resize** — the PBO stays 1 byte.
3. `final_pass` then binds that PBO as `GL_PIXEL_UNPACK_BUFFER` and does
   `glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 512, 512, 0, GL_RGB, GL_UNSIGNED_BYTE, None)`, which
   reads `512*512*3 = 786432` bytes from the 1-byte buffer → `GL_INVALID_OPERATION`.

## Fix (recommended)

Size the PBO to its real size in `setup_rc` instead of the 1-byte placeholder — same formula
`change_size` uses:
```python
pitch = ((fbo_width * 3) + 3) & ~0x3
GL.glBufferData(GL.GL_PIXEL_PACK_BUFFER, fbo_height * pitch, None, GL.GL_STREAM_COPY)
```
`after_glow_valid` starts `False`, so the COMBINE shader ignores the (uninitialized) after-glow
texture on frame 1 — a correctly-sized-but-uninitialized PBO is fine; no frame-1 special-casing
needed. (Alternative: drop the `!= orig` guard for the PBO so the first `change_size` sizes it,
but that also re-runs the FBO/renderbuffer reallocation pointlessly on the first frame — sizing
it in `setup_rc` is cleaner.)

Cross-check against the C++ `hdrbloom.cpp` if available to confirm where the original sized the PBO.

## Verify
Bill runs it (needs a display): it should start, show the HDR ball, and the after-glow trail
should work when spinning. Can't be checked in-container.

## Note — sibling pre-existing crash
`chapt06/motionblur` has a *different* startup crash (`glAccum` → GLError 1282, no accumulation
buffer on Bill's Mesa — environmental, see auto-memory `env-mvp-opengl-accum-buffer`). Both were
surfaced while visually verifying the geometry-extraction conversions; neither is caused by it.
