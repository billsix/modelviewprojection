# Pre-existing runtime crashes: pixbufobj (PBO readback) + texfloat (float-texture segfault)

Done 2026-11-15. Both SuperBible v4 chapter 18 demos crashed on their first run on the maintainer's
Fedora/Mesa host (surfaced 2026-05-29 while verifying the imgui render-options work, which did not
cause them). Both now run on host GL. The traps behind them are recorded in
`tasks/reference/gl-and-imgui-gotchas.md` (the PBO `None` offset, and reading EXRs with OpenEXR).

## pixbufobj — `glReadPixels` GLError 1282 with "Use PBOs" on

Three stacked bugs, each found by fixing the one before (2026-08-02, reproduced headless under
Xvfb + software Mesa):

1. `glGenBuffers` was never called: the pixel-pack PBOs were bound and deleted by the literal names
   1/2/3. Fixed with a `pbo_ids` list filled once in `setup_rc` by `glGenBuffers(3)`.
2. `glReadPixels(..., None)` / `glTexImage2D(..., None)` with a PBO bound: PyOpenGL turns `None` into
   a fresh client array and passes its address, which GL reads as a byte offset into the buffer
   (`GL_INVALID_OPERATION`). Fixed with `ctypes.c_void_p(0)`, the C original's `(GLvoid*)0`.
3. `np.ctypes.c_uint8` in the map/attenuate code (numpy has no `ctypes` attribute). Fixed to
   `ctypes.c_uint8`.

A `_check_gl()` probe after the PBO readback prints the site of any remaining GL error. The
maintainer verified it on host GL 2026-08-31 (`PBOs: ON`, no GL error, clean exit). The separate
"multiple spinning images" behaviour, which does not reproduce under software GL, is tracked in
`tasks/pixbufobj-port-fidelity.md`.

## texfloat — startup SIGSEGV

- **2026-08-02:** the crash was C-level, so a Python `try` could not catch it. A flushed `_trace()`
  print was added before each GL call in `setup_rc` → `setup_textures` to name the failing call.
- **2026-08-31:** on host GL the SIGSEGV was gone, replaced by a clean imageio `OSError` before any GL
  call: the venv had no EXR backend. The likely explanation is a native crash in whatever EXR decoder
  the older image carried.
- **2026-10-22:** the maintainer decided to keep the `.exr` assets and use an imageio EXR backend,
  not opencv and not converted assets.
- **2026-11-15:** every candidate backend was tested in the mvp image (imageio 2.38.1, Python 3.15)
  against all eight `openexr-images/*.exr`:
  - pyav (`av==19.0.2`) decodes them but clamps values to [0, 1], even with `format="gbrpf32le"`.
  - Fedora's `freeimage-3.19.0` loads but has no EXR support (`EXR-FI` "can not handle the given
    uri").
  - `OpenEXR==3.5.4`, the ASWF Python bindings (a wheel, and not an imageio plugin), reads all eight
    as float16 with true HDR maxima (Blobbies 6.4, Ocean 2100).

  The maintainer (William Emerison Six <billsix@gmail.com>, 2026-11-15) chose OpenEXR, replacing the
  imageio decision. `OpenEXR==3.5.4` is pinned in `requirements.txt`, `constraints.txt` was
  regenerated with `make update-pins` (openexr was the only addition), and `setup_textures` reads
  the `RGBA` or `RGB` channel through `OpenEXR.File`.
- **Verification:** headless on the host-built image, texfloat loaded Blobbies.exr (1040x1040),
  uploaded the RGB16F texture, built all four tone-map shaders and rendered with the image visible.
  The maintainer then ran it on host GL with no crash, and the `_trace()` instrumentation was
  removed. Format and type-check gates passed.
